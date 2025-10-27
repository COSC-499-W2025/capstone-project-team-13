def sniff_supertype(file_path: str) -> str:
    """
    Classify file content into one of:
        "code"  - any structured code/markup/config (py/js/html/json/yaml/sql etc)
        "media" - any binary file (pdf, zip, image, video, docx, etc)
        "text"  - human-readable plain text (no code-like patterns)
    """

    with open(file_path, "rb") as f:
        chunk = f.read(8192)

    # --- BINARY check = MEDIA ---
    if b"\x00" in chunk:            # fast binary signature
        return "media"

    # decode best-effort
    text = chunk.decode("utf-8", errors="ignore").lower()

    # --- CODE detection patterns ---
    code_markers = (
        # typical programming
        "def ", "class ", "import ", "#include", "fn ", "public ", "function ",
        # markup/config
        "<html", "<!doctype", "<?xml", "{", "[", "---", "apiVersion:", "version:",
        # common structured file types
        "select ", "insert ", "update ", "from ", "var ", "let ", "const ",
    )

    if any(marker in text for marker in code_markers):
        return "code"

    # --- Everything decoded & not code => plain text ---
    return "text"
