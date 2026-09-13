import json
import sys
from time import perf_counter

from openai import OpenAIError

from src.metrics_service import build_metrics, save_metrics
from src.openai_service import generate_support_response

def get_user_query() -> str:
    """
    Gets the user query from command-line arguments or interactive input.
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

        start_time = perf_counter()

        response_data, response = generate_support_response(user_query)

        latency_ms = (
            perf_counter() - start_time
        ) * 1000

        print(
            json.dumps(
                response_data,
                indent=2,
                ensure_ascii=False,
            )
        )

        try:
            metrics = build_metrics(
                response=response,
                latency_ms=latency_ms,
            )

            save_metrics(metrics)

        except (ValueError, OSError) as error:
            print(
                f"Metrics error: {error}",
                file=sys.stderr,
            )
            return 1

        return 0

    except ValueError as error:
        print(
            f"Validation error: {error}",
            file=sys.stderr
        )
        return 1

    except OpenAIError as error:
        print(
            f"OpenAI API error: {error}",
            file=sys.stderr,
        )
        return 1

    except OSError as error:
        print(
            f"File error: {error}",
            file=sys.stderr,
        )
        return 1

    except EOFError:
        print(
            "No user input was received.",
            file=sys.stderr,
        )
        return 1

    except KeyboardInterrupt:
        print(
            "\nExecution cancelled by the user.",
            file=sys.stderr,
        )
        return 130

if __name__ == "__main__":
    raise SystemExit(main())