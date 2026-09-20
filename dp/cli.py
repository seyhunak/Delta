from __future__ import annotations

import asyncio
import time
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from dp.benchmark import LexicalOverlapScorer, estimate_tokens, run_single_benchmark
from dp.config import ConfigStore, Settings, get_settings
from dp.providers import (
    KNOWN_PROVIDERS,
    SUPPORTED_PROVIDERS,
    ProviderStatus,
    default_model_for,
    detect_providers,
    provider_factory,
    select_provider,
)
from dp.providers.base import DEFAULT_TEMPERATURE, ProviderError
from dp.session import SessionStore, now_iso
from dp.tools.tavily import TavilyClient, build_web_context_block

console = Console()
app = typer.Typer(help="Delta CLI")
baseline_app = typer.Typer(help="Manage baseline prompt")
delta_app = typer.Typer(help="Manage deltas")
goal_app = typer.Typer(help="Manage goal")

app.add_typer(baseline_app, name="baseline")
app.add_typer(delta_app, name="delta")
app.add_typer(goal_app, name="goal")


def get_store() -> SessionStore:
    return SessionStore(get_settings().session_path)


def get_config_store() -> ConfigStore:
    return ConfigStore(get_settings().config_path)


def compose_user_prompt(baseline: str, deltas: list[str], goal: str) -> str:
    lines: list[str] = [f"Baseline: {baseline}"]
    for delta in deltas:
        lines.append(f"Δ({delta})")
    lines.append("Goal:")
    lines.append(goal)
    return "\n".join(lines)


def compose_messages(
    baseline: str,
    deltas: list[str],
    goal: str,
    preferences: list[str] | None = None,
) -> list[dict[str, str]]:
    system_text = "You are a capable AI."
    if preferences:
        pref_block = "\n".join(f"- {pref}" for pref in preferences)
        system_text = f"{system_text}\n\nUser preferences:\n{pref_block}"
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": compose_user_prompt(baseline, deltas, goal)},
    ]


def add_web_context_to_messages(messages: list[dict[str, str]], web_context: str) -> list[dict[str, str]]:
    if not web_context:
        return messages
    updated = [dict(msg) for msg in messages]
    for msg in updated:
        if msg.get("role") == "user":
            msg["content"] = f"{msg.get('content', '').rstrip()}\n\n{web_context}"
            break
    return updated


def ensure_prompt_inputs(baseline: str, goal: str) -> None:
    if not baseline.strip():
        raise typer.BadParameter("Baseline is empty. Use: dp baseline set \"...\"")
    if not goal.strip():
        raise typer.BadParameter("Goal is empty. Use: dp goal set \"...\"")


def _normalize_markdown(text: str) -> str:
    body = text.strip()
    if not body:
        return "## Response\n\n_No content returned._"
    if body.startswith("#"):
        return body
    return f"## Response\n\n{body}"


def render_pretty_response(
    *,
    title: str,
    provider: str,
    model: str,
    elapsed_s: float,
    prompt_tokens: int,
    output_tokens: int,
    output: str,
    web_sources: int = 0,
    border_style: str = "green",
    include_output: bool = True,
) -> None:
    summary = Table(show_header=False, box=None, pad_edge=False)
    summary.add_column("k", style="cyan", no_wrap=True)
    summary.add_column("v", style="white")
    summary.add_row("Provider", provider)
    summary.add_row("Model", model)
    summary.add_row("Latency", f"{elapsed_s:.2f}s")
    summary.add_row("Prompt tokens (est.)", str(prompt_tokens))
    summary.add_row("Output tokens (est.)", str(output_tokens))
    summary.add_row("Total tokens (est.)", str(prompt_tokens + output_tokens))
    summary.add_row("Web sources", str(web_sources))
    summary.add_row("Chars", str(len(output)))
    console.print(Panel(summary, title="Run Summary", border_style="cyan"))
    if not include_output:
        console.print(Rule(style="dim"))
        return
    console.print(
        Panel.fit(
            Markdown(_normalize_markdown(output), code_theme="monokai", hyperlinks=True),
            title=title,
            border_style=border_style,
        )
    )
    console.print(Rule(style="dim"))


@baseline_app.command("set")
def baseline_set(text: str) -> None:
    store = get_store()
    state = store.load()
    state.baseline = text
    store.save(state)
    console.print("[green]Baseline updated.[/green]")


@delta_app.command("add")
def delta_add(text: str) -> None:
    store = get_store()
    state = store.load()
    state.deltas.append(text)
    store.save(state)
    console.print(f"[green]Delta added.[/green] total={len(state.deltas)}")


@goal_app.command("set")
def goal_set(text: str) -> None:
    store = get_store()
    state = store.load()
    state.goal = text
    store.save(state)
    console.print("[green]Goal updated.[/green]")


@app.command("set")
def set_all(
    baseline: Annotated[str, typer.Argument(help="Baseline text")],
    goal: Annotated[str, typer.Argument(help="Goal text")],
    delta: Annotated[
        list[str] | None,
        typer.Option(
            "-d",
            "--delta",
            help="Delta text. Repeat the flag for multiple deltas.",
        ),
    ] = None,
    append_deltas: Annotated[
        bool,
        typer.Option(
            "-a",
            "--append-deltas/--replace-deltas",
            help="Append new deltas to existing ones (default: replace).",
        ),
    ] = False,
) -> None:
    store = get_store()
    state = store.load()

    state.baseline = baseline
    state.goal = goal
    incoming_deltas = delta or []
    if append_deltas:
        state.deltas.extend(incoming_deltas)
    else:
        state.deltas = incoming_deltas

    store.save(state)

    table = Table(title="Session Updated")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Baseline", state.baseline or "<empty>")
    table.add_row("Goal", state.goal or "<empty>")
    table.add_row("Deltas", str(len(state.deltas)))
    console.print(table)


async def _detect_and_suggest(
    settings: Settings,
    preferred: str | None,
) -> tuple[dict[str, ProviderStatus], str]:
    statuses = await detect_providers()
    try:
        suggested = await select_provider(None, settings, preferred=preferred)
    except ProviderError:
        suggested = "ollama"
    return statuses, suggested


@app.command("setup")
def setup() -> None:
    settings = get_settings()
    config_store = ConfigStore(settings.config_path)
    config = config_store.load()
    statuses, suggested_provider = asyncio.run(
        _detect_and_suggest(settings, preferred=config.default_provider)
    )

    available = [p for p in SUPPORTED_PROVIDERS if statuses.get(p) and statuses[p].available]
    if available:
        console.print(f"Detected providers: {', '.join(available)}")
    else:
        console.print("[yellow]No providers detected; defaulting to ollama.[/yellow]")

    chosen_provider = typer.prompt(
        "Default provider",
        default=config.default_provider or suggested_provider,
    ).strip().lower()
    if chosen_provider not in SUPPORTED_PROVIDERS:
        raise typer.BadParameter(
            f"Unsupported provider '{chosen_provider}'. Choose from: {', '.join(SUPPORTED_PROVIDERS)}"
        )

    suggested_model = config.models.get(chosen_provider) or default_model_for(chosen_provider, settings)
    chosen_model = typer.prompt("Default model", default=suggested_model).strip()
    preferences_raw = typer.prompt(
        "Preferences (comma-separated, optional)",
        default=", ".join(config.preferences),
    ).strip()
    preferences = [part.strip() for part in preferences_raw.split(",") if part.strip()]
    web_search_enabled = typer.confirm(
        "Enable Tavily web search for prompts?",
        default=config.web_search_enabled,
    )
    max_results = config.web_search_max_results
    if web_search_enabled:
        max_results = typer.prompt(
            "Max Tavily results per run (1-10)",
            default=str(config.web_search_max_results),
        ).strip()
        try:
            max_results = max(1, min(int(max_results), 10))
        except ValueError as exc:
            raise typer.BadParameter("Max Tavily results must be an integer.") from exc

    config.default_provider = chosen_provider
    config.models[chosen_provider] = chosen_model
    config.preferences = preferences
    config.web_search_enabled = web_search_enabled
    config.web_search_max_results = int(max_results)
    config_store.save(config)

    table = Table(title="Saved Configuration")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Config path", str(settings.config_path))
    table.add_row("Default provider", config.default_provider or "<empty>")
    table.add_row("Model", config.models.get(chosen_provider, "<empty>"))
    table.add_row("Preferences", ", ".join(config.preferences) or "<empty>")
    table.add_row("Web search", "enabled" if config.web_search_enabled else "disabled")
    table.add_row("Web max results", str(config.web_search_max_results))
    console.print(table)


@app.command("show")
def show() -> None:
    store = get_store()
    state = store.load()
    config = get_config_store().load()

    table = Table(title="Delta Session")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Baseline", state.baseline or "<empty>")
    table.add_row("Goal", state.goal or "<empty>")
    table.add_row("Deltas", str(len(state.deltas)))
    table.add_row("History entries", str(len(state.history)))
    table.add_row("Default provider", config.default_provider or "<empty>")
    table.add_row("Preferences", ", ".join(config.preferences) or "<empty>")
    table.add_row("Web search", "enabled" if config.web_search_enabled else "disabled")
    table.add_row("Web max results", str(config.web_search_max_results))
    console.print(table)

    if state.deltas:
        deltas_table = Table(title="Deltas")
        deltas_table.add_column("#", style="cyan")
        deltas_table.add_column("Text", style="white")
        for idx, delta in enumerate(state.deltas, start=1):
            deltas_table.add_row(str(idx), delta)
        console.print(deltas_table)


@app.command("reset")
def reset() -> None:
    store = get_store()
    store.reset()
    console.print("[yellow]Session reset.[/yellow]")


async def _run(
    provider: str | None,
    model: str | None,
    web_search: bool | None,
    search_query: str | None,
    search_results: int | None,
    temperature: float | None,
    max_tokens: int | None,
    stream: bool,
) -> None:
    settings = get_settings()
    store = SessionStore(settings.session_path)
    config = ConfigStore(settings.config_path).load()
    state = store.load()
    ensure_prompt_inputs(state.baseline, state.goal)

    resolved_temperature = DEFAULT_TEMPERATURE if temperature is None else temperature
    if resolved_temperature < 0:
        raise typer.BadParameter("Temperature must be >= 0.")
    if max_tokens is not None and max_tokens < 1:
        raise typer.BadParameter("Max tokens must be >= 1.")

    selected_provider = await select_provider(provider, settings, preferred=config.default_provider)
    selected_model = model or config.models.get(selected_provider) or default_model_for(selected_provider, settings)

    messages = compose_messages(state.baseline, state.deltas, state.goal, preferences=config.preferences)
    use_web_search = config.web_search_enabled if web_search is None else web_search
    web_result_items: list[dict[str, str]] = []

    if use_web_search:
        tavily_key = settings.tavily_api_key
        if not tavily_key:
            console.print(
                "[yellow]Web search requested but Tavily API key is missing. "
                "Set TAVILY_API_KEY in your environment.[/yellow]"
            )
        else:
            query = search_query or state.goal
            max_results = max(1, min(search_results or config.web_search_max_results, 10))
            try:
                with console.status(
                    f"[bold cyan]Fetching web context[/bold cyan] query={query!r}",
                    spinner="dots",
                ):
                    tavily = TavilyClient(api_key=tavily_key)
                    web_result_items = await tavily.search(query=query, max_results=max_results)
                web_context = build_web_context_block(web_result_items)
                messages = add_web_context_to_messages(messages, web_context)
            except ProviderError as exc:
                console.print(f"[yellow]Web search failed, continuing without it: {exc}[/yellow]")

    prompt_tokens = estimate_tokens("\n".join(msg.get("content", "") for msg in messages))

    try:
        runner = provider_factory(selected_provider)
        started = time.perf_counter()
        if stream:
            console.print(f"[dim]Streaming provider={selected_provider} model={selected_model}[/dim]")
            chunks: list[str] = []
            async for chunk in runner.generate_stream(
                messages=messages,
                model=selected_model,
                temperature=resolved_temperature,
                max_tokens=max_tokens,
            ):
                chunks.append(chunk)
                print(chunk, end="", flush=True)
            print(flush=True)
            output = "".join(chunks)
        else:
            with console.status(
                f"[bold cyan]Running[/bold cyan] provider={selected_provider} model={selected_model}",
                spinner="dots",
            ):
                output = await runner.generate(
                    messages=messages,
                    model=selected_model,
                    temperature=resolved_temperature,
                    max_tokens=max_tokens,
                )
        elapsed = time.perf_counter() - started
        used_model = runner.resolved_model or selected_model
        if used_model != selected_model:
            console.print(
                f"[yellow]Requested model '{selected_model}' unavailable; "
                f"used '{used_model}'.[/yellow]"
            )
        output_tokens = estimate_tokens(output)
    except ProviderError as exc:
        state.history.append(
            {
                "timestamp": now_iso(),
                "provider": selected_provider,
                "model": selected_model,
                "error": str(exc),
            }
        )
        store.save(state)
        raise

    state.history.append(
        {
            "timestamp": now_iso(),
            "provider": selected_provider,
            "model": used_model,
            "temperature": resolved_temperature,
            "prompt": messages,
            "output": output,
        }
    )
    store.save(state)

    render_pretty_response(
        title=f"Run Result [{selected_provider}:{used_model}]",
        provider=selected_provider,
        model=used_model,
        elapsed_s=elapsed,
        prompt_tokens=prompt_tokens,
        output_tokens=output_tokens,
        output=output,
        web_sources=len(web_result_items),
        border_style="green",
        include_output=not stream,
    )


@app.command("run")
def run(
    provider: Annotated[
        str | None,
        typer.Option("--provider", help="Provider name (openai, anthropic, ollama)"),
    ] = None,
    model: Annotated[str | None, typer.Option("--model", help="Model override")] = None,
    web_search: Annotated[
        bool | None,
        typer.Option(
            "--web-search/--no-web-search",
            help="Enable/disable Tavily web context for this run.",
        ),
    ] = None,
    search_query: Annotated[
        str | None,
        typer.Option("--search-query", help="Override Tavily query (default: goal text)."),
    ] = None,
    search_results: Annotated[
        int | None,
        typer.Option("--search-results", help="Tavily max results (1-10).", min=1, max=10),
    ] = None,
    temperature: Annotated[
        float | None,
        typer.Option("--temperature", help="Sampling temperature (default: 0.2).", min=0.0, max=2.0),
    ] = None,
    max_tokens: Annotated[
        int | None,
        typer.Option("--max-tokens", help="Max output tokens (provider default if omitted).", min=1),
    ] = None,
    stream: Annotated[
        bool,
        typer.Option("--stream/--no-stream", help="Stream output tokens live."),
    ] = False,
) -> None:
    try:
        asyncio.run(
            _run(
                provider=provider,
                model=model,
                web_search=web_search,
                search_query=search_query,
                search_results=search_results,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )
        )
    except ProviderError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    except typer.BadParameter as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc


async def _doctor() -> None:
    statuses = await detect_providers()
    console.print("Provider availability:")

    for name in KNOWN_PROVIDERS:
        status = statuses.get(name)
        if status and status.available and name in SUPPORTED_PROVIDERS:
            console.print(f"[green]✓ {name}[/green]")
        else:
            console.print(f"[red]✗ {name}[/red]")

    settings = get_settings()
    config = ConfigStore(settings.config_path).load()
    try:
        selected = await select_provider(None, settings, preferred=config.default_provider)
        console.print(f"Selected default provider: [bold]{selected}[/bold]")
    except ProviderError as exc:
        console.print(f"[red]Provider selection error: {exc}[/red]")


@app.command("doctor")
def doctor() -> None:
    asyncio.run(_doctor())


async def _benchmark(
    providers: list[str] | None,
    model: str | None,
    web_search: bool | None,
    search_query: str | None,
    search_results: int | None,
    temperature: float | None,
    max_tokens: int | None,
) -> None:
    settings = get_settings()
    store = SessionStore(settings.session_path)
    config = ConfigStore(settings.config_path).load()
    state = store.load()
    ensure_prompt_inputs(state.baseline, state.goal)

    resolved_temperature = DEFAULT_TEMPERATURE if temperature is None else temperature
    if resolved_temperature < 0:
        raise typer.BadParameter("Temperature must be >= 0.")
    if max_tokens is not None and max_tokens < 1:
        raise typer.BadParameter("Max tokens must be >= 1.")

    requested = [p.lower() for p in providers] if providers else list(SUPPORTED_PROVIDERS)
    statuses = await detect_providers()

    messages = compose_messages(state.baseline, state.deltas, state.goal, preferences=config.preferences)
    use_web_search = config.web_search_enabled if web_search is None else web_search

    if use_web_search:
        tavily_key = settings.tavily_api_key
        if not tavily_key:
            console.print(
                "[yellow]Web search requested but Tavily API key is missing. "
                "Set TAVILY_API_KEY in your environment.[/yellow]"
            )
        else:
            query = search_query or state.goal
            max_results = max(1, min(search_results or config.web_search_max_results, 10))
            try:
                with console.status(
                    f"[bold cyan]Fetching shared web context[/bold cyan] query={query!r}",
                    spinner="dots",
                ):
                    tavily = TavilyClient(api_key=tavily_key)
                    web_items = await tavily.search(query=query, max_results=max_results)
                messages = add_web_context_to_messages(messages, build_web_context_block(web_items))
            except ProviderError as exc:
                console.print(f"[yellow]Web search failed, continuing without it: {exc}[/yellow]")
    results = []

    for name in requested:
        if name not in SUPPORTED_PROVIDERS:
            console.print(f"[yellow]Skipping unknown/unsupported provider: {name}[/yellow]")
            continue
        if not statuses.get(name) or not statuses[name].available:
            console.print(f"[yellow]Skipping unavailable provider: {name}[/yellow]")
            continue

        chosen_model = model or config.models.get(name) or default_model_for(name, settings)
        provider_client = provider_factory(name)

        try:
            started = time.perf_counter()
            with console.status(
                f"[bold cyan]Benchmarking[/bold cyan] provider={name} model={chosen_model}",
                spinner="dots",
            ):
                result = await run_single_benchmark(
                    provider_name=name,
                    provider=provider_client,
                    model=chosen_model,
                    messages=messages,
                    temperature=resolved_temperature,
                    max_tokens=max_tokens,
                )
                if provider_client.resolved_model:
                    result.model = provider_client.resolved_model
            elapsed = time.perf_counter() - started
            console.print(f"[dim]{name} completed in {elapsed:.2f}s[/dim]")
            results.append(result)
        except ProviderError as exc:
            console.print(f"[red]{name} failed: {exc}[/red]")

    if not results:
        console.print("[red]No benchmark results produced.[/red]")
        raise typer.Exit(code=1)

    table = Table(title="Benchmark")
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="white")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Prompt Tok (est.)", justify="right")
    table.add_column("Output Tok (est.)", justify="right")
    table.add_column("Total Tok (est.)", justify="right")
    for result in results:
        table.add_row(
            result.provider,
            result.model,
            f"{result.latency_ms:.2f}",
            str(result.prompt_token_estimate),
            str(result.output_token_estimate),
            str(result.total_token_estimate),
        )
    console.print(table)

    reference = results[0]
    scorer = LexicalOverlapScorer()
    compare = Table(title=f"Output Comparison (reference: {reference.provider})")
    compare.add_column("Provider", style="cyan")
    compare.add_column("Score", justify="right")

    for result in results:
        if result.provider == reference.provider:
            compare.add_row(result.provider, "— (ref)")
        else:
            score = scorer.score(reference.output, result.output)
            compare.add_row(result.provider, f"{score:.3f}")
    console.print(compare)

    for result in results:
        console.print(Rule(f"[bold]Output: {result.provider}[/bold]", style="blue"))
        console.print(
            Panel.fit(
                Markdown(_normalize_markdown(result.output), code_theme="monokai", hyperlinks=True),
                title=f"{result.provider}:{result.model}",
                border_style="blue",
            )
        )


@app.command("benchmark")
def benchmark(
    providers_opt: Annotated[
        list[str] | None,
        typer.Option(
            "--providers",
            help="Providers to benchmark, e.g. --providers openai --providers anthropic",
        ),
    ] = None,
    providers: Annotated[
        list[str] | None,
        typer.Argument(help="Optional extra providers, e.g. dp benchmark --providers openai anthropic ollama"),
    ] = None,
    model: Annotated[str | None, typer.Option("--model", help="Override model for all providers")] = None,
    web_search: Annotated[
        bool | None,
        typer.Option(
            "--web-search/--no-web-search",
            help="Enable/disable Tavily web context for benchmark prompt.",
        ),
    ] = None,
    search_query: Annotated[
        str | None,
        typer.Option("--search-query", help="Override Tavily query (default: goal text)."),
    ] = None,
    search_results: Annotated[
        int | None,
        typer.Option("--search-results", help="Tavily max results (1-10).", min=1, max=10),
    ] = None,
    temperature: Annotated[
        float | None,
        typer.Option("--temperature", help="Sampling temperature (default: 0.2).", min=0.0, max=2.0),
    ] = None,
    max_tokens: Annotated[
        int | None,
        typer.Option("--max-tokens", help="Max output tokens (provider default if omitted).", min=1),
    ] = None,
) -> None:
    selected = (providers_opt or []) + (providers or [])
    asyncio.run(
        _benchmark(
            providers=selected or None,
            model=model,
            web_search=web_search,
            search_query=search_query,
            search_results=search_results,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    )


if __name__ == "__main__":
    app()
