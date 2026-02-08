# Python Code Runner (Sandbox)
I was designing a problem-solving platform and needed a safe way to execute untrusted user code without risking the core system or cloud account.
So I developed this solution.

## How it works
1. **API (FastAPI)**: Receives the code and a callback URL.
2. **Task Queue**: Since running code takes time, the API dispatches the job to GitHub Actions and returns a `submission_id` immediately so the user isn't hanging.
3. **Sandbox (Docker + GitHub Actions)**:
   - The job runs on a fresh GitHub runner (VM).
   - Inside that VM, the code is wrapped in a **Docker container**.
   - I used specific flags to lock it down: `--network none` (no internet), `--memory 128m` (RAM limit), and `--cpus 0.5` (CPU limit).
4. **Callback**: Once the code finishes (or hits a 5s timeout), the output is Base64 encoded and sent back to my local server via a webhook.



## Why this approach?
* **Security**: Even if someone submits `os.system('rm -rf /')`, they only delete files inside the temporary Docker container, not the host runner.
* **Cost/Scale**: Using GitHub Actions means I don't need a massive server running 24/7. It scales up only when code is submitted.
* **Real-time**: Using **ngrok** allows the cloud runner to talk back to my local environment during development.



## Testing it locally
1. **Install dependencies**: 
   `pip install fastapi uvicorn requests python-dotenv`
2. **Setup environment**: 
   Create a `.env` file with your `GITHUB_TOKEN`.
3. **Start the server**: 
   `uvicorn main:app --reload`
4. **Use Swagger**: 
   Go to `/docs` to send a POST request to the `/submit` endpoint.

**Note on logs**: When you check the status, you might see Docker "Pulling" logs in the result. This happens on the first run of a fresh runner because it has to download the `python:3.10-slim` image before it can execute the code.
