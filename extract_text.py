import fitz  # PyMuPDF
import pandas as pd
import os

df = pd.read_csv('data/labels.csv')

texts = []
for _, row in df.iterrows():
    filename = row['filename']
    try:
        # Fix .txt vs .pdf mismatch
        pdf_path = filename.replace('.txt', '.pdf')
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        texts.append({'filename': filename, 'text': text[:500] + '...'})
        print(f"{filename}: {len(text)} chars")
    except:
        print(f"{filename} missing")

# Save texts
text_df = pd.DataFrame(texts)
text_df.to_csv('data/resume_texts.csv', index=False)
print("\nSaved resume_texts.csv!")
