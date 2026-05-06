import streamlit as st
import joblib
import fitz
import numpy as np
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="AI Resume Security", layout="wide")

# Load models
@st.cache_resource
def load_models():
    fake_model = joblib.load('resume_detector.pkl')
    return fake_model

model = load_models()

st.title("Generative AI Resume Security Agent")
st.markdown("**Fake Detection + Anomaly Detection + SQLi/XSS Protection**")

tab1, tab2 = st.tabs(["Fake Detector", "Anomaly Detection"])

# TAB 1: Fake Detector
with tab1:
    st.header("Scan for Fake Resumes & Attacks")
    uploaded_file = st.file_uploader("📤 Upload PDF", type=['pdf'])
    
    if uploaded_file is not None:
        with st.spinner("🔍 Analyzing..."):
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
        
        prob = model.predict_proba([text])[0]
        pred = model.classes_[np.argmax(prob)]
        
        col1, col2 = st.columns(2)
        with col1:
            st.header(f"**{pred.upper()}**")
            if pred == 'fake':
                st.error("🚨 **SQLi/XSS Attack or Fake Resume**")
            else:
                st.success("Legitimate Resume")
        
        with col2:
            st.metric("Real", f"{prob[0]:.0%}")
            st.metric("Fake/Attack", f"{prob[1]:.0%}")
        
        st.subheader("📄 Preview")
        st.text_area("", text[:800], height=200)

# TAB 2: Anomaly Detection  
with tab2:
    st.header("Detect Unusual Patterns")
    uploaded_file = st.file_uploader("📤 Upload PDF", type=['pdf'], key="anomaly")
    
    if uploaded_file is not None:
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        # Anomaly features
        length = len(text)
        words = len(text.split())
        unique_words = len(set(text.split()))
        avg_word_len = np.mean([len(w) for w in text.split() if w])
        
        st.metric("Length", f"{length:,}")
        st.metric("Words", f"{words:,}")
        st.metric("Unique Words", f"{unique_words:,}")
        
        # Anomaly rules
        anomalies = []
        if length < 500:
            anomalies.append("Too short")
        if length > 15000:
            anomalies.append("Too long") 
        if unique_words / words < 0.6:
            anomalies.append("Repetitive text")
        if avg_word_len < 3:
            anomalies.append("Suspicious words")
        
        if anomalies:
            st.error("ANOMALIES DETECTED:")
            for a in anomalies:
                st.write(a)
        else:
            st.success("Normal Resume Pattern")

st.markdown("---")
#st.caption("Trained on 500+ resumes | Ready for May 11 demo")
