import base64
import os
import requests
import uuid
from fastapi import FastAPI, BackgroundTasks, Request


app = FastAPI(title="Platform Engine Code Runner")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "Sunnycse10/code-runner-engine" 

db = {}

def dispatch_to_github(submission_id: str, code: str, tests: str, callback_url: str):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
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
    requests.post(url, json=payload, headers=headers)

@app.post("/submit")
async def submit_code(request: Request, bg: BackgroundTasks):
    data = await request.json()
    sub_id = str(uuid.uuid4())
    
    # Track the submission
    db[sub_id] = {"status": "Processing", "result": None}
    
    # Dispatch the "work" to GitHub in the background
    bg.add_task(
        dispatch_to_github, 
        sub_id, data['code'], data['tests'], data['callback_url']
    )
    
    return {"submission_id": sub_id, "message": "Code sent to sandbox."}

@app.post("/callback")
async def receive_result(request: Request):
    data = await request.json()
    sub_id = data.get("submission_id")
    
    # Decode the Base64 output from the sandbox
    encoded_output = data.get("output", "")
    decoded_output = base64.b64decode(encoded_output).decode("utf-8")
    
    db[sub_id] = {
        "status": data.get("status"),
        "result": decoded_output
    }
    return {"status": "received"}

@app.get("/status/{sub_id}")
async def get_status(sub_id: str):
    return db.get(sub_id, {"error": "Not found"})