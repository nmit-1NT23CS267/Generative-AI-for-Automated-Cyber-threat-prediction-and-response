import streamlit as st
import requests
from datetime import datetime


# Page config
st.set_page_config(page_title="Cyber Recruitment Platform", layout="wide")


# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'token' not in st.session_state:
    st.session_state.token = None


# Login function
def login(username, password):
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.logged_in = True
            st.session_state.user_info = data
            st.session_state.token = data['access_token']
            return True
        else:
            return False
    except requests.RequestException as error:
        st.error(f"Backend connection failed: {error}")
        return False


# Login page
if not st.session_state.logged_in:
    st.title("🔐 Cyber Recruitment Platform")
    
    # Tab for login and register
    tab1, tab2 = st.tabs(["Login", "Register as Candidate"])
    
    with tab1:
        st.markdown("### Please login to continue")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    with tab2:
        st.markdown("### Create Candidate Account")
        
        with st.form("register_form"):
            reg_username = st.text_input("Username")
            reg_email = st.text_input("Email")
            reg_password = st.text_input("Password", type="password")
            reg_name = st.text_input("Full Name")
            reg_phone = st.text_input("Phone")
            reg_skills = st.text_input("Skills (comma separated)")
            reg_exp = st.number_input("Experience Years", min_value=0, value=0)
            
            submit_reg = st.form_submit_button("Register")
            
            if submit_reg:
                skills_list = [s.strip() for s in reg_skills.split(',')] if reg_skills else []
                
                response = requests.post(
                    "http://127.0.0.1:8000/api/recruitment/candidate/register",
                    json={
                        "username": reg_username,
                        "email": reg_email,
                        "password": reg_password,
                        "full_name": reg_name,
                        "phone": reg_phone,
                        "skills": skills_list,
                        "experience_years": reg_exp
                    }
                )
                
                if response.status_code == 200:
                    st.success("Registration successful! Please login.")
                else:
                    try:
                        error_data = response.json()
                        error_message = error_data.get("detail", "Registration failed")
                    except requests.exceptions.JSONDecodeError:
                        error_message = f"Server returned status {response.status_code}: {response.text[:200]}"

                    st.error(error_message)
    
    st.markdown("---")
    st.info("**Demo credentials:**\n- admin / admin123\n- recruiter / admin123\n- tester / admin123")
    st.stop()


# Main dashboard
st.title(f"🏢 Cyber Recruitment Platform")
st.markdown(f"**Welcome, {st.session_state.user_info['username']}** ({st.session_state.user_info['role']})")


# Logout button
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.session_state.token = None
    st.rerun()


# Role-based views
user_role = st.session_state.user_info['role']
token = st.session_state.token
headers = {"Authorization": f"Bearer {token}"}


# ==================== CANDIDATE VIEW ====================
if user_role == 'candidate':
    st.header("📋 Job Search & Applications")
    
    # Sidebar navigation
    candidate_menu = st.sidebar.radio("Menu", ["Search Jobs", "My Applications", "My Profile"])
    
    if candidate_menu == "Search Jobs":
        st.subheader("🔍 Available Jobs")
        
        if st.button("🔄 Refresh Jobs"):
            st.rerun()
        
        try:
            response = requests.get("http://127.0.0.1:8000/api/recruitment/jobs", headers=headers)
            if response.status_code == 200:
                jobs = response.json().get('jobs', [])
                
                if jobs:
                    for job in jobs:
                        with st.expander(f"💼 {job['title']} at {job.get('company_name', 'Company')}"):
                            st.markdown(f"**Location:** {job['location']}")
                            st.markdown(f"**Salary:** {job['salary_range']}")
                            st.markdown(f"**Description:** {job['description']}")
                            st.markdown(f"**Requirements:** {', '.join(job['requirements'])}")
                            
                            if st.button(f"Apply Now", key=f"apply_{job['job_id']}"):
                                apply_response = requests.post(
                                    "http://127.0.0.1:8000/api/recruitment/apply",
                                    headers=headers,
                                    json={"job_id": job['job_id']}
                                )
                                if apply_response.status_code == 200:
                                    st.success("Application submitted!")
                                else:
                                    st.error(apply_response.json().get('detail', 'Failed to apply'))
                else:
                    st.info("No jobs available")
            else:
                st.error(f"Error loading jobs: {response.status_code}")
        except Exception as e:
            st.error(f"Error: {e}")
    
    elif candidate_menu == "My Applications":
        st.subheader("📬 My Job Applications")
        
        if st.button("🔄 Refresh Applications"):
            st.rerun()
        
        try:
            response = requests.get("http://127.0.0.1:8000/api/recruitment/applications", headers=headers)
            if response.status_code == 200:
                applications = response.json().get('applications', [])
                
                if applications:
                    for app in applications:
                        st.markdown(f"**{app['job_title']}** - Status: {app['status']} (Applied: {app['applied_at']})")
                else:
                    st.info("No applications yet")
        except Exception as e:
            st.error(f"Error: {e}")
    
    elif candidate_menu == "My Profile":
        st.subheader("👤 My Profile")
        st.info("Profile management - coming soon")


# ==================== RECRUITER VIEW ====================
elif user_role == 'recruiter':
    st.header("👔 Recruiter Dashboard")
    
    recruiter_menu = st.sidebar.radio("Menu", ["Post Job", "View Applications", "Company Profile"])
    
    if recruiter_menu == "Post Job":
        st.subheader("📝 Create New Job Posting")
        
        with st.form("job_form"):
            title = st.text_input("Job Title")
            description = st.text_area("Job Description")
            requirements = st.text_area("Requirements (comma separated)")
            location = st.text_input("Location")
            salary = st.text_input("Salary Range")
            
            submit = st.form_submit_button("Post Job")
            
            if submit:
                req_list = [r.strip() for r in requirements.split(',')]
                
                response = requests.post(
                    "http://127.0.0.1:8000/api/recruitment/jobs",
                    headers=headers,
                    json={
                        "title": title,
                        "description": description,
                        "requirements": req_list,
                        "location": location,
                        "salary_range": salary
                    }
                )
                
                if response.status_code == 200:
                    st.success("Job posted successfully!")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                        
    elif recruiter_menu == "View Applications":
        st.subheader("📬 Candidate Applications")
        
        if st.button("🔄 Refresh Applications"):
            st.rerun()
        
        try:
            response = requests.get("http://127.0.0.1:8000/api/recruitment/applications", headers=headers)
            if response.status_code == 200:
                applications = response.json().get('applications', [])
                
                if applications:
                    for app in applications:
                        st.markdown(f"**{app['candidate_name']}** applied for **{app['job_title']}** - {app['status']}")
                else:
                    st.info("No applications yet")
        except Exception as e:
            st.error(f"Error: {e}")
    
    elif recruiter_menu == "Company Profile":
        st.subheader("🏢 Company Profile")
        
        with st.form("company_form"):
            company_name = st.text_input("Company Name")
            description = st.text_area("Company Description")
            website = st.text_input("Website URL")
            
            submit = st.form_submit_button("Create/Update Company")
            
            if submit:
                response = requests.post(
                    "http://127.0.0.1:8000/api/recruitment/company",
                    data={
                        "company_name": company_name,
                        "description": description,
                        "website": website,
                        "token": token
                    }
                )
                
                if response.status_code == 200:
                    st.success("Company profile created!")
                else:
                    st.error(f"Error: {response.json().get('detail', 'Failed to create')}")


# ==================== TESTER VIEW ====================
elif user_role == 'tester':
    st.header("🔐 Security Testing Dashboard")
    st.warning("⚠️ You have access to security testing tools only. Job search is restricted for testers.")
    
    tester_menu = st.sidebar.radio("Menu", ["Run Tests", "Test History"])
    
    if tester_menu == "Run Tests":
        st.subheader("🎯 Security Test Simulations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Attack Simulations")
            
            if st.button("Brute Force Test"):
                response = requests.post(
                    "http://127.0.0.1:8000/api/recruitment/test/brute-force",
                    headers=headers
                )
                if response.status_code == 200:
                    result = response.json()
                    st.success(result.get("message", "Test completed"))
                    st.info(result.get("result", ""))
                else:
                    st.error(f"Test failed: HTTP {response.status_code}")
                    st.code(response.text)

            if st.button("SQL Injection Test"):
                response = requests.post(
                    "http://127.0.0.1:8000/api/recruitment/test/sqli",
                    headers=headers
                )
                if response.status_code == 200:
                    result = response.json()
                    st.success(result.get("message", "Test completed"))
                    st.info(result.get("result", ""))
                else:
                    st.error(f"Test failed: HTTP {response.status_code}")
                    st.code(response.text)

            if st.button("Bot Activity Test"):
                response = requests.post(
                    "http://127.0.0.1:8000/api/recruitment/test/bot",
                    headers=headers
                )
                if response.status_code == 200:
                    result = response.json()
                    st.success(result.get("message", "Test completed"))
                    st.info(f"Filename: {result.get('filename', '')}")
                    st.write("Threats:", result.get("threats", []))
                else:
                    st.error(f"Upload test failed: HTTP {response.status_code}")
                    st.code(response.text)
        
        with col2:
            st.markdown("### File Upload Test")
            
            uploaded_file = st.file_uploader("Upload test file", type=['pdf', 'doc', 'docx', 'txt'])
            
            if uploaded_file and st.button("📁 Test Malicious Upload"):
                files = {"file": uploaded_file}
                data = {"token": token}
                
                response = requests.post(
                    "http://127.0.0.1:8000/api/recruitment/test/malicious-upload",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    st.success(response.json().get('message', 'Test completed'))
                    st.info(f"Filename: {response.json().get('filename', '')}")
    
    elif tester_menu == "Test History":
        st.subheader("📊 Previous Test Results")
        st.info("Test history - coming soon")


# ==================== ADMIN VIEW ====================
elif user_role == 'admin':
    st.header("👑 Admin Dashboard")
    
    st.subheader("System Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Users", "Loading...")
    
    with col2:
        st.metric("Active Jobs", "Loading...")
    
    with col3:
        st.metric("Total Applications", "Loading...")
    
    st.subheader("User Management")
    st.info("User management features - coming soon")
    
    st.subheader("Security Logs")
    st.info("Security monitoring - coming soon")