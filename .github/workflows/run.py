import os
import argparse
import sys
import subprocess
import ghlinguist as ghl


def main():

    # This function will :
    # Gather a list of GitHub repos from the GitHub API that have "Visual Basic" as their language (sorting by oldest)
    # Clone each repo to a local directory
    # Run the Linguist tool on the repo
    # Output the results to a file

    # Get the list of repos
    repos = search_github_repos('language:"Visual Basic"', sort="created", order="asc", per_page=5, page=1)

    if repos is None:
        sys.exit(1)

    # Clone each repo
    for repo in repos['items']:
        clone_repo(repo['clone_url'])

    # Run Linguist on each repo
    for repo in repos['items']:
        run_linguist(repo['name'])

    # Output the results to a file
    with open('results.txt', 'w') as f:
        for repo in repos['items']:
            f.write(f"Repo: {repo['name']}\n")
            f.write(f"Language: {repo['language']}\n")
            f.write(f"URL: {repo['html_url']}\n")
            f.write("\n")

def clone_repo(clone_url):
    # Clone the repo to a local directory
    subprocess.run(["git", "clone", clone_url])

def run_linguist(repo_name):
    # Run the Linguist tool on the repo
    # subprocess.run(["linguist", repo_name])

    #Use ghlinguist to run linguist on the repo
    return ghl.linguist(repo_name)
    
def search_github_repos(query, sort='updated', order='asc', per_page=10, page=1):
    url = f"https://api.github.com/search/repositories"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    params = {
        'q': query,
        'sort': sort,
        'order': order,
        'per_page': per_page,
        'page': page
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data from GitHub API. Status code: {response.status_code}")
        return None

if __name__ == "__main__":
    main()