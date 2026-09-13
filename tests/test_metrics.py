import csv
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.metrics_service import (
    METRICS_FIELDS,
    build_metrics,
    calculate_estimated_cost,
    save_metrics,
)


@pytest.fixture
def api_response():
    """
    Simulates an OpenAI response with token usage.
    """

    return SimpleNamespace(
        model="gpt-5-mini-2025-08-07",
        usage=SimpleNamespace(
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            output_tokens_details=SimpleNamespace(
                reasoning_tokens=300,
            ),
        ),
    )


@pytest.mark.parametrize(
    "model, expected_cost",
    [
        ("gpt-4o-mini", 0.00045),
        ("gpt-4o", 0.0075),
        ("gpt-4.1", 0.006),
        ("gpt-4.1-mini", 0.0012),
        ("gpt-4.1-nano", 0.0003),
        ("gpt-5", 0.00625),
        ("gpt-5-mini", 0.00125),
        ("gpt-5-nano", 0.00025),
    ],
)
def test_calculates_model_cost(model, expected_cost):
    cost = calculate_estimated_cost(
        model=model,
        prompt_tokens=1000,
        completion_tokens=500,
    )

    assert cost == pytest.approx(expected_cost)


def test_resolves_model_alias():
    alias_cost = calculate_estimated_cost(
        "gpt-5-mini-2025-08-07",
        1000,
        500,
    )

    base_cost = calculate_estimated_cost(
        "gpt-5-mini",
        1000,
        500,
    )

    assert alias_cost == base_cost


def test_zero_tokens_have_zero_cost():
    cost = calculate_estimated_cost(
        "gpt-4o-mini",
        0,
        0,
    )

    assert cost == 0


def test_rejects_unknown_model():
    with pytest.raises(
        ValueError,
        match="Pricing is not configured",
    ):
        calculate_estimated_cost(
            "unknown-model",
            1000,
            500,
        )


def test_builds_execution_metrics(api_response):
    metrics = build_metrics(
        response=api_response,
        latency_ms=123.456,
    )

    assert set(metrics) == set(METRICS_FIELDS)
    assert metrics["model"] == api_response.model
    assert metrics["prompt_tokens"] == 1000
    assert metrics["completion_tokens"] == 500
    assert metrics["total_tokens"] == 1500
    assert metrics["reasoning_tokens"] == 300
    assert metrics["latency_ms"] == 123.46
    assert metrics["estimated_cost_usd"] == pytest.approx(
        0.00125
    )

    timestamp = datetime.fromisoformat(
        metrics["timestamp"]
    )

    assert timestamp.utcoffset().total_seconds() == 0


def test_reasoning_tokens_are_not_counted_twice(
    api_response,
):
    first_metrics = build_metrics(
        api_response,
        latency_ms=100,
    )

    api_response.usage.output_tokens_details.reasoning_tokens = (
        400
    )

    second_metrics = build_metrics(
        api_response,
        latency_ms=100,
    )

    assert first_metrics["estimated_cost_usd"] == (
        second_metrics["estimated_cost_usd"]
    )

    assert second_metrics["total_tokens"] == 1500


def test_handles_missing_reasoning_details(api_response):
    del api_response.usage.output_tokens_details

    metrics = build_metrics(
        api_response,
        latency_ms=100,
    )

    assert metrics["reasoning_tokens"] is None


def test_rejects_missing_usage(api_response):
    api_response.usage = None

    with pytest.raises(
        ValueError,
        match="did not return token usage",
    ):
        build_metrics(
            api_response,
            latency_ms=100,
        )


def test_creates_csv_with_header(
    api_response,
    tmp_path,
):
    file_path = tmp_path / "metrics" / "metrics.csv"

    metrics = build_metrics(
        api_response,
        latency_ms=100,
    )

    save_metrics(
        metrics,
        file_path=file_path,
    )

    with file_path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        assert reader.fieldnames == METRICS_FIELDS

    assert len(rows) == 1
    assert rows[0]["prompt_tokens"] == "1000"
    assert rows[0]["reasoning_tokens"] == "300"


def test_appends_rows_without_repeating_header(
    api_response,
    tmp_path,
):
    file_path = tmp_path / "metrics.csv"

    metrics = build_metrics(
        api_response,
        latency_ms=100,
    )

    save_metrics(metrics, file_path)
    save_metrics(metrics, file_path)

    with file_path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.reader(file))

    assert rows[0] == METRICS_FIELDS
    assert len(rows) == 3
    assert rows.count(METRICS_FIELDS) == 1


def test_rejects_incompatible_csv_header(
    api_response,
    tmp_path,
):
    file_path = tmp_path / "metrics.csv"

    original_content = "old_column\nexisting_value\n"
    file_path.write_text(
        original_content,
        encoding="utf-8",
    )

    metrics = build_metrics(
        api_response,
        latency_ms=100,
    )

    with pytest.raises(
        ValueError,
        match="header is incompatible",
    ):
        save_metrics(
            metrics,
            file_path=file_path,
        )

    assert file_path.read_text(
        encoding="utf-8"
    ) == original_content