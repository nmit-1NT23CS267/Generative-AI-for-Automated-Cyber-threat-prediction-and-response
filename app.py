import streamlit as st
import joblib
import fitz
import numpy as np
import pandas as pd
from io import BytesIO

# Load model
@st.cache_resource
def load_model():
    return joblib.load('resume_detector.pkl')

model = load_model()
st.title("AI Resume Security Agent")
st.write("**Detects fake resumes, SQLi/XSS attacks**")

# File upload
uploaded_file = st.file_uploader("Upload PDF Resume", type=['pdf'])

if uploaded_file:
    # Extract text
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    
    # Predict
    prob = model.predict_proba([text])[0]
    pred = model.classes_[np.argmax(prob)]
    
    st.header(f"**Result: {pred.upper()}**")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Real", f"{prob[0]:.0%}")
    with col2:
        st.metric("Fake/Attack", f"{prob[1]:.0%}")
    
    if pred == 'fake':
        st.error("MALICIOUS RESUME - Possible SQLi/XSS attack!")
    else:
        st.success("LEGITIMATE RESUME")
    
    st.text_area("Preview:", text[:500], height=200)
