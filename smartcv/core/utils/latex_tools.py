import os
import tempfile
import subprocess

def compile_tex_to_pdf(tex_content):
    """
    Compile a LaTeX string to PDF using tectonic (no shell escape).
    Returns compiled PDF bytes.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = os.path.join(tmpdir, "resume.tex")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(tex_content)

        result = subprocess.run(
            ["tectonic", tex_file, "--outdir", tmpdir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )

        if result.returncode != 0:
            print(tex_content)
            raise Exception(f"Tectonic compile failed: {result.stderr.decode()}")

        pdf_path = os.path.join(tmpdir, "resume.pdf")
        with open(pdf_path, "rb") as f:
            return f.read()
