import json
import logging

from typing import Any

from src.config import (
    MAX_OUTPUT_TOKENS,
    OPENAI_MODEL,
    get_openai_client,
)

from src.safety import (
    analyze_input,
    create_safety_fallback,
    log_safety_event,
)

from src.prompt_loader import load_prompt

from src.schema import (
    RESPONSE_SCHEMA,
    validate_response,
)

logger = logging.getLogger(__name__)

def generate_support_response(user_query: str) -> tuple[dict[str, Any], Any]:
    """
    Generate and validate a structured support response.

    Recognized sensitive data is redacted before sending the query.
    Suspicious input is logged but is not automatically blocked.
    A native model refusal produces a contract-valid fallback.

    Returns:
        The validated response and the original OpenAI response.

    Raises:
        ValueError: If the query or generated response is invalid.
    """

    if not isinstance(user_query, str) or not user_query.strip():
        raise ValueError(
            "The user query cannot be empty."
        )

    analysis = analyze_input(user_query.strip())

    if analysis["manipulation_patterns"] or analysis["redacted_count"]:
        try:
            log_safety_event(
                event_type="input_analysis",
                decision="continue_with_sanitized_input",
                manipulation_patterns=analysis["manipulation_patterns"],
                redacted_count=analysis["redacted_count"],
                redacted_query=analysis["clean_text"],
            )
        except OSError:
            logger.warning("Could not save the input safety event.")

    client = get_openai_client()
    prompt = load_prompt()

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=prompt,
        input=analysis["clean_text"],
        max_output_tokens=MAX_OUTPUT_TOKENS,
        text={
            "format": {
                "type": "json_schema",
                "name": "support_response",
                "strict": True,
                "schema": RESPONSE_SCHEMA,
            }
        },
        store=False,
    )

    if response.status != "completed":
        incomplete_details = getattr(
            response,
            "incomplete_details",
            None,
        )

        reason = getattr(
            incomplete_details,
            "reason",
            response.status,
        )

        raise ValueError(
            f"OpenAI response was not completed: {reason}"
        )

    for item in response.output:
        if item.type != "message":
            continue

        for content in item.content:
            if content.type == "refusal":
                fallback = create_safety_fallback()

                if not validate_response(fallback):
                    raise ValueError(
                        "Safety fallback does not match "
                        "the expected schema."
                    )

                try:
                    log_safety_event(
                        event_type="model_refusal",
                        decision="safe_fallback",
                        response_id=response.id,
                        manipulation_patterns=(
                            analysis["manipulation_patterns"]
                        ),
                        redacted_count=analysis["redacted_count"],
                        redacted_query=analysis["clean_text"],
                    )
                except OSError:
                    logger.warning(
                        "Could not save the refusal safety event."
                    )

                return fallback, response

    if not response.output_text:
        raise ValueError("OpenAI returned an empty response.")

    try:
        response_data = json.loads(response.output_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            "OpenAI returned an invalid JSON response."
        ) from error

    if not validate_response(response_data):
        raise ValueError(
            "OpenAI response does not match the expected schema."
        )

    return response_data, response
