# create_board.py
# Script to create 52 weekly GitHub issues for the 52weeks-dataengineer project.
# Security enhancements:
# - Loads sensitive data from .env file using python-dotenv.
# - Validates inputs and handles errors gracefully.
# - Implements rate limiting with delays and checks API rate limits.
# - Uses logging instead of print for safer output.
# - Requires 'repo' scope for the GitHub Personal Access Token (PAT).
#
# Setup:
# 1. Install dependencies: `pip install requests python-dotenv`
# 2. Create a `.env` file in the same directory with:
#    GITHUB_TOKEN=your_github_token_here
#    OWNER=your_username_here
#    REPO=52weeks-dataengineer
#    PROJECT_ID=your_project_id_here
# 3. Ensure `.env` is added to `.gitignore` to prevent committing sensitive data.
# 4. Run the script: `python create_board.py`

import os
import time
import logging
from dotenv import load_dotenv
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
OWNER = os.getenv('OWNER')
REPO = os.getenv('REPO')
PROJECT_ID = os.getenv('PROJECT_ID')  # Projects v2 ID (optional for issues)

# Validate environment variables
if not all([GITHUB_TOKEN, OWNER, REPO]):
    logger.error("Missing required environment variables: GITHUB_TOKEN, OWNER, or REPO")
    exit(1)

# Headers for GitHub API requests
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

# Create a requests session for connection pooling
session = requests.Session()

def check_rate_limit(response):
    """Check GitHub API rate limit from response headers."""
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    limit = int(response.headers.get('X-RateLimit-Limit', 0))
    if remaining < 50:  # Arbitrary threshold to warn user
        logger.warning(f"Low API rate limit remaining: {remaining}/{limit}")

def create_issue(week):
    """Create a GitHub issue for the specified week."""
    title = f"Week {week:02d}"
    body = (
        f"📆 **Week {week} - Toss DE Roadmap**\n\n"
        "- [ ] Organize goals\n"
        "- [ ] Checklist of main tasks\n"
        "- [ ] Record deliverables\n\n"
        "🔁 Weekly completion report due Sunday"
    )
    data = {
        "title": title,
        "body": body
    }
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/issues'
    
    try:
        response = session.post(url, json=data, headers=HEADERS, timeout=10)
        check_rate_limit(response)
        
        if response.ok:
            logger.info(f"Created Issue: Week {week}")
        else:
            logger.error(f"Failed to create issue for Week {week}: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while creating issue for Week {week}: {str(e)}")

def main():
    """Create 52 weekly issues with a delay to respect rate limits."""
    for i in range(1, 53):
        create_issue(i)
        time.sleep(1)  # 1-second delay to avoid rate limiting

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    finally:
        session.close()  # Close the requests session