import sys

from llm_client import GenerationError, ask_model, get_model_name


def main() -> int:
    try:
        reply = ask_model(
            "You are a helpful assistant.",
            "Reply with one short sentence confirming the connection works.",
        )
    except GenerationError as exc:
        print(f"Connection test failed: {exc}")
        return 1
    except Exception as exc:  
        print(f"Connection test failed with an unexpected error: {exc}")
        return 1

    print(f"Model: {get_model_name()}")
    print(f"Reply: {reply}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
