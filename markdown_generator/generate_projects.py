import os
import requests
import yaml

# --- Configuration ---
# Load the configuration file to get the GitHub username
try:
    with open('../_config.yml', 'r') as f:
        config = yaml.safe_load(f)
        GITHUB_USERNAME = config.get('author', {}).get('github')
        if not GITHUB_USERNAME:
            raise ValueError("GitHub username not found in _config.yml under author.github")
except FileNotFoundError:
    print("Error: _config.yml not found. Please ensure the script is run from the 'markdown_generator' directory.")
    exit()
except Exception as e:
    print(f"Error reading _config.yml: {e}")
    exit()

REPOS_TO_SKIP = [
    'rahmat-ml.github.io' 
]
PROJECTS_DIR = '../_projects'

# --- Main Script ---

def get_github_repos(username):
    """Fetches public repositories for a given GitHub user or organization."""
    # Use the 'orgs' endpoint for organizations
    api_url = f'https://api.github.com/orgs/{username}/repos'
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raises an exception for 4XX or 5XX status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        # If the org endpoint fails, try the user endpoint as a fallback
        print(f"Could not fetch from organization endpoint: {e}. Trying user endpoint...")
        api_url = f'https://api.github.com/users/{username}/repos'
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as user_e:
            print(f"Error fetching repositories from user endpoint as well: {user_e}")
            return None

def create_project_files(repos):
    """Creates markdown files for each repository."""
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)
        print(f"Created directory: {PROJECTS_DIR}")

    for repo in repos:
        repo_name = repo.get('name')
        
        # Skip this repository if it's in the skip list
        if repo_name in REPOS_TO_SKIP:
            print(f"Skipping repository: {repo_name}")
            continue

        description = repo.get('description', 'No description provided.')
        url = repo.get('html_url')
        tags = repo.get('topics', [])
        
        # Create a URL-friendly slug for the filename and permalink
        slug = repo_name.lower().replace(' ', '-')
        
        # Define the path for the new markdown file
        file_path = os.path.join(PROJECTS_DIR, f'{slug}.md')
        
        # --- Build the file content ---
        # Start with the basic front matter
        file_content_parts = [
            "---",
            f'title: "{repo_name}"',
            f'excerpt: "{description}"',
            "collection: projects",
        ]

        # Add tags only if they exist
        if tags:
            file_content_parts.append("tags:")
            for tag in tags:
                file_content_parts.append(f"  - {tag}")

        # Add the rest of the front matter and content
        file_content_parts.extend([
            f"permalink: /projects/{slug}",
            "---",
            "",
            "This project is available on GitHub.",
            "",
            f"[View on GitHub]({url})",
        ])

        file_content = "\n".join(file_content_parts)
        # --- End of building file content ---
        
        # Write the content to the file
        with open(file_path, 'w') as f:
            f.write(file_content)
        
        print(f"Successfully created project file for: {repo_name}")

if __name__ == '__main__':
    print(f"Fetching repositories for: {GITHUB_USERNAME}...")
    repos = get_github_repos(GITHUB_USERNAME)
    if repos:
        # Filter out forked repositories
        original_repos = [repo for repo in repos if not repo['fork']]
        print(f"Found {len(original_repos)} original repositories. Generating project files...")
        create_project_files(original_repos)
        print("\nProject file generation complete.")
    else:
        print("Could not fetch repositories. Aborting.")

