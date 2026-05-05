from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os

# Initialize the FastAPI application
app = FastAPI(
    title="Cosmic IT Backend",
    description="Serverless API Router for AI Automations",
    version="1.0.0"
)

# Enable CORS so your React frontend (hosted on GitHub pages) can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Security note: Change this to your actual GitHub Pages URL later!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the expected incoming data from the React frontend
class VideoRequest(BaseModel):
    topic: str
    style: str = "faceless"
    client_email: str

async def trigger_github_action(payload: dict):
    """
    Sends a 'repository_dispatch' webhook to GitHub to wake up the Action Runner.
    """
    # These will be set securely in your Render.com environment variables
    github_token = os.getenv("GITHUB_PAT") # Personal Access Token
    repo_owner = os.getenv("GITHUB_OWNER") # Your GitHub Username
    repo_name = os.getenv("GITHUB_REPO")   # Your Repo Name
    
    if not all([github_token, repo_owner, repo_name]):
        print("Warning: GitHub credentials not configured. Skipping trigger.")
        return

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}",
    }
    
    data = {
        "event_type": "generate_omnistream_video",
        "client_payload": payload
    }

    # Asynchronously trigger the heavy compute engine
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        if response.status_code != 204:
            print(f"Failed to trigger GitHub Action: {response.text}")

@app.post("/api/omnistream/generate")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """
    The endpoint your React frontend calls.
    It responds instantly so the frontend doesn't hang, and triggers GitHub in the background.
    """
    
    # 1. Prepare the data to send to GitHub
    payload = {
        "topic": request.topic,
        "style": request.style,
        "client_email": request.client_email
    }
    
    # 2. Tell FastAPI to trigger the GitHub action in the background
    background_tasks.add_task(trigger_github_action, payload)
    
    # 3. Immediately return success to the React frontend
    return {
        "status": "success",
        "message": "Engine ignited. OmniStream AI is now generating your video on a serverless compute node.",
        "queued_topic": request.topic
    }

@app.get("/")
async def health_check():
    """Simple endpoint to verify the API is awake (useful for Render free tier)."""
    return {"status": "online", "architecture": "serverless"}