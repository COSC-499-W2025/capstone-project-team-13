def identify_project_type(file_metadata):
    contributors = file_metadata.get("contributors", [])
    if len(contributors) > 1:
        return "Collaborative Project"
    elif len(contributors) == 1:
        return "Individual Project"
    else:
        return "Unknown"
