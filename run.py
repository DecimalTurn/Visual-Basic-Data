import os
import argparse
import sys
import subprocess
import ghlinguist as ghl
import requests


def main():

    # This function will :
    # Gather a list of GitHub repos from the GitHub API that have "Visual Basic" as their language (sorting by oldest)
    # Clone each repo to a local directory
    # Run the Linguist tool on the repo
    # Output the results to a file

    # Get the list of repos
    repos = search_github_repos("lang:vbnet pushed:<2019-12-07", sort="created", order="asc", per_page=5, page=1)

    if repos is None:
        sys.exit(1)

    if not os.path.exists("repos"):
        os.makedirs("repos")
    os.chdir("repos")

    # Clone each repo
    for repo in repos['items']:
        clone_repo(repo['clone_url'])

    # Print that we are done cloning the repos
    print("Done cloning repos")

    os.chdir("..")

    # Run Linguist on each repo (ie each directory in the repos directory)
    # We need to go through each directory in the repos directory and save the paths to a list
    # We need the folders inside the folder of the name of the author, so the 2nd level of directories

    repos_list = []
    for author in os.listdir("repos"):
        for repo in os.listdir(f"repos/{author}"):
            repos_list.append({"name": f"repos/{author}/{repo}"})

    # Print the list of repos
    print(repos_list)

    with open('results.txt', 'w') as f:
        for repo in repos_list:
            print(f"Running Linguist on {repo['name']}")
            linguist_output = run_linguist(repo['name'])
            print(f"Linguist output: {linguist_output}")
            slug = repo['name'].split('/')[1]+"/"+ repo['name'].split('/')[2]
            f.write(f"Repo: {slug}\n")
            f.write(f"Url: https://github.com/{slug}\n")
            f.write(f"Language: {linguist_output}\n")
            f.write("\n")

    print("Done running Linguist")

    # Output the results to a file


def clone_repo(clone_url):
    
    #Create a directory with the name of the author
    author = clone_url.split('/')[3]
    if not os.path.exists(author):
        os.makedirs(author)
    os.chdir(author)
    
    # Clone the repo if it doesn't exist
    if not os.path.exists(clone_url.split('/')[4].split('.')[0]):
        subprocess.run(["git", "clone", "--depth", "1", clone_url])

    # Go back to the parent directory (repos)
    os.chdir("..")

def run_linguist(repo_name):
    # Run the Linguist tool on the repo
    # subprocess.run(["linguist", repo_name])

    #Use ghlinguist to run linguist on the repo (need to supply the full path not just the name)
    full_path = os.path.abspath(repo_name)
    return ghl.linguist(full_path, True)
    
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