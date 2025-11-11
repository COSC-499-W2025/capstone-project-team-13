EXT_SUPERTYPES = {
    # --- code ---
    ".py": "code", ".js": "code", ".ts": "code", ".java": "code",
    ".cpp": "code", ".c": "code", ".rb": "code", ".php": "code",
    ".go": "code", ".rs": "code", ".cs": "code", ".swift": "code",
    ".html": "code", ".css": "code",
    
    # --- text / markup ---
    ".txt": "text", ".md": "text", ".xml": "text", ".pdf": "text", ".doc": "text", ".docx": "text",


   # --- media: raster images ---
    ".png": "media", ".jpg": "media", ".jpeg": "media", ".gif": "media", 
    ".bmp": "media", ".tiff": "media", ".tif": "media", ".webp": "media", ".ico": "media",
    
    # --- media: RAW image formats ---
    ".raw": "media", ".cr2": "media", ".nef": "media", ".arw": "media", 
    ".dng": "media", ".orf": "media", ".rw2": "media",

    # --- media: design files ---
    ".psd": "media", ".psb": "media", ".xcf": "media", ".afphoto": "media",
    
    # --- media: vector graphics ---
    ".ai": "media", ".svg": "media", ".eps": "media", ".cdr": "media",
    
    # --- media: UI/UX design ---
    ".fig": "media", ".sketch": "media", ".xd": "media",
    
    # --- media: 3D modeling ---
    ".blend": "media", ".obj": "media", ".fbx": "media", ".max": "media", 
    ".ma": "media", ".mb": "media", ".c4d": "media", ".3ds": "media", ".stl": "media",
    
    # --- media: video files ---
    ".mp4": "media", ".mov": "media", ".avi": "media", ".mkv": "media", 
    ".webm": "media", ".flv": "media", ".wmv": "media", ".m4v": "media", 
    ".mpg": "media", ".mpeg": "media",
    
    # --- media: video project files ---
    ".aep": "media", ".prproj": "media", ".veg": "media", ".drp": "media",
    
    # --- media: audio files ---
    ".mp3": "media", ".wav": "media", ".flac": "media", ".aac": "media", 
    ".ogg": "media", ".m4a": "media",

}
ALLOWED_FORMATS = list(EXT_SUPERTYPES.keys()) + [".zip"]
