# link_issues_to_project.py
# Script to link all issues in KTaey129/52weeks-dataengineer to a GitHub Project (v2)
# Requirements: pip install requests python-dotenv
# Setup:
# 1. Ensure .env file contains:
#    GITHUB_TOKEN=github_pat_YourTokenHere
#    OWNER=KTaey129
#    REPO=52weeks-dataengineer
#    PROJECT_ID=PVT_YourProjectIdHere
# 2. Token: Fine-grained PAT with Issues and Projects read/write permissions
# 3. Run: python link_issues_to_project.py

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
PROJECT_ID = os.getenv('PROJECT_ID')

# Validate environment variables
if not all([GITHUB_TOKEN, OWNER, REPO, PROJECT_ID]):
    logger.error("Missing required environment variables: GITHUB_TOKEN, OWNER, REPO, or PROJECT_ID")
    exit(1)
if not PROJECT_ID.startswith('PVT_'):
    logger.error("Invalid PROJECT_ID format: Must start with 'PVT_'")
    exit(1)

# Headers for GitHub APIs
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',  # Use 'token' for REST, fine-grained PAT
    'Accept': 'application/vnd.github+json'
}
GRAPHQL_HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',  # Use 'Bearer' for GraphQL
    'Content-Type': 'application/json',
    'Accept': 'application/vnd.github+json'
}

def check_rate_limit(response):
    """Check GitHub API rate limit."""
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    limit = int(response.headers.get('X-RateLimit-Limit', 0))
    if remaining < 50:
        logger.warning(f"Low API rate limit remaining: {remaining}/{limit}")

def get_issue_node_ids():
    """Fetch node IDs of all issues (excluding pull requests) with pagination."""
    issues = []
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/issues?state=all&per_page=100'
    
    while url:
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            check_rate_limit(response)
            if not response.ok:
                logger.error(f"Failed to fetch issues: {response.status_code} - {response.text}")
                return []
            data = response.json()
            if not isinstance(data, list):
                logger.error(f"Unexpected API response: {data}")
                return []
            issues.extend([issue for issue in data if 'pull_request' not in issue])
            url = response.links.get('next', {}).get('url')
            time.sleep(0.5)  # Delay to respect rate limits
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching issues: {str(e)}")
            return []
    
    return [(issue['number'], issue['node_id']) for issue in issues]

def link_issue_to_project(node_id, issue_number):
    """Link an issue to a GitHub Project (v2) using GraphQL."""
    query = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item {
          id
        }
      }
    }
    """
    variables = {
        "projectId": PROJECT_ID,
        "contentId": node_id
    }
    payload = {
        "query": query,
        "variables": variables
    }
    try:
        response = requests.post("https://api.github.com/graphql", json=payload, headers=GRAPHQL_HEADERS, timeout=10)
        check_rate_limit(response)
        if response.ok:
            data = response.json()
            if 'errors' in data:
                logger.error(f"Failed to link issue #{issue_number}: {data['errors']}")
                return response.status_code, data
            logger.info(f"Linked issue #{issue_number} to project {PROJECT_ID}")
            return response.status_code, data
        else:
            logger.error(f"Failed to link issue #{issue_number}: {response.status_code} - {response.text}")
            return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while linking issue #{issue_number}: {str(e)}")
        return None, {'error': str(e)}

def main():
    """Link all issues to the specified project."""
    logger.info(f"Fetching issues for {OWNER}/{REPO}")
    issues = get_issue_node_ids()
    
    if not issues:
        logger.warning("No issues found in the repository")
        return
    
    logger.info(f"Found {len(issues)} issues to link")
    for number, node_id in issues:
        status, resp = link_issue_to_project(node_id, number)
        logger.info(f"Linked issue #{number}: Status {status}, Response: {resp}")
        time.sleep(1.5)  # Avoid rate limit

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")