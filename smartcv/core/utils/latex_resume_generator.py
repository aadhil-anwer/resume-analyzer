import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_latex_resume(resume_text: str, ai_suggestions: dict) -> str:
    """
    Generate an ATS-optimized LaTeX resume using GPT-5-mini based on:
    - the user's raw resume text
    - the ATS feedback / improvement suggestions
    - a predefined LaTeX template (latex_temp_1.txt)

    Returns:
        str: The final valid LaTeX code (ready to compile)
    """

    # --- Load system prompt (truth-preserving ATS resume generator) ---
    prompt_path = os.path.join(os.path.dirname(__file__), "latex_system_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # --- Load LaTeX template file ---
    template_path = os.path.join(os.path.dirname(__file__), "latex_temp_1.txt")
    with open(template_path, "r", encoding="utf-8") as f:
        base_template = f.read()

    # Replace the placeholder {{TEMPLATE}} in system prompt with actual template content
    system_prompt = system_prompt.replace("{{TEMPLATE}}", base_template)

    # --- Prepare the model input ---
    user_input = f"""
    RAW RESUME TEXT:
    {resume_text}

    ATS SCORE AND SUGGESTIONS:
    {json.dumps(ai_suggestions, indent=2, ensure_ascii=False)}
    """
    print("=== DEBUG RESUME TEXT ===")
    print(resume_text[:500])  # print first 500 chars
    print("=========================")

    print("=== DEBUG AI SUGGESTIONS ===")
    print(json.dumps(ai_suggestions, indent=2))
    print("============================")

    # --- Call OpenAI GPT-5-mini ---
    response = client.responses.create(
    model="gpt-5-mini",
    input=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ],

)

# --- ✅ Print token usage ---
    if hasattr(response, "usage"):
        usage = response.usage
        input_tokens = getattr(usage, "input_tokens", 0)
        output_tokens = getattr(usage, "output_tokens", 0)
        total_tokens = getattr(usage, "total_tokens", 0)

        print(f"🧮 GPT Token Usage:")
        print(f"   Input Tokens : {input_tokens}")
        print(f"   Output Tokens: {output_tokens}")
        print(f"   Total Tokens : {total_tokens}")
    else:
        print("⚠️ No token usage data returned in response.")

    # --- Extract output ---
    final_output = response.output_text.strip()


    # --- Safety cleanup ---
    # Sometimes models output code fences or markdown accidentally — ensure clean LaTeX only
    return final_output
