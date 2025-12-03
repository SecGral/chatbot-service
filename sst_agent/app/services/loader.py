from pypdf import PdfReader
from docx import Document
import os

DATA_FOLDER = "sst_agent/app/data/docs"

def load_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def load_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def load_file(path):
    if path.endswith(".pdf"):
        return load_pdf(path)
    elif path.endswith(".docx"):
        return load_docx(path)
    elif path.endswith(".txt"):
        return open(path, encoding="utf8").read()
    else:
        raise ValueError("Formato no soportado")

def get_all_files():
    files = []
    for f in os.listdir(DATA_FOLDER):
        if f.endswith((".pdf", ".docx", ".txt")):
            files.append(os.path.join(DATA_FOLDER, f))
    return files
