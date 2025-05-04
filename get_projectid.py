import os
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
OWNER = os.getenv('OWNER')  # GitHub username or organization

# Validate environment variables
if not all([GITHUB_TOKEN, OWNER]):
    logger.error("Missing GITHUB_TOKEN or OWNER in .env")
    exit(1)

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

def query_projects(is_organization=False):
    """Query GitHub Projects v2 for a user or organization."""
    entity = "organization" if is_organization else "user"
    query = f"""
    query($login: String!) {{
      {entity}(login: $login) {{
        projectsV2(first: 10) {{
          nodes {{
            id
            title
            number
          }}
        }}
      }}
    }}
    """
    variables = {"login": OWNER}
    payload = {"query": query, "variables": variables}
    url = 'https://api.github.com/graphql'

    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        if response.ok:
            data = response.json()
            if 'errors' in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []
            entity_data = data.get('data', {}).get(entity)
            if not entity_data:
                logger.error(f"No {entity} found for login: {OWNER}")
                return []
            projects = entity_data.get('projectsV2', {}).get('nodes', [])
            return projects
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {str(e)}")
        return []

def main():
    """Fetch and display GitHub Projects v2 IDs."""
    logger.info(f"Fetching projects for {OWNER}")

    # Try user query first
    projects = query_projects(is_organization=False)
    if not projects:
        logger.info(f"No user projects found for {OWNER}. Trying organization...")
        projects = query_projects(is_organization=True)

    if projects:
        logger.info(f"Found {len(projects)} projects:")
        for project in projects:
            logger.info(f"Title: {project['title']}, ID: {project['id']}, Number: {project['number']}")
    else:
        logger.warning(f"No projects found for {OWNER}. Please create a Project (v2) at https://github.com/users/{OWNER}/projects")

if __name__ == "__main__":
    main()