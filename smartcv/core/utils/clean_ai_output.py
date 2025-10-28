import re
import json
import ast
import logging

logger = logging.getLogger(__name__)

def clean_gpt_response(raw_output):
    """
    Cleans messy GPT output and extracts + parses the first valid JSON object.
    Handles both JSON text and accidentally stringified Python dicts.

    Returns:
      dict -> parsed content if valid
      {"error": "..."} -> fallback structure if parsing fails
    """
    try:
        if raw_output is None:
            return {}

        # If GPT already returned a Python dict, just return it.
        if isinstance(raw_output, dict):
            return raw_output

        text = str(raw_output).strip()

        # --- 1️⃣ Basic cleanup ---
        text = re.sub(r"^.*?RAW\s*GPT.*?:", "", text, flags=re.I | re.S)
        text = re.sub(r"```(?:json)?", "", text, flags=re.I)
        text = text.replace("\r", "\n")

        # --- 2️⃣ Find first balanced JSON block ---
        start = text.find("{")
        if start == -1:
            raise ValueError("No opening '{' found in GPT output.")
        depth, in_string, escape = 0, False, False
        end = None
        for i in range(start, len(text)):
            ch = text[i]
            if ch == '"' and not escape:
                in_string = not in_string
            if in_string and ch == "\\" and not escape:
                escape = True
                continue
            if not in_string:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            escape = False
        if end is None:
            raise ValueError("No balanced '}' found for JSON object.")
        json_block = text[start:end + 1].strip()

        # --- 3️⃣ Attempt JSON or Python-dict parsing ---
        parsed = None
        try:
            parsed = json.loads(json_block)
        except json.JSONDecodeError:
            try:
                # Handle accidentally Python dict-style text
                parsed = ast.literal_eval(json_block)
            except Exception:
                raise ValueError("Failed to parse JSON or Python-like dict.")

        # --- 4️⃣ Handle nested JSON strings ---
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except Exception:
                pass

        return parsed

    except Exception as exc:
        preview = (str(raw_output)[:1000] + "...") if len(str(raw_output)) > 1000 else str(raw_output)
        logger.warning(f"⚠️ GPT output cleaning failed: {exc} — raw_preview={preview}")
        return {
            "error": "Failed to decode GPT output",
            "debug": str(exc),
            "raw_preview": preview
        }
