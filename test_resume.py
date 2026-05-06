import joblib
import fitz
import sys
import numpy as np

# Load model
model = joblib.load('resume_detector.pkl')

def scan_resume(file_path):
    # Extract text
    doc = fitz.open(file_path)
    text = ''.join(page.get_text() for page in doc)
    
    # Predict
    prob = model.predict_proba([text])[0]
    pred = model.classes_[np.argmax(prob)]
    
    print(f"{file_path}")
    print(f"Prediction: {pred}")
    print(f"Real prob: {prob[0]:.1%} | Fake prob: {prob[1]:.1%}")
    if pred == 'fake':
        print("ALERT: Fake resume or attack detected!")
    print()

# Test all PDFs
for file in sys.argv[1:] or ['resume_0001.pdf']:
    scan_resume(file)
