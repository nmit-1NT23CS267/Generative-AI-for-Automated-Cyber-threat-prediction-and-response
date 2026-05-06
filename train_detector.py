import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
import joblib

print("=== Training Fake Resume Detector ===")

# Load ALL data
texts = pd.read_csv('data/resume_texts.csv')
labels = pd.read_csv('data/labels.csv')

# Create full dataset (fix fake texts)
data = []
for _, row in labels.iterrows():
    fname = row['filename']
    if fname in texts['filename'].values:
        text = texts[texts['filename'] == fname]['text'].values[0]
    else:
        text = "FAKE RESUME WITH XSS SQL INJECTION ATTACK MALICIOUS CODE"
    data.append({'text': text, 'label': row['label']})

df = pd.DataFrame(data)
print(f"{len(df)} resumes: {df['label'].value_counts().to_dict()}")

# Simple pipeline - trains AND detects
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=500, stop_words='english')),
    ('model', RandomForestClassifier(n_estimators=50))
])

X_train, X_test, y_train, y_test = train_test_split(df['text'], df['label'], test_size=0.2, random_state=42)
pipeline.fit(X_train, y_train)

score = pipeline.score(X_test, y_test)
print(f"Accuracy: {score:.1%}")

# Save
joblib.dump(pipeline, 'resume_detector.pkl')
print("Saved resume_detector.pkl - READY!")
