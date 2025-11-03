import os
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_latex_resume(
    resume_text: str,
    ai_suggestions: Dict[str, Any],
    *,
    system_prompt_file: str = "latex_system_prompt.txt",
    template_file: str = "latex_temp_1.txt",
    model: str = "gpt-5",
    max_retries: int = 2,
) -> str:
    """
    Generate an ATS-optimized LaTeX resume using GPT-5.
    Combines a system prompt and a LaTeX template file, then
    feeds resume data + AI suggestions to produce final LaTeX code.

    Parameters
    ----------
    resume_text : str
        Raw resume text.
    ai_suggestions : dict
        AI-generated analysis/suggestions.
    system_prompt_file : str
        Path to the system prompt text file.
    template_file : str
        Path to the LaTeX template file.
    model : str
        OpenAI model to use (default: "gpt-5").
    max_retries : int
        Retry attempts on transient errors.
    """

    base_dir = os.path.dirname(__file__)
    system_prompt_path = os.path.join(base_dir, system_prompt_file)
    template_path = os.path.join(base_dir, template_file)

    # --- Validation ---
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("❌ Missing OPENAI_API_KEY in .env file.")
    if not os.path.exists(system_prompt_path):
        raise FileNotFoundError(f"System prompt not found: {system_prompt_path}")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")

    # --- Load prompt & template ---
    with open(system_prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    with open(template_path, "r", encoding="utf-8") as f:
        latex_template = f.read()

    # Replace placeholder {{TEMPLATE}} inside system prompt
    if "{{TEMPLATE}}" in system_prompt:
        system_prompt = system_prompt.replace("{{TEMPLATE}}", latex_template)
    else:
        system_prompt += "\n\n" + latex_template

    # --- Prepare user input ---
    suggestions_json = json.dumps(ai_suggestions, indent=2, ensure_ascii=False)
    user_input = f"""
RAW RESUME TEXT:
{resume_text}

ATS SCORE AND SUGGESTIONS:
{suggestions_json}

Please generate the final LaTeX resume using the provided template and instructions.
Return only the LaTeX code — no explanations, no markdown fences.
"""

    logger.info(f"🚀 Starting GPT-5 LaTeX generation using model `{model}`")

    # --- GPT API call ---
    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 2):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
            )

            # Extract response content safely
            content = ""
            if hasattr(response, "choices") and response.choices:
                msg = getattr(response.choices[0], "message", None)
                if msg and hasattr(msg, "content"):
                    content = msg.content
                elif isinstance(response.choices[0], dict):
                    content = response.choices[0].get("message", {}).get("content", "")
            if not content:
                raise ValueError("Empty response from GPT-5 API")

            # Clean markdown fences if any
            cleaned_output = (
                content.replace("```latex", "")
                .replace("```", "")
                .strip()
            )

            logger.info("✅ LaTeX generation successful.")
            return cleaned_output

        except Exception as e:
            logger.warning(f"⚠️ Attempt {attempt} failed: {e}")
            last_error = e
            if attempt == max_retries + 1:
                raise RuntimeError(f"❌ GPT-5 failed after {attempt} attempts: {e}")

    raise RuntimeError("Unexpected error during LaTeX generation") from last_error
