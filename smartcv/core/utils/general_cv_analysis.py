import json
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import os
today = datetime.now().strftime("%B %d, %Y")
load_dotenv()
# ------------------ GEMINI ANALYSIS ------------------
def gemini_resume_analysis(text: str):
    """
    Send resume to Gemini 2.5 Pro for ATS, grammar, and impact scoring.
    Includes safe fallbacks and structured JSON enforcement.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    # Handle missing API key gracefully
    if not api_key:
        return {
            "error": "Gemini API key not found in environment. Set GEMINI_API_KEY to enable AI analysis.",
            "offline_fallback": {
                "ats_score": 0,
                "grammar_feedback": "AI not configured — no grammar analysis performed.",
                "impact_feedback": "AI not configured — no impact analysis performed.",
                "tone_feedback": "N/A",
                "keyword_feedback": "N/A",
                "overall_recommendations": [
                    "Set up your GEMINI_API_KEY environment variable to enable full AI scoring."
                ],
            },
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-2.5-pro")

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
   - Avoid vague duty-based phrasing (“responsible for,” “helped with”). Emphasize measurable outcomes.
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
   - Penalize buzzword-stuffing (“highly motivated,” “results-driven,” etc.).
   - Detect and flag copied job description phrases or inflated achievements.

6. **Contact & File Standards (5%)**
   - Email must be professional (e.g., Gmail/Outlook); reject unprofessional handles.
   - Location format: “City, State” or short equivalent only.
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

    


        response = model.generate_content(
        prompt,
        generation_config={
        "max_output_tokens": 8192,
        "temperature": 0.2,       # stable responses
        "top_p": 0.9,
        
    }
)
        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            print("\n===== GEMINI TOKEN USAGE =====")
            print(f"Input tokens  : {usage.prompt_token_count}")
            print(f"Output tokens : {usage.candidates_token_count}")
            print(f"Total tokens  : {usage.total_token_count}")
            print("================================\n")
        else:
            print("⚠️ No token usage metadata available in response.")
        # Safely parse model output
        raw = getattr(response, "text", "").strip()
        try:
            return json.loads(raw)
            
        except Exception:
            return {
                "error": "Gemini response not valid JSON.",
                "raw_output": raw  # partial output for debugging
            }
    
        

    except Exception as e:
        return {"error": f"Gemini 2.5 Pro API call failed: {str(e)}"}


