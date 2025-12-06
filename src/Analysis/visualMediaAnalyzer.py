import os
from PIL import Image, ExifTags

def analyze_visual_project(path):
    """
    Analyze a folder or single visual/media file.
    Returns insights such as likely software used and top skills involved.
    
    Supports: Images (including RAW), Design files, 3D models, Videos, Audio
    """

    # supported formats 
    supported_formats = (
        # Raster images
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.ico',
        # RAW image formats
        '.raw', '.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2',
        # Design files
        '.psd', '.psb', '.xcf', '.afphoto',
        # Vector graphics
        '.ai', '.svg', '.eps', '.cdr',
        # UI/UX design
        '.fig', '.sketch', '.xd',
        # 3D modeling
        '.blend', '.obj', '.fbx', '.max', '.ma', '.mb', '.c4d', '.3ds', '.stl',
        # Video files
        '.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg',
        # Video project files
        '.aep', '.prproj', '.veg', '.drp',
        # Audio files
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'
    )
    
    path = os.path.abspath(path)
    media_files = []
    software_detected = set()
    skills_detected = set()

    # --- Collect media files from either a folder OR a single file ---
    if os.path.isdir(path):
        # Crawl folder for media files
        for root, _, files in os.walk(path):
            for file in files:
                if file.lower().endswith(supported_formats):
                    media_files.append(os.path.join(root, file))
    elif os.path.isfile(path):
        # Single-file mode: analyze just this file if supported
        if path.lower().endswith(supported_formats):
            media_files.append(path)
    else:
        # Path doesn't exist or is something weird
        return {"type": "visual_media", "details": "Path does not exist or is not a file/folder."}

    if not media_files:
        return {"type": "visual_media", "details": "No visual media files found."}

    # --- Infer software & skills based on extensions ---
    for path in media_files:
        ext = os.path.splitext(path)[1].lower()

        # Photoshop
        if ext in ['.psd', '.psb']:
            software_detected.add("Adobe Photoshop")
            skills_detected.update(["Digital Painting", "Photo Editing", "Layer Compositing", "Image Manipulation"])
        
        # Vector graphics
        elif ext in ['.ai', '.svg', '.eps']:
            software_detected.add("Adobe Illustrator")
            skills_detected.update(["Vector Illustration", "Logo Design", "Graphic Design"])
        
        # 3D software
        elif ext in ['.blend']:
            software_detected.add("Blender")
            skills_detected.update(["3D Modeling", "Rendering", "Lighting", "Animation", "Texturing"])
        elif ext in ['.max']:
            software_detected.add("3ds Max")
            skills_detected.update(["3D Modeling", "Rendering", "Architectural Visualization"])
        elif ext in ['.ma', '.mb']:
            software_detected.add("Maya")
            skills_detected.update(["3D Modeling", "Character Animation", "Rigging", "VFX"])
        elif ext in ['.c4d']:
            software_detected.add("Cinema 4D")
            skills_detected.update(["3D Modeling", "Motion Graphics", "Rendering"])
        elif ext in ['.obj', '.fbx', '.3ds', '.stl']:
            software_detected.add("3D Modeling Software")
            skills_detected.update(["3D Modeling", "Asset Creation"])
        
        # UI/UX design
        elif ext in ['.fig']:
            software_detected.add("Figma")
            skills_detected.update(["UI Design", "Prototyping", "Interface Design", "User Experience"])
        elif ext in ['.sketch']:
            software_detected.add("Sketch")
            skills_detected.update(["UI Design", "Interface Design", "Mobile Design"])
        elif ext in ['.xd']:
            software_detected.add("Adobe XD")
            skills_detected.update(["UI Design", "Prototyping", "User Experience"])
        
        # Video editing
        elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg']:
            software_detected.add("Video Editing Software")
            skills_detected.update(["Video Editing", "Motion Design", "Color Grading"])
        elif ext in ['.aep']:
            software_detected.add("Adobe After Effects")
            skills_detected.update(["Motion Graphics", "Visual Effects", "Animation", "Compositing"])
        elif ext in ['.prproj']:
            software_detected.add("Adobe Premiere Pro")
            skills_detected.update(["Video Editing", "Color Grading", "Audio Editing"])
        elif ext in ['.veg']:
            software_detected.add("Sony Vegas Pro")
            skills_detected.update(["Video Editing", "Audio Editing"])
        elif ext in ['.drp']:
            software_detected.add("DaVinci Resolve")
            skills_detected.update(["Video Editing", "Color Grading", "Post-Production"])
        
        # RAW photography
        elif ext in ['.raw', '.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2']:
            software_detected.add("RAW Photo Editor (Lightroom/Capture One)")
            skills_detected.update(["Photography", "Photo Editing", "RAW Processing", "Color Correction"])
        
        # Other design tools
        elif ext in ['.xcf']:
            software_detected.add("GIMP")
            skills_detected.update(["Image Editing", "Photo Manipulation"])
        elif ext in ['.afphoto']:
            software_detected.add("Affinity Photo")
            skills_detected.update(["Photo Editing", "Image Manipulation"])
        elif ext in ['.cdr']:
            software_detected.add("CorelDRAW")
            skills_detected.update(["Vector Illustration", "Graphic Design"])
        
        # Audio
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']:
            software_detected.add("Audio Editing Software")
            skills_detected.update(["Audio Editing", "Sound Design", "Audio Production"])
        
        # Generic image files
        elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.ico']:
            software_detected.add("Image Editor")
            skills_detected.update(["Image Editing", "Photo Composition"])

        # Check EXIF metadata for program info (for images)
        if ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
            try:
                with Image.open(path) as img:
                    exif_data = img.getexif()
                    if exif_data:
                        for tag, value in exif_data.items():
                            decoded = ExifTags.TAGS.get(tag, tag)
                            if decoded == "Software" and isinstance(value, str):
                                # Detect software from EXIF
                                value_lower = value.lower()
                                if "photoshop" in value_lower:
                                    software_detected.add("Adobe Photoshop")
                                    skills_detected.add("Photo Editing")
                                elif "lightroom" in value_lower:
                                    software_detected.add("Adobe Lightroom")
                                    skills_detected.update(["Photography", "Photo Editing"])
                                elif "blender" in value_lower:
                                    software_detected.add("Blender")
                                    skills_detected.add("3D Rendering")
                                elif "illustrator" in value_lower:
                                    software_detected.add("Adobe Illustrator")
                                elif "affinity" in value_lower:
                                    software_detected.add("Affinity Photo")
                                elif "gimp" in value_lower:
                                    software_detected.add("GIMP")
            except Exception:
                # Skip if can't read EXIF
                continue

    # --- Calculate metrics ---
    total_size = sum(os.path.getsize(f) for f in media_files if os.path.exists(f))
    num_files = len(media_files)
    
    # --- Return analysis summary ---
    return {
        "type": "visual/media project",
        "num_files": num_files,
        "total_size": total_size,
        "software_used": sorted(list(software_detected)),
        "skills_detected": sorted(list(skills_detected))
    }