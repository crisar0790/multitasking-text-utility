from pathlib import Path

from src.config import BASE_DIR

DEFAULT_PROMPT_PATH = BASE_DIR / "prompts" /"main_prompt.md"

def load_prompt(prompt_path: Path = DEFAULT_PROMPT_PATH) -> str:
    """
    Loads the prompt template from a Markdown file.

    Args:
        prompt_path: Path to prompt file.

    Returns:
        The prompt content without leading or trailing whitespace.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
        ValueError: If the prompt file is empty.
    """

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_path}"
        )

    prompt_content = prompt_path.read_text(encoding="utf-8").strip()

    if not prompt_content:
        raise ValueError(
            f"Prompt file is empty: {prompt_path}"
        )

    return prompt_content