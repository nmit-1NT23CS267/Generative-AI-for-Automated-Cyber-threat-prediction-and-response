from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def write_log(message: str):
    with open("logs/activity.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

@app.get("/")
def home():
    return {"message": "Job Portal Security API is running"}

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    status = "success" if password == "123456" else "failed"
    log_line = f"{datetime.now()} | login | {email} | {status}"
    write_log(log_line)
    return {"email": email, "status": status}

@app.post("/upload-resume")
async def upload_resume(email: str = Form(...), file: UploadFile = File(...)):
    file_path = os.path.join("uploads", file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    log_line = f"{datetime.now()} | resume_upload | {email} | {file.filename} | success"
    write_log(log_line)

    return {"message": "Resume uploaded", "filename": file.filename, "email": email}
