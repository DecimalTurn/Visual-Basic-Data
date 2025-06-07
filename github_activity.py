# There is a file at the root of the current repo named Last_activity.txt
# It contains a date in the format yyyy-mm-dd
# We want to replace the content of that file with the current date and use git to commit that file and push it to origin

import datetime
import subprocess
import sys

def update_last_activity_file():
    # Step 1: Write current date to Last_activity.txt
    today = datetime.date.today().isoformat()
    try:
        with open("Last_activity.txt", "w") as f:
            f.write(today + "\n")
        print(f"Updated Last_activity.txt with date: {today}")
    except Exception as e:
        print(f"Failed to write to file: {e}")
        sys.exit(1)

def git_commit_and_push():
    try:
        subprocess.run(["git", "add", "Last_activity.txt"], check=True)
        subprocess.run(["git", "commit", "-m", "Update Last_activity.txt with current date"], check=True)
        subprocess.run(["git", "push", "origin"], check=True)
        print("Changes pushed to origin successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_last_activity_file()
    git_commit_and_push()
