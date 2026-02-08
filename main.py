import base64
import os
import requests
import uuid
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Platform Engine Code Runner")

class SubmissionRequest(BaseModel):
    code: str
    tests: str
    callback_url: str

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "Sunnycse10/code-runner-engine" 
db = {}

def dispatch_to_github(submission_id: str, code: str, tests: str, callback_url: str):
    url = f"https://api.github.com/repos/{REPO}/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "event_type": "run_submission",
        "client_payload": {
            "submission_id": submission_id,
            "code": code,
            "tests": tests,
            "callback_url": callback_url
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"--- Dispatch for {submission_id}: Status {response.status_code} ---")

@app.post("/submit")
async def submit_code(sub_request: SubmissionRequest, bg: BackgroundTasks):
    sub_id = str(uuid.uuid4())
    db[sub_id] = {"status": "Processing", "result": "In Queue"}
    
    bg.add_task(
        dispatch_to_github, 
        sub_id, sub_request.code, sub_request.tests, sub_request.callback_url
    )
    
    return {"submission_id": sub_id, "message": "Code sent to sandbox."}

@app.post("/callback")
async def receive_result(request: Request):
    data = await request.json()
    sub_id = data.get("submission_id")
    
    encoded_output = data.get("output", "")
    try:
        decoded_output = base64.b64decode(encoded_output).decode("utf-8")
    except Exception:
        decoded_output = "Error decoding output"
    
    db[sub_id] = {
        "status": data.get("status"),
        "result": decoded_output
    }
    return {"status": "received"}

@app.get("/status/{sub_id}")
async def get_status(sub_id: str):
    return db.get(sub_id, {"error": "Not found"})