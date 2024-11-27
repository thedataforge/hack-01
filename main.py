from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import requests
import json
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from gpt4all import GPT4All

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

model = GPT4All("ggml-gpt4all-j-v1.3-groovy")  # Local AI model
class CommitWebhook:
    def __init__(self, github_token: str, ngrok_url: str):

        self.ngrok_url = 'https://f399-99-230-198-24.ngrok-free.app'
        self.headers = {
            ...
        }

    def create_webhook(self, repo_id: str = "RayTracing") -> dict:
        """Create a webhook for the specified repository"""
        url = f"https://api.github.com/repositories/{repo_id}/hooks"
        
        webhook_config = {
            "name": "web",
            "active": True,
            "events": ["push"],  # Track push events (commits)
            "config": {
                "url": f"{self.ngrok_url}/webhook/commits",
                "content_type": "json",
                "insecure_ssl": "0"
            }
        }
        
        response = requests.post(url, json=webhook_config, headers=self.headers)
        
        if response.status_code != 201:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"GitHub API error: {response.text}"
            )
        
        return response.json()

class RepoConfig(BaseModel):
    repo_id: str

# Initialize webhook handler
webhook_handler = CommitWebhook(
    github_token=os.getenv("GITHUB_TOKEN"),
    ngrok_url=os.getenv("NGROK_URL")
)

@app.post("/setup-webhook")
async def setup_webhook(config: RepoConfig):
    """Set up webhook for the specified repository"""
    try:
        # Create the webhook
        webhook_data = webhook_handler.create_webhook(config.repo_id)
        
        # Save webhook configuration
        webhook_info = {
            "webhook_id": webhook_data["id"],
            "repository_id": config.repo_id,
            "created_at": datetime.now().isoformat(),
            "webhook_url": webhook_data["config"]["url"],
            "events": webhook_data["events"],
            "github_response": webhook_data
        }
        
        # Save to JSON file
        os.makedirs("webhook_config", exist_ok=True)
        config_file = f"webhook_config/webhook_{config.repo_id}.json"
        
        with open(config_file, 'w') as f:
            json.dump(webhook_info, f, indent=2)
        
        logger.info(f"Webhook created for repository {config.repo_id}")
        return {
            "status": "success",
            "message": "Webhook configured successfully",
            "webhook_id": webhook_data["id"],
            "config_file": config_file
        }
        
    except Exception as e:
        logger.error(f"Error setting up webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_file_content(full_name: str, commit_id: str, file_path: str, headers: dict) -> str:
    """Fetch file content from GitHub"""
    try:
        url = f"https://api.github.com/repos/{full_name}/contents/{file_path}?ref={commit_id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json().get("content", "")
            if content:
                import base64
                return base64.b64decode(content).decode('utf-8')
        return ""
    except Exception as e:
        logger.error(f"Error fetching file content: {str(e)}")
        return ""

async def generate_commit_explanation(commit_data: dict) -> str:
    """Generate explanation of commit changes using commit data"""
    try:
        # Create a clear summary of the changes
        summary = f"""
        Please explain these repository changes in simple English:
        
        Repository: {commit_data['repository']['full_name']}
        Branch: {commit_data['ref'].split('/')[-1]}
        
        Changes:
        - Modified files: {', '.join(commit_data['commits'][0]['modified_files'])}
        - Added files: {', '.join(commit_data['commits'][0]['added_files'])}
        - Removed files: {', '.join(commit_data['commits'][0]['removed_files'])}
        
        Commit Message: {commit_data['commits'][0]['message']}
        Author: {commit_data['commits'][0]['author']['name']}
        
        Please provide a clear explanation of what changes were made and their purpose.
        """
        
        explanation = await model.generate(
            summary,
            max_tokens=500,
            temp=0.7,
            top_k=40,
            top_p=0.9,
            repeat_penalty=1.1
        )
        print(explanation)
        print(model)
        return explanation.strip()
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        return f"Error generating explanation: {str(e)}"

@app.post("/webhook/commits")
async def handle_commits(request: Request):
    """Handle incoming commit webhooks and generate explanations"""
    try:
        # Get webhook payload
        payload = await request.json()
        
        # Extract commit information
        commits = payload.get("commits", [])
        repository = payload.get("repository", {})
        
        # Create commit data
        commit_data = {
            "repository": {
                "id": repository.get("id"),
                "name": repository.get("name"),
                "full_name": repository.get("full_name")
            },
            "ref": payload.get("ref"),
            "commits": [
                {
                    "id": commit.get("id"),
                    "message": commit.get("message"),
                    "timestamp": commit.get("timestamp"),
                    "author": commit.get("author"),
                    "modified_files": commit.get("modified", []),
                    "added_files": commit.get("added", []),
                    "removed_files": commit.get("removed", [])
                }
                for commit in commits
            ],
            "received_at": datetime.now().isoformat()
        }
        
        os.makedirs("commits", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        commit_file = f"commits/commit_data_{timestamp}.json"
        
        with open(commit_file, 'w') as f:
            json.dump(commit_data, f, indent=2)
        
        explanation = await generate_commit_explanation(commit_data)
        print(explanation)
        print('___________')
        
        os.makedirs("commit_explanations", exist_ok=True)
        explanation_file = f"commit_explanations/commit_explanation_{timestamp}.txt"
        
        with open(explanation_file, 'w') as f:
            f.write(f"Repository: {repository.get('full_name')}\n")
            f.write(f"Branch: {commit_data['ref'].split('/')[-1]}\n")
            f.write(f"Commit ID: {commit_data['commits'][0]['id']}\n")
            f.write(f"Author: {commit_data['commits'][0]['author']['name']}\n")
            f.write(f"Timestamp: {commit_data['commits'][0]['timestamp']}\n")
            f.write(f"Modified Files: {', '.join(commit_data['commits'][0]['modified_files'])}\n")
            f.write(f"Added Files: {', '.join(commit_data['commits'][0]['added_files'])}\n")
            f.write(f"Removed Files: {', '.join(commit_data['commits'][0]['removed_files'])}\n")
            f.write(f"Commit Message: {commit_data['commits'][0]['message']}\n")
            f.write("\nExplanation:\n")
            f.write(explanation)
        
        logger.info(f"Generated explanation for commit {commit_data['commits'][0]['id']}")
        
        return {
            "status": "success",
            "message": "Generated commit explanation",
            "commit_data": commit_file,
            "explanation_file": explanation_file
        }
        
    except Exception as e:
        logger.error(f"Error processing commits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/webhook/status/{repo_id}")
async def get_webhook_status(repo_id: str):
    """Get webhook status for a repository"""
    try:
        config_file = f"webhook_config/webhook_{repo_id}.json"
        if not os.path.exists(config_file):
            raise HTTPException(status_code=404, detail="Webhook configuration not found")
            
        with open(config_file, 'r') as f:
            webhook_info = json.load(f)
            
        return {
            "status": "active",
            "webhook_info": webhook_info
        }
        
    except Exception as e:
        logger.error(f"Error getting webhook status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)