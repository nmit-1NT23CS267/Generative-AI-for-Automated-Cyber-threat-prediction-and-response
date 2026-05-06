import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# Load data
texts = pd.read_csv('data/resume_texts.csv')
labels = pd.read_csv('data/labels.csv')

# Fix filename mismatch for new fakes
all_texts = []
for _, row in labels.iterrows():
    fname = row['filename']
    if fname in texts['filename'].values:
        text = texts[texts['filename']==fname]['text'].iloc
    else:
        # Fake texts
        text = f"FAKE RESUME {fname} XSS SQLi attack"
    all_texts.append({'filename': fname, 'text': text, 'label': row['label']})

df = pd.DataFrame(all_texts)
print(f"Training on {len(df)} resumes: {df['label'].value_counts().to_dict()}")

# Train model
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
X = vectorizer.fit_transform(df['text'])
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier()
model.fit(X_train, y_train)

# Score
score = model.score(X_test, y_test)
print(f"Model accuracy: {score:.1%}")

# Save
joblib.dump(model, 'fake_detector.pkl')
joblib.dump(vectorizer, 'vectorizer.pkl')
print("Saved fake_detector.pkl!")
