import json
import os
import argparse
import sys
import subprocess
import ghlinguist as ghl
import requests
from datetime import datetime, timedelta
import requests

counter_limit = 15

def main():

    # This function will :
    # Gather a list of GitHub repos from the GitHub API that have "Visual Basic" as their language (sorting by oldest)
    # Clone each repo to a local directory
    # Run the Linguist tool on the repo
    # Output the results to a file

    # Read the file and store the repos in a list
    repos = []
    with open('repos.txt') as file:
        repos = file.readlines()

    if not os.path.exists("repos"):
        os.makedirs("repos")

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

    return

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


def create_repo_list(start_date, end_date):

    repos_content = ""

    current_date = start_date
    current_year = get_year(current_date)

    # Read the file once and store its contents
    with open(f"data/{current_year}.csv") as file:
        repos_content = file.read()

    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")

    # Loop over the start date to the end date
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
    current_date_dt = start_date_dt

    problem_encountered = False
    counter = 0
    while current_date_dt >= end_date_dt:
        
        print(f"Fetching repos for date: {current_date}")

        counter += 1

        if counter == counter_limit:
            print("Reached the maximum number of days for testing")
            break

        page = 1
        while True:
            repos = search_github_repos(f"lang:vbnet pushed:{current_date}", sort="updated", order="asc", per_page=100, page=page)

            #Debuggin: Write the response to a file by converting it to a json string
            # with open('repos.json', 'a') as f:
                # json_str = json.dumps(repos, indent=4)
                # f.write(json_str)
       
            if repos is None or not repos['items']:
                break

            if page > 10:
                print("Reached the maximum number of pages")
                exit(1)

            linguist_version = subprocess.run(["github-linguist", "--version"], capture_output=True).stdout.decode('utf-8').strip()
            date_now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

            # Add the repos to a file
            with open(f'data/{get_year(current_date)}.csv', 'a') as f:
                for repo in repos['items']:
                    # Check if the repo is already in the file
                    slug = repo['clone_url'].split('/')[3]+"/"+ repo['clone_url'].split('/')[4].split('.')[0]
                    if slug not in repos_content:

                        latest_commit_date = get_latest_commit_date(slug)

                        if latest_commit_date is None:
                            latest_commit_date = "Unknown (repo deleted or no commits)"
                        
                        lang = None
                        if latest_commit_date == "Unknown (repo deleted or no commits)":
                            lang = "N/A"
                        else:
                            lang = get_language(slug)


                        if lang is None:
                            print(f"Failed to determine the language of repo {slug}")
                            problem_encountered = True
                            break

                        # Each line has 5 columns. Create an empty array of 5 elements
                        line = [""] * 5
                        line[0] = slug
                        line[1] = latest_commit_date
                        if latest_commit_date != "Unknown (repo deleted or no commits)":
                            line[2] = lang
                            line[3] = linguist_version
                            line[4] = date_now

                        # Join the line back together, replacing None with an empty string
                        new_line = ",".join("" if item is None else str(item) for item in line) 
                        if new_line[-1] != "\n":
                            new_line += "\n"
                        f.write(new_line)
                    else:
                        print(f"Repo {slug} already analyzed")

            if problem_encountered:
                # Break out of the searching loop for that day
                break
            
            page += 1

        if problem_encountered:
            break

        # Increment the date by one day
        current_date_dt -= timedelta(days=1)
        current_date = current_date_dt.strftime("%Y-%m-%d")
    
    if problem_encountered:
        print("Problem encountered. We'll have to resume at the current date")
        return current_date_dt.strftime("%Y-%m-%d")
    
    # Move on to the next day (for the next run)
    current_date_dt -= timedelta(days=1)
    return current_date_dt.strftime("%Y-%m-%d")
        

def get_year(date):
    return date.split('-')[0]

def fill_missing_data_in_csv1():
    # The repos.csv file is missing some data, so we need to fill it in
    # Read the file once and store its contents
    repos_content = ""
    with open('repos.csv') as file:
        repos_content = file.readlines()

    linguist_version = subprocess.run(["github-linguist", "--version"], capture_output=True).stdout.decode('utf-8').strip()
    language_determination_date = subprocess.run(["date"], capture_output=True).stdout.decode('utf-8').strip()

    # If the language column (column 3) is missing, we need to add it
    counter = 0
    new_repos_content = []
    for repo in repos_content:
        counter += 1
        if counter == counter_limit:
            print("Reached the maximum number of repos for testing")

        if len(repo.split(',')[2]) == 0 and counter < counter_limit :
            # Run Linguist on the repo
            print(f"Running Linguist on {repo.split(',')[0]}")

            # Check if the repo is already cloned
            if not os.path.exists("repos/"+repo.split(',')[0]):
                cloning_status = clone_repo_from_slug(repo.split(',')[0])

            linguist_output = run_linguist("repos/"+repo.split(',')[0])

            # Add the language to the repo line in the csv
            line = repo.split(',')
            line[0] = line[0].strip()
            line[1] = line[1].strip()
            line[2] = linguist_output
            line[3] = linguist_version
            line[4] = convert_date_format(language_determination_date)

            # Join the line back together, replacing None with an empty string
            repo = ",".join("" if item is None else str(item) for item in line)
        
            #Add a new line character if it's not already the last character in repo
            if repo[-1] != "\n":
                repo += "\n"

        #else:
            # If the language is already determined, just print it
            #print(f"Repo {repo.split(',')[0]} already has a language determined")
        
        new_repos_content.append(repo)


    # Write the updated repos_content to the file
    with open('repos.csv', 'w') as file:
        file.write("".join(new_repos_content))

def get_language(slug):
    #Check if the repo is already cloned
    if not os.path.exists("repos/"+slug):
        cloning_status = clone_repo_from_slug(slug)

        if cloning_status == "Failed":
            return None

    return run_linguist("repos/"+slug)

def convert_date_format(date_str):
    """
    Convert a date from 'Sat Sep 28 21:47:10 UTC 2024' format to '2015-07-21T16:39:25Z' format.

    Parameters:
    date_str (str): The date string in the format 'Sat Sep 28 21:47:10 UTC 2024'.

    Returns:
    str: The date string in ISO 8601 format '2015-07-21T16:39:25Z'.
    """
    # Parse the input date string to a datetime object
    dt = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Z %Y")
    # Convert the datetime object to the desired format
    iso_format_date = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return iso_format_date

def fill_missing_data_in_csv2():
    # The repos.csv file is missing some data, so we need to fill it in
    # Read the file once and store its contents
    repos_content = ""
    with open('repos.csv') as file:
        repos_content = file.readlines()

    linguist_version = subprocess.run(["github-linguist", "--version"], capture_output=True).stdout.decode('utf-8').strip()
    language_determination_date = subprocess.run(["date"], capture_output=True).stdout.decode('utf-8').strip()

    # If the language column (column 3) is missing, we need to add it
    counter = 0

    new_repos_content = []
    for repo in repos_content:
        counter += 1
        if counter == counter_limit:
            print("Reached the maximum number of repos for testing")

        if len(repo.split(',')[1]) == 0 and counter < counter_limit :

            # Get the last commit date of the repo
            slug = repo.split(',')[0]
            last_commit_date = get_latest_commit_date(slug)

            # Add the language to the repo line in the csv
            line = repo.split(',')
            line[1] = last_commit_date

            # Join the line back together, replacing None with an empty string
            repo = ",".join("" if item is None else str(item) for item in line)

            #Add a new line character if it's not already the last character in repo
            if repo[-1] != "\n":
                repo += "\n"
        
        #else:
            # If the language is already determined, just print it
            #print(f"Repo {repo.split(',')[0]} already has a language determined")
        
        new_repos_content.append(repo)


    # Write the updated repos_content to the file
    with open('repos.csv', 'w') as file:
        file.write("".join(new_repos_content))
            

def clone_repo(clone_url):
    clone_repo_from_slug(url_to_slug(clone_url))

def clone_repo_from_slug(slug):

    # Check if we are in the repos directory
    if os.path.basename(os.getcwd()) != "repos":
        if not os.path.exists("repos"):
            os.makedirs("repos")
        os.chdir("repos")

    #Create a directory with the name of the author
    author = slug.split('/')[0]
    repo_name = slug.split('/')[1]
    if not os.path.exists(author):
        os.makedirs(author)
    os.chdir(author)
    
    status = ""

    # Clone the repo if it doesn't exist
    if not os.path.exists(repo_name):
        try:
            subprocess.run(["git", "clone", "--depth", "1", slug_to_url(slug)])
            status = "Success"
        except:
            print(f"Failed to clone repo {slug}")
            status = "Failed"

    # Go back to the parent directory (repos)
    os.chdir("..")

    # Go back to the parent directory (main directory)
    os.chdir("..")

    return status

def url_to_slug(url):
    return url.split('/')[3]+"/"+ url.split('/')[4].split('.')[0]

def slug_to_url(slug):
    return "https://github.com/"+slug

def run_linguist(repo_name):
    # Run the Linguist tool on the repo
    # subprocess.run(["linguist", repo_name])

    #Use ghlinguist to run linguist on the repo (need to supply the full path not just the name)
    full_path = os.path.abspath(repo_name)
    return ghl.linguist(full_path, True)
    
def search_github_repos(query, sort='updated', order='asc', per_page=10, page=1):
    token = os.getenv('GITHUB_TOKEN')

    # if not token:
    #     print("GITHUB_TOKEN is not set")
    # else:
    #     print(f"GITHUB_TOKEN is set: {token[:4]}...")

    url = f"https://api.github.com/search/repositories"
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}'
        }
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
        print(f"Url: {url}")
        print(response.json())
        return None

def get_latest_commit_date(repo_slug):
    """
    Get the latest commit date for a given repository slug (e.g., 'owner/repo').

    Parameters:
    repo_slug (str): The repository slug in the format 'owner/repo'.

    Returns:
    str: The latest commit date in ISO 8601 format, or 'Unknown' if the request fails.
    """
    token = os.getenv('GITHUB_TOKEN')
    url = f"https://api.github.com/repos/{repo_slug}/commits"

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}'
        }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        latest_commit_date = response.json()[0]['commit']['author']['date']
        return latest_commit_date
    elif response.status_code == 404:
        print(f"Repo {repo_slug} has no commits or was deleted")
        return None
    else:
        print(f"Failed to get the latest commit date for {repo_slug}")
        print(response.json())
        exit(1)

if __name__ == "__main__":
    
    span = 1

    # Read the start date from date.txt
    start_date = ""
    with open('date.txt') as file:
        start_date = file.readline().strip()

    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_dt = start_date_dt - timedelta(days=span)
    end_date = end_date_dt.strftime("%Y-%m-%d")

    current_date = create_repo_list(start_date, end_date)

    # Update the date in date.txt
    with open('date.txt', 'w') as file:
        file.write(current_date)
    