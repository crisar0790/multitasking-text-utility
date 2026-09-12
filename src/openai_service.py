import json

from typing import Any

from src.config import (
    MAX_OUTPUT_TOKENS,
    OPENAI_MODEL,
    get_openai_client,
)

from src.prompt_loader import load_prompt

from src.schema import (
    RESPONSE_SCHEMA,
    validate_response,
)

def generate_support_response(user_query: str) -> tuple[dict[str, Any], Any]:
    """
    Sends a user query to OpenAi and returns a validated response.

    Args:
        user_query: Customer support question.

    Returns:
        A tuple contsining:
        - The validated structured response.
        - The original OpenAi response.

    Raises:
        ValueError: If the query is empty or response is invalid.
    """

    if not isinstance(user_query, str) or not user_query.strip():
        raise ValueError(
            "The user query cannot be empty."
        )

    client = get_openai_client()
    prompt = load_prompt()

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=prompt,
        input=user_query.strip(),
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
