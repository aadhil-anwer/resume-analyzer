\# 🧠 Resume Rater



> AI-powered resume rating, optimization, and LaTeX generation system.



Resume Rater is an intelligent system that evaluates resumes against job descriptions using ATS-style logic and generates perfectly formatted LaTeX resumes based on actionable suggestions.  

It combines smart resume analytics, ATS compliance, and instant LaTeX rendering — all in one streamlined platform.



---



\## 🚀 Features



\- \*\*📄 Resume Evaluation\*\*

&nbsp; - Rates resumes from \*\*0–5\*\* based on JD match.

&nbsp; - Provides granular breakdowns for \*\*skills\*\*, \*\*experience\*\*, and \*\*ATS compliance\*\*.

&nbsp; - Uses a \*\*weighted scoring algorithm\*\* to mimic real ATS and recruiter behavior.



\- \*\*🧩 Suggestion Engine\*\*

&nbsp; - Generates AI-based improvement tips for wording, formatting, and keyword optimization.

&nbsp; - Recommends \*\*bullet rewriting\*\*, \*\*impact phrases\*\*, and \*\*role alignment\*\*.



\- \*\*🪶 LaTeX Resume Generator\*\*

&nbsp; - Converts raw or optimized text into \*\*beautiful LaTeX resumes\*\*.

&nbsp; - Uses modular templates with guaranteed \*\*zero compilation errors\*\*.

&nbsp; - Supports both \*\*generic ATS\*\* and \*\*JD-specific\*\* versions.



\- \*\*⚙️ Integration Friendly\*\*

&nbsp; - Supports resume parsing from PDF/DOCX (via Tesseract + PyMuPDF).

&nbsp; - Modular architecture — ready for API and Gemini/GPT integration.

&nbsp; - Future support for \*\*automatic resume rebuilding\*\* via feedback loops.



---



\## 🧰 Tech Stack



| Layer | Tools / Frameworks |

|-------|--------------------|

| \*\*Backend\*\* | Django, Python, REST Framework |

| \*\*AI/ML\*\* | GPT-5 / Gemini, Resume Scoring Logic |

| \*\*Parsing\*\* | PyMuPDF, python-docx, Tesseract OCR |

| \*\*Template Engine\*\* | LaTeX, Custom Resume Templates |

| \*\*Frontend (planned)\*\* | React / Tailwind (for resume builder UI) |

| \*\*Database\*\* | SQLite (dev), PostgreSQL (prod) |



---



\## 🧑‍💻 Development Setup



```bash

\# 1️⃣ Clone repository

git clone https://github.com/yourusername/resume-rater.git

cd resume-rater



\# 2️⃣ Install dependencies

pip install -r requirements.txt



\# 3️⃣ Run server

python manage.py runserver



