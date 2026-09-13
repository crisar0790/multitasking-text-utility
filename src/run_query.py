import json
import sys

from openai import OpenAIError

from src.openai_service import generate_support_response

def get_user_query() -> str:
    """
    Gets the user query from command-line arguments or interactive input.

    Returns:
        The query entered by the user.
    """

    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]).strip()

    return input("Enter your support question: ").strip()

def main() -> int:
    """
    Runs the customer support assistant.

    Returns:
        Process exit code. Zero indicates success.
    """

    try:
        user_query = get_user_query()

        response_data, _ = generate_support_response(user_query)

        print(
            json.dumps(
                response_data,
                indent=2,
                ensure_ascii=False,
            )
        )

        return 0

    except ValueError as error:
        print(f"Validation error: {error}", file=sys.stderr)
        return 1

    except OpenAIError as error:
        print(f"OpenAI API error: {error}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nExecution cancelled by the user.", file=sys.stderr)
        return 130

if __name__ == "__main__":
    raise SystemExit(main())