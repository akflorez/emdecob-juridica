import docx
import os

doc_path = r"c:\Users\ANA KARINA\Desktop\emdecob consultas\paso a paso.docx"

if os.path.exists(doc_path):
    doc = docx.Document(doc_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    print("\n".join(full_text))
else:
    print(f"File not found: {doc_path}")
