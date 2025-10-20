def identify_project_type(project_data):
    """
    Identify whether a project is individual or collaborative
    based on the number of unique contributors detected
    from parsed file metadata.
    """
    contributors = set()

    for file in project_data.get("files", []):
        if "owner" in file and file["owner"]:
            contributors.add(file["owner"])
        for editor in file.get("editors", []):
            contributors.add(editor)

    if len(contributors) > 1:
        return "Collaborative Project"
    elif len(contributors) == 1:
        return "Individual Project"
    else:
        return "Unknown (no contributor data found)"
