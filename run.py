import json
import os
import argparse
import sys
import subprocess
import ghlinguist as ghl
import requests
from datetime import datetime, timedelta
import requests
import traceback
import errno

# My scripts:
import chart

new_data = False
counter_limit = 15
retries_limit = 8

def create_repo_list(start_date, end_date):
    
    global new_data
    repos_content = ""

    current_date = start_date

    # Read the file once and store its contents
    with open(f"data/data.csv") as file:
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

            #Debugging: Write the response to a file by converting it to a json string
            # with open('repos.json', 'a') as f:
                # json_str = json.dumps(repos, indent=4)
                # f.write(json_str)
       
            if repos is None:
                print("Failed to fetch repos")
                problem_encountered = True
                break

            if not repos['items']:
                print(f"No more repos for this date: {current_date}")
                break

            if page > 10:
                print("Reached the maximum number of pages")
                exit(1)

            linguist_version = subprocess.run(["bundle", "exec", "github-linguist", "--version"], capture_output=True).stdout.decode('utf-8').strip()
            date_now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

            # Add the repos to a file
            with open(f'data/data.csv', 'a') as f:
                for repo in repos['items']:
                    # Check if the repo is already in the file
                    slug = repo['clone_url'].split('/')[3]+"/"+ repo['clone_url'].split('/')[4].split('.')[0]
                    if slug not in repos_content:

                        latest_commit_date = get_latest_commit_date(slug)

                        if latest_commit_date is None:
                            latest_commit_date = "Unknown (repo deleted or no commits)"
                        
                        lang = None
                        if latest_commit_date == "Unknown (repo deleted or no commits)":
                            lang = "Unknown"
                        else:
                            print(f"Analyzing {slug}")
                            lang = get_language(slug)

                        if lang is None:
                            print(f"Failed to determine the language of repo {slug}")
                            problem_encountered = True
                            break
                            
                        print(f"    Output: {lang}")

                        # Each line has 5 columns. Create an empty array of 5 elements
                        line = [""] * 5
                        line[0] = slug
                        line[1] = latest_commit_date
                        line[2] = lang
                        line[3] = linguist_version
                        line[4] = date_now

                        # Join the line back together, replacing None with an empty string
                        new_line = ",".join("" if item is None else str(item) for item in line) 
                        if new_line[-1] != "\n":
                            new_line += "\n"
                        f.write(new_line)
                        new_data = True

                    else:
                        print(f"Repo {slug} already analyzed")

            if problem_encountered:
                # Break out of the searching loop for that day
                break

            if len(repos['items']) < 100:
                print(f"No more repos for this date: {current_date}")
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
    # Since the loop decrements the date, we don't need to decrement it further
    return current_date_dt.strftime("%Y-%m-%d")
        
def get_language(slug):
    #Check if the repo is already cloned
    if not os.path.exists("repos/"+slug):
        cloning_status = clone_repo_from_slug(slug)

        if cloning_status == "Failed":
            return None

    return run_linguist("repos/"+slug)

def clone_repo(clone_url):
    clone_repo_from_slug(url_to_slug(clone_url))

def clone_repo_from_slug(slug):
    # Check if we are in the repos directory
    if os.path.basename(os.getcwd()) != "repos":
        if not os.path.exists("repos"):
            os.makedirs("repos")
        os.chdir("repos")

    # Create a directory with the name of the author
    author, repo_name = slug.split('/')
    if not os.path.exists(author):
        os.makedirs(author)
    os.chdir(author)

    status = ""

    # Clone the repo if it doesn't exist
    if not os.path.exists(repo_name):
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", slug_to_url(slug)],
                check=True
            )
            status = "Success"
        except subprocess.CalledProcessError as e:
            print(f"Command '{e.cmd}' failed with exit status {e.returncode}.")
            print(f"Error output:\n{e.stderr}")
            status = "Failed"
        except OSError as e:
            print(f"OSError [Errno {e.errno}]: {e.strerror}")
            print(f"File/Command: {e.filename}")
            if e.errno == errno.EACCES:
                print(f"Permission denied while accessing '{repo_name}'.")
            elif e.errno == errno.ENOSPC:
                print("No space left on the device.")
            elif e.errno == errno.ENOENT:
                print(f"Command not found: '{e.filename}'.")
            else:
                print("An unexpected OS error occurred.")
            status = "Failed"
        except Exception as e:
            print(f"Failed to clone repo {slug}.")
            print(f"Error: {e}")
            print("Traceback:")
            traceback.print_exc()
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

# Run the Linguist tool on the repo
def run_linguist(repo_name):

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
        print(f"Page: {page}")
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
    elif response.status_code == 409:
        print(f"Repo {repo_slug} is empty")
        return None
    else:
        print(f"Failed to get the latest commit date for {repo_slug}")
        print(response.json())
        exit(1)

def create_github_issue(slug, title, body, labels=None):

    token = os.getenv('GITHUB_TOKEN')

    url = f"https://api.github.com/repos/{slug}/issues"
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}'
    }
    data = {
        'title': title,
        'body': body,
        'labels': labels if labels else []  # Use the provided labels or an empty list if none are given
    }
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"🟢 Issue created successfully: {response.json()['html_url']}")
        return response.json()['number']
    else:
        print(f"🔴 Failed to create issue. Status code: {response.status_code}")
        print(response.json())

def update_chart():
    # Update the chart
    chart.main()

if __name__ == "__main__":

    # If the disable.txt file exists and contains the word "True", exit the program
    if os.path.exists("disable.txt"):
        with open('disable.txt') as file:
            if file.readline().strip() == "True":
                print("The program is disabled. Exiting")
                exit(0)

    # Span days to look at (0 means only one day)
    span = 2  # Change span to 1 to look at 2 days at a time

    # Read the start date from date.txt
    start_date = ""
    with open('date.txt') as file:
        start_date = file.readline().strip()

    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_dt = start_date_dt - timedelta(days=span)
    end_date = end_date_dt.strftime("%Y-%m-%d")

    next_start_date = create_repo_list(start_date, end_date)

    if next_start_date != start_date:
        # Update the date in date.txt
        with open('date.txt', 'w') as file:
            print(f"Updating the next start date to {next_start_date}")
            file.write(next_start_date)
        
        # Update retries count in retries.txt
        with open('retries.txt', 'w') as file:
            file.write("0")

        update_chart()

    elif new_data == False:
        print("No new data was added. Exiting")

        # Increase the retries count in retries.txt
        retries = 0
        with open('retries.txt', 'r+') as file:
            retries = int(file.readline().strip())
            print(f"This was retry number {retries}")
            retries += 1
            file.seek(0)
            file.write(str(retries))
            file.truncate()
        
        if retries == retries_limit:
            print("Retries exceeded. Disabling the program")
            with open('disable.txt', 'w') as file:
                file.write("True")
            create_github_issue(os.getenv('GITHUB_REPOSITORY'), "Issue with the data collection", "No new data was added", ["bug"])
            exit(0)
        
        exit(0)

    else:
        print("New data was added, but we didn't process all the data for that day. Exiting")
        exit(0)


