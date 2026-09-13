import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import BASE_DIR

METRICS_PATH = BASE_DIR / "metrics" / "metrics.csv"

METRICS_FIELDS = [
    "timestamp",
    "model",
    "prompt_tokens",
    "completion_tokens",
    "reasoning_tokens",
    "total_tokens",
    "latency_ms",
    "estimated_cost_usd",
]

# Standard USD pricing per million tokens.
# Verified on 2026-09-13.
# Excludes cache discounts, Batch pricing and additional tool costs.

MODEL_PRICES = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "gpt-5": {"input": 1.25, "output": 10.00},
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
    "gpt-5-nano": {"input": 0.05, "output": 0.40},
}

# Map dated snapshots to their pricing model.
MODEL_ALIASES = {
    "gpt-4o-mini-2024-07-18": "gpt-4o-mini",
    "gpt-4o-2024-08-06": "gpt-4o",
    "gpt-4o-2024-11-20": "gpt-4o",
    "gpt-4.1-2025-04-14": "gpt-4.1",
    "gpt-4.1-mini-2025-04-14": "gpt-4.1-mini",
    "gpt-4.1-nano-2025-04-14": "gpt-4.1-nano",
    "gpt-5-2025-08-07": "gpt-5",
    "gpt-5-mini-2025-08-07": "gpt-5-mini",
    "gpt-5-nano-2025-08-07": "gpt-5-nano",
}

def calculate_estimated_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Estimates standard token cost in USD, excluding cache discounts.

    Completion tokens already include reasoning tokens.

    Raises:
        ValueError: If pricing is not configured for the model.
    """

    pricing_model = MODEL_ALIASES.get(model, model)

    if pricing_model not in MODEL_PRICES:
        raise ValueError(
            f"Pricing is not configured for model: {model}"
        )

    prices = MODEL_PRICES[pricing_model]

    input_cost = prompt_tokens * prices["input"] / 1_000_000
    output_cost = completion_tokens * prices["output"] / 1_000_000

    return round(input_cost + output_cost, 8)

def build_metrics(response: Any, latency_ms: float) -> dict[str, Any]:
    """
    Builds execution metrics from the original OpenAI response.

    Reasoning tokens are a subset of completion tokens.
    A missing reasoning token count is represented as None.

    Raises:
        ValueError: If token usage or model pricing is unavailable.
    """

    if response.usage is None:
        raise ValueError(
            "OpenAI did not return token usage."
        )

    usage = response.usage

    output_details = getattr(
        usage,
        "output_tokens_details",
        None,
    )

    reasoning_tokens = getattr(
        output_details,
        "reasoning_tokens",
        None,
    )

    estimated_cost = calculate_stimated_cost(
        model=response.model,
        prompt_tokens=usage.input_tokens,
        completion_tokens=usage.output_tokens,
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": response.model,
        "prompt_tokens": usage.input_tokens,
        "completion_tokens": usage.output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": usage.total_tokens,
        "latency_ms": round(latency_ms, 2),
        "estimated_cost_usd": estimated_cost,
    }

def save_metrics(metrics: dict[str, Any], file_path: Path = METRICS_PATH) -> None:
    """
    Appends execution metrics to a CSV file.

    Creates the directory and CSV header when necessary.
    Rejects an existing file with an incompatible header.

    Raises:
        ValueError: If the existing CSV header is incompatible.
    """

    file_path.parent.mkdir(parents=True, exist_ok=True)

    write_header = (
        not file_path.exists()
        or file_path.stat().st_size == 0
    )

    if not write_header:
        with file_path.open(
            mode="r",
            newline="",
            encoding="utf-8",
        ) as file:
            reader = csv.reader(file)
            existing_header = next(reader, None)

        if existing_header != METRICS_FIELDS:
            raise ValueError(
                "The metrics CSV header is incompatible. "
                "Archive the existing file before recording new metrics."
            )

    with file_path.open(
        mode="a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=METRICS_FIELDS,
        )

        if write_header:
            writer.writeheader()

        writer.writerow(metrics)