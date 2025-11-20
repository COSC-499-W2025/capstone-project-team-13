from git import Repo
def identify_project_type(project_path, project_data):
    """
    Identify whether a project is individual or collaborative
    based on the number of unique contributors detected
    from parsed file metadata.
    """
    contributors = set()

#Scan through parsed file metadata
    for file in project_data.get("files", []):
        if "owner" in file and file["owner"]:
            contributors.add(file["owner"])
        for editor in file.get("editors", []):
            contributors.add(editor)

  # 2. From Git commit history (if repo exists)
    try:
        repo = Repo(project_path)
        for commit in repo.iter_commits():
            if commit.author and commit.author.email:
                contributors.add(commit.author.email)
    except Exception as e:
        print("Git analysis skipped:", e)



#Classify
    if len(contributors) > 1:
        return "Collaborative Project"
    elif len(contributors) == 1:
        return "Individual Project"
    else:
        return "Unknown (no contributor data found)"
