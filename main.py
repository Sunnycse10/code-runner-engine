import os
import uuid
import base64
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Platform Engine Code Runner")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "Sunnycse10/code-runner-engine" 

db = {}

@app.post("/submit")
async def submit(code: str, tests: str, callback_url: str):
    sub_id = str(uuid.uuid4())
    db[sub_id] = "In Queue"
    
    dispatch_url = f"https://api.github.com/repos/{REPO}/dispatches"
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "event_type": "run_submission",
        "client_payload": {
            "submission_id": sub_id,
            "code": code,
            "tests": tests,
            "callback_url": callback_url
        }
    }
    
    response = requests.post(dispatch_url, json=payload, headers=headers)
    return {"submission_id": sub_id, "github_status": response.status_code}

@app.post("/callback")
async def callback(request: Request):
    data = await request.json()
    sub_id = data.get("submission_id")
    job_status = data.get("status")
    
    raw_output = data.get("output")
    output = base64.b64decode(raw_output).decode("utf-8") if raw_output else "No output"
    db[sub_id] = f"[{job_status.upper()}] {output}"
    print(f"--- Result for {sub_id} received: {job_status} ---")
    return {"status": "ok"}

@app.get("/status/{sub_id}")
async def get_status(sub_id: str):
    return {"status": db.get(sub_id, "Not Found")}