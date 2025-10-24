
import json
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import os
today = datetime.now().strftime("%B %d, %Y")
load_dotenv()

def gemini_resume_jd_match_analysis(resume_text: str, jd_text: str):
    """Compare resume vs job description and score ATS match."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return {"error": "Missing GEMINI_API_KEY"}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-2.5-pro")

        
        prompt = f"""
SYSTEM ROLE:
You are a Fortune-100 Senior Recruiter and ATS Optimization Specialist with 15+ years of experience hiring across global tech, finance, and consulting organizations.
You are known for critical, data-driven resume benchmarking. You must evaluate a candidate's resume in comparison to *industry-best resumes for that same role* and grade strictly, assuming hundreds of competitive applicants exist.
SYSTEM DATE: {today}
You are evaluating this resume as if reviewed today.
EVALUATION CONTEXT:
You are evaluating this resume against:
1. The provided Job Description (JD)
2. The top 10% of resumes in the same role, based on measurable outcomes, keyword strength, layout precision, and ATS parsing quality
3. Common market expectations for the role (essential certifications, domain tools, methodologies)

INPUT VARIABLES:
• [RESUME TEXT]
• [JOB DESCRIPTION TEXT]

EVALUATION GOAL:
Provide a compact JSON object that evaluates how competitive, ATS-compliant, and employer-ready the resume is — using a realistic, non-liberal grading curve (average resumes score 60–70; only truly exceptional ones exceed 90).

─────────────────────────────
EVALUATION CRITERIA (0–5 EACH)
─────────────────────────────
1. Layout & ATS Compatibility – one-column, text-based, machine-readable
2. Professional Presentation – clean header, contact format, no gimmicks
3. Resume Length – optimal length per experience level (1–2 pages)
4. Skim Value & Readability – logical flow, bullet efficiency, visual hierarchy
5. Summary/Profile Effectiveness – clarity, role focus, value proposition
6. Work Experience Structure – reverse chronology, measurable contributions
7. Language & Tone – professional, confident, not verbose
8. Gaps & Multiple Roles – transparently managed, clear timelines
9. Education Placement/Relevance – appropriate order, key degrees visible
10. Quantifiable Achievements – metrics or tangible results in ≥50% bullets
11. Action-Result Structure – STAR/PAR clarity (context → action → result)
12. Skills Presentation – organized, measurable, realistic
13. Targeted Keyword Alignment – overlap with JD + core industry skills
14. Relevant Placement of Key Content – key qualifications appear early
15. Integrity & Honesty – originality, no job-description copy-paste
16. Job Level Match – candidate experience fits advertised level
17. Market Competitiveness – how it compares to top 10% resumes for the same role (technical depth, leadership, impact, certifications)

─────────────────────────────
ADDITIONAL RULES
─────────────────────────────
• Include a **relative competitiveness score** inside your analysis, comparing it to industry-best candidates for that role.
• If the resume lacks core domain skills that are expected for the role but not mentioned in the JD, deduct points (e.g., cybersecurity → missing SIEM, Nmap, MITRE ATT&CK, etc.).
• Do not inflate scores for presentation; content depth, measurable results, and keywords weigh heavier.
• Consider skill density, modern tool familiarity, and project impact as primary differentiators.

─────────────────────────────
OUTPUT FORMAT (STRICT JSON)
─────────────────────────────
Return ONLY one valid compact JSON object (no markdown, no code fences, no extra text):

{{
  "status": "SUCCESS",
  "evaluation": {{
    "overall_summary": "≤200-word narrative summarizing major strengths, competitive weaknesses, and relative ranking vs industry-best resumes.",
    "criteria": [
      {{"id": 1, "name": "Layout & ATS Compatibility", "score": (0–5), "feedback": "One-sentence justification."}},
      {{"id": 2, "name": "Professional Presentation", "score": (0–5), "feedback": "Explanation."}},
      ...
      {{"id": 17, "name": "Market Competitiveness", "score": (0–5), "feedback": "Describe how this resume compares to top 10% candidates."}}
    ],
    "total_score": "Average of all 17 criteria, rounded to two decimals",
    "competitiveness_percentile": "(Estimated percentile position vs peers, e.g., 'Top 15%' or 'Below Average')",
    "action_recommendation": "One of: 'Immediate Interview', 'Further Review', 'Needs Major Revision', or 'Reject'"
  }}
}}

─────────────────────────────
STRICT OUTPUT RULES
─────────────────────────────
• Respond with **valid compact JSON only** — no markdown, no commentary.
• Include every key listed above, even if feedback is positive.
• Keep total length < 1500 tokens.
• End exactly with the closing curly brace '}}'.
• Internally ensure output would pass Python `json.loads()`.
• Use strict, recruiter-level grading — do NOT give inflated or generous scores.

RESUME TEXT:
{resume_text}

JOB DESCRIPTION TEXT:
{jd_text}
"""

        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 8192,
                "temperature": 0.2,
                "top_p": 0.9
            }
        )

        raw = getattr(response, "text", "").strip()
        try:
            return json.loads(raw)
        except Exception:
            return {"error": "Gemini response invalid", "raw_output": raw}

    except Exception as e:
        return {"error": f"Gemini JD match analysis failed: {str(e)}"}
