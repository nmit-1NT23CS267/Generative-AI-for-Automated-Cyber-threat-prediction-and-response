import pandas as pd
import os

# Load labels
df = pd.read_csv('data/labels.csv')
print("Your resumes:")
print(df.head(20))  # Shows first 20

# Count files
resume_dir = 'data/resumes/'
num_resumes = len([f for f in os.listdir(resume_dir) if f.endswith('.pdf')])
print(f"\nTotal PDFs found: {num_resumes}")
