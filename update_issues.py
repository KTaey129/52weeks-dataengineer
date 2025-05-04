# update_issues.py
# Script to update existing GitHub issues in 52weeks-dataengineer to use "Enhancing DE skill Roadmap"
# Requirements: pip install requests python-dotenv
# Setup:
# 1. Ensure .env file contains:
#    GITHUB_TOKEN=ghp_YourTokenHere
#    OWNER=KTaey129
#    REPO=52weeks-dataengineer
# 2. Token must have 'repo' scope
# 3. Run: python update_issues.py

import os
import time
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
OWNER = os.getenv('OWNER')
REPO = os.getenv('REPO')

# Validate environment variables
if not all([GITHUB_TOKEN, OWNER, REPO]):
    logger.error("Missing required environment variables: GITHUB_TOKEN, OWNER, or REPO")
    exit(1)

# Headers for GitHub API
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

# Create a requests session
session = requests.Session()

def check_rate_limit(response):
    """Check GitHub API rate limit."""
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    limit = int(response.headers.get('X-RateLimit-Limit', 0))
    if remaining < 50:
        logger.warning(f"Low API rate limit remaining: {remaining}/{limit}")

def get_all_issues():
    """Fetch all issues (open and closed) from the repository."""
    issues = []
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/issues?state=all&per_page=100'
    
    while url:
        try:
            response = session.get(url, headers=HEADERS, timeout=10)
            check_rate_limit(response)
            if not response.ok:
                logger.error(f"Failed to fetch issues: {response.status_code} - {response.text}")
                return []
            issues.extend(response.json())
            url = response.links.get('next', {}).get('url')
            time.sleep(0.5)  # Delay to respect rate limits
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching issues: {str(e)}")
            return []
    
    return issues

def update_issue(issue):
    """Update an issue's title and body if it matches Week XX pattern."""
    issue_number = issue['number']
    title = issue['title']
    
    # Check if issue is a weekly issue (e.g., "Week 01" to "Week 52")
    if not title.startswith("Week ") or not title[5:7].isdigit():
        logger.info(f"Skipping issue #{issue_number}: Not a weekly issue ({title})")
        return
    
    week = int(title[5:7])
    new_title = f"Week {week:02d}"
    new_body = (
        f"📆 **Week {week} - Enhancing DE skill Roadmap**\n\n"
        "- [ ] Organize goals\n"
        "- [ ] Checklist of main tasks\n"
        "- [ ] Record deliverables\n\n"
        "🔁 Weekly completion report due Sunday"
    )
    
    data = {
        "title": new_title,
        "body": new_body
    }
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/issues/{issue_number}'
    
    try:
        response = session.patch(url, json=data, headers=HEADERS, timeout=10)
        check_rate_limit(response)
        if response.ok:
            logger.info(f"Updated issue #{issue_number}: {new_title}")
        else:
            logger.error(f"Failed to update issue #{issue_number}: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while updating issue #{issue_number}: {str(e)}")

def main():
    """Update all weekly issues in the repository."""
    logger.info(f"Fetching issues for {OWNER}/{REPO}")
    issues = get_all_issues()
    
    if not issues:
        logger.warning("No issues found in the repository")
        return
    
    logger.info(f"Found {len(issues)} issues to check")
    for issue in issues:
        update_issue(issue)
        time.sleep(0.5)  # Delay to avoid rate limiting
    
    logger.info("Completed updating issues")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    finally:
        session.close()