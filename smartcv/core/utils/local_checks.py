


import re

# ------------------ LOCAL RULE CHECKS ------------------
def run_local_checks(text: str):
    """Improved deterministic pre-check before AI call."""
    feedback = []
    failed = False
    words = len(text.split())
    text_lower = text.lower()

    # --- 1. Basic length sanity ---
    if words < 150:
        feedback.append("Resume seems too short (<150 words). Add more experience or details.")
        failed = True
    elif words > 1200:
        feedback.append("Resume seems too long (>1200 words). Condense to 1–2 pages.")
        failed = True

    # --- 2. Flexible section check ---
    exp_aliases = [
        "experience", "work experience", "employment", "career history",
        "professional experience", "internship", "projects", "work history"
    ]
    edu_aliases = [
        "education", "academic background", "qualifications", "academics",
        "educational qualifications", "degree", "university"
    ]

    has_exp = any(a in text_lower for a in exp_aliases)
    has_edu = any(a in text_lower for a in edu_aliases)

    if not has_exp or not has_edu:
        missing = []
        if not has_exp: missing.append("Experience")
        if not has_edu: missing.append("Education")
        feedback.append(f"Missing key section(s): {', '.join(missing)}.")
        failed = True

    # --- 3. Bullet point presence ---
    if not any(sym in text for sym in ['-', '*', '•']):
        feedback.append("No bullet points detected. Use '-' or '*' for clarity.")
        failed = True

    # --- 4. Sensitive info check ---
    if re.search(r'\b(age|gender|religion|married|nationality)\b', text_lower):
        feedback.append("Contains personal info (age, gender, religion, etc.). Remove it.")

    # --- 5. Contact info check ---
    if not re.search(r'[\w\.-]+@[\w\.-]+\.\w{2,}', text):
        feedback.append("Missing a valid email address.")
        failed = True

    return {"failed": failed, "feedback": feedback}


