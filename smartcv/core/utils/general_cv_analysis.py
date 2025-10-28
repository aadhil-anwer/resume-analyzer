import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from core.utils.clean_ai_output import clean_gpt_response 

load_dotenv()
today = datetime.now().strftime("%B %d, %Y")


def gemini_resume_analysis(text: str):
    """
    Analyze a resume using GPT-5 and return clean, properly escaped JSON for the frontend.
    Handles malformed, escaped, or invalid model outputs gracefully.
    """

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "error": "OpenAI API key not found in environment. Set OPENAI_API_KEY to enable AI analysis.",
            "ai_analysis": {
                "ats_score": 0,
                "grammar_feedback": "AI not configured — no grammar analysis performed.",
                "impact_feedback": "AI not configured — no impact analysis performed.",
                "tone_feedback": "N/A",
                "keyword_feedback": "N/A",
                "overall_recommendations": "Set OPENAI_API_KEY to enable full AI scoring.",
                "confidence_score": 0.0,
            },
        }

    try:
        client = OpenAI(api_key=api_key)

        # ------------------ GPT-5 PROMPT ------------------
        prompt = f"""
SYSTEM ROLE:
You are a Fortune 100 recruiter and Certified Professional Resume Writer with 15+ years of experience evaluating resumes for large corporate hiring pipelines. You rigorously assess resumes based on globally recognized professional, structural, and ATS (Applicant Tracking System) standards.

SYSTEM DATE: {today}
You are evaluating this resume as if reviewed today.

You must apply quantitative and qualitative evaluation techniques, including:
- STAR (Situation-Task-Action-Result) and PAR (Problem-Action-Result) frameworks for impact analysis.
- Action verb density scoring (measure strength and variation of bullet openings).
- Quantification presence check (percentages, numbers, metrics, timeframes).
- Tone calibration (formal, recruiter-friendly, confident).
- Keyword diversity measurement (technical + certifications + domain keywords).
- Formatting and ATS-readiness scoring (single-column, readable font, standard section hierarchy).

STRICTNESS RULE:
Be highly conservative and non-liberal when scoring. Never inflate ATS scores for formatting, verbosity, or subjective impressions. Score strictly on factual adherence to professional standards and measurable evidence. Default to the stricter interpretation when uncertain.

WEIGHTED EVALUATION MATRIX (TOTAL 100 POINTS):
1. **Format, Layout & Length (20%)**
   - Must be single-column, text-based, and ATS-parsable. No icons, bars, or two-column templates.
   - Accept 2 pages only if 20+ years of experience explicitly stated.
   - Deduct heavily for Canva/InDesign or other graphical templates.

2. **Grammar, Clarity & Readability (15%)**
   - Must be grammatically flawless, concise, and written in professional tense with zero spelling errors.
   - Bullet length ≤25 words. Deduct for tense inconsistency, verbosity, or typographical issues.
   - Ensure overall tone reads smoothly and clearly to a recruiter.

3. **Experience & Impact (STAR/PAR Framework) (30%)**
   - Every bullet must start with a strong and unique **action verb**.
   - Quantifiable results (%, $, count, time saved, efficiency gained, etc.) required in ≥50% of bullets.
   - Avoid vague duty-based phrasing ("responsible for," "helped with"). Emphasize measurable outcomes.
   - Context must clarify scope (industry, org size, project type, or objective).
   - Deduct for generic, unverifiable, or filler content.

4. **Skills & Keyword Relevance (20%)**
   - Verify that most skills are demonstrated through Experience, Projects, or Education.
   - Heavily penalize unsubstantiated or irrelevant skills.
   - Reject all graphical elements (skill bars, star ratings, or percentages).
   - Reward balanced diversity across technical, analytical, and certification-related keywords.

5. **Tone, Professionalism & Integrity (10%)**
   - Maintain a confident, recruiter-friendly, and formal tone.
   - Avoid first-person language or informal phrasing.
   - Penalize buzzword-stuffing ("highly motivated," "results-driven," etc.).
   - Detect and flag copied job description phrases or inflated achievements.

6. **Contact & File Standards (5%)**
   - Email must be professional (e.g., Gmail/Outlook); reject unprofessional handles.
   - Location format: "City, State" or short equivalent only.
   - Penalize for filenames including dates, roles, or extraneous identifiers.

SCORING GUIDELINES (DO NOT BE LIBERAL):
- Start from 100 and deduct proportionally per the above weight matrix.
- Only resumes that excel across all measurable dimensions may exceed 90.
- 90–100 → Outstanding (rare, Fortune 100–ready)
- 75–89 → Meets Standard (competitive)
- 60–74 → Needs Minor Revision
- 40–59 → Needs Major Revision
- <40 → Unacceptable (structural or ATS failure)

OUTPUT FORMAT (must match exactly):

{{
  "ai_analysis": {{
    "ats_score": (0-100),
    "grammar_feedback": "Brief grammar and clarity summary if issues exist, else a short positive note.",
    "impact_feedback": "Assess use of metrics and action verbs; summarize measurable results quality.",
    "tone_feedback": "Comment on professionalism and recruiter-friendliness of tone.",
    "keyword_feedback": "Comment on skill keyword relevance and diversity (technical, soft, certification).",
    "overall_recommendations": "Provide a concise 2–3 sentence summary of improvement steps or praise.",
    "confidence_score": (0.0-1.0)
  }}
}}

ABSOLUTE OUTPUT RULES:
- Return ONLY one valid JSON object — no markdown, no code fences, no extra text.
- Output must be ONE SINGLE-LINE JSON OBJECT (no newlines, indentation, or explanations).
- The JSON must NOT contain ```json, backticks, or any prefix/suffix text.
- Keep output under 1000 tokens.
- Always include every field listed, even if feedback is positive.
- Grammar and tone notes must be concise but concrete.
- End your response EXACTLY with the final closing curly brace '}}' — nothing else.
- Before sending, internally ensure JSON validity (use compact formatting equivalent to json.dumps(obj, separators=(',', ':'))).

Resume:
{text}

"""


        # ------------------ GPT-5 CALL ------------------
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are an AI resume analysis assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=1,
        )

        raw = response.choices[0].message.content.strip()
        print("\n🔍 RAW GPT-5 RESPONSE:\n", raw, "\n")

        # ------------------ SAFE JSON PARSING ------------------
        if raw.startswith("```json"):
            raw = raw.replace("```json", "").replace("```", "").strip()

        parsed = None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            try:
                parsed = json.loads(json.loads(raw))
            except Exception as e:
                print(f"⚠️ Failed to decode GPT-5 response: {e}")
                return {"error": "GPT-5 response not valid JSON.", "raw_output": raw}

        if not isinstance(parsed, dict):
            return {"error": "Unexpected GPT-5 output structure.", "raw_output": raw}

        ai_analysis = parsed.get("ai_analysis", parsed)
        defaults = {
            "ats_score": 0,
            "grammar_feedback": "",
            "impact_feedback": "",
            "tone_feedback": "",
            "keyword_feedback": "",
            "overall_recommendations": "",
            "confidence_score": 0.0,
        }
        ai_analysis= clean_gpt_response(ai_analysis)
        for key, val in defaults.items():
            ai_analysis.setdefault(key, val)

        return {"ai_analysis": ai_analysis}

    except Exception as e:
        print("❌ GPT-5 API ERROR:", str(e))
        return {"error": f"GPT-5 API call failed: {str(e)}"}
