import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
import joblib

print("Training Fake Resume Detector...")

# Load texts
texts_df = pd.read_csv('data/resume_texts.csv')

# Create training data
train_data = []
train_labels = []

for _, label_row in pd.read_csv('data/labels.csv').iterrows():
    filename = label_row['filename']
    label = label_row['label']
    
    if filename in texts_df['filename'].values:
        text = texts_df[texts_df['filename'] == filename]['text'].iloc[0]
    else:
        text = "FAKE RESUME XSS SQL INJECTION <script>alert('hack')</script> ' OR 1=1 -- DROP TABLE"
    
    train_data.append(text)
    train_labels.append(label)

print(f"{len(train_data)} resumes loaded: {pd.Series(train_labels).value_counts().to_dict()}")

# Train pipeline
X_train, X_test, y_train, y_test = train_test_split(train_data, train_labels, test_size=0.2, random_state=42)

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=300, stop_words='english', ngram_range=(1,2))),
    ('clf', RandomForestClassifier(n_estimators=30, random_state=42))
])

pipeline.fit(X_train, y_train)
accuracy = pipeline.score(X_test, y_test)

print(f"Model Accuracy: {accuracy:.1%}")
print("Examples:")
for text, pred in zip(X_test[:3], pipeline.predict(X_test[:3])):
    print(f"  Predicted: {pred} | Text preview: {text[:100]}...")

# Save model
joblib.dump(pipeline, 'resume_detector.pkl')
#print("\nModel saved as resume_detector.pkl ")
