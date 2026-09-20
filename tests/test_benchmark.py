from __future__ import annotations

import pytest

from dp.benchmark import LexicalOverlapScorer, delta_compression_ratio, estimate_tokens


def test_estimate_tokens_minimum_one() -> None:
    assert estimate_tokens("") == 1
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcdefgh") == 2


def test_scorer_identical_is_one() -> None:
    assert LexicalOverlapScorer().score("hello world", "hello world") == 1.0


def test_scorer_partial_overlap() -> None:
    assert LexicalOverlapScorer().score("a b c d", "a b e f") == 0.5


def test_scorer_empty_reference_is_zero() -> None:
    assert LexicalOverlapScorer().score("", "something") == 0.0


def test_scorer_both_empty_is_one() -> None:
    assert LexicalOverlapScorer().score("", "") == 1.0


def test_scorer_case_insensitive() -> None:
    assert LexicalOverlapScorer().score("Hello", "hello") == 1.0


def test_delta_compression_ratio() -> None:
    naive = "x" * 400
    delta = "y" * 100
    assert delta_compression_ratio(naive, delta) == pytest.approx(100 / 25)


def test_delta_compression_ratio_never_divides_by_zero() -> None:
    assert delta_compression_ratio("x" * 400, "") >= 1.0
