import os
from PIL import Image, ExifTags

def analyze_visual_project(folder_path):
    """
    Analyze a folder containing visual/media files.
    Returns insights such as likely software used and top skills involved.
    """

    supported_formats = ('.png', '.jpg', '.jpeg', '.psd', '.svg', '.ai', '.blend', '.fig', '.mp4')
    image_files = []
    software_detected = set()
    skills_detected = set()

    # Crawl folder for media files
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(supported_formats):
                image_files.append(os.path.join(root, file))

    if not image_files:
        return {"type": "media", "details": "No media files found."}

    # --- Infer software & skills based on extensions ---
    for path in image_files:
        ext = os.path.splitext(path)[1].lower()

        # Infer software
        if ext in ['.psd']:
            software_detected.add("Adobe Photoshop")
            skills_detected.update(["Digital Painting", "Photo Editing", "Layer Compositing"])
        elif ext in ['.ai', '.svg']:
            software_detected.add("Adobe Illustrator")
            skills_detected.update(["Vector Illustration", "Logo Design"])
        elif ext in ['.blend']:
            software_detected.add("Blender")
            skills_detected.update(["3D Modeling", "Rendering", "Lighting", "Animation"])
        elif ext in ['.fig']:
            software_detected.add("Figma")
            skills_detected.update(["UI Design", "Prototyping"])
        elif ext in ['.mp4']:
            software_detected.add("Video Editor (Premiere/After Effects)")
            skills_detected.update(["Motion Design", "Editing", "Color Grading"])
        else:
            software_detected.add("Generic Image Editor")
            skills_detected.update(["Image Editing", "Composition"])

        # Check EXIF metadata for program info
        if ext in ['.jpg', '.jpeg', '.png']:
            try:
                with Image.open(path) as img:
                    exif_data = img.getexif()
                    for tag, value in exif_data.items():
                        decoded = ExifTags.TAGS.get(tag, tag)
                        if decoded == "Software":
                            if "Photoshop" in value:
                                software_detected.add("Adobe Photoshop")
                            elif "Blender" in value:
                                software_detected.add("Blender Render")
                            elif "Illustrator" in value:
                                software_detected.add("Adobe Illustrator")
            except Exception:
                continue

    # --- Estimate project effort ---
    total_size = sum(os.path.getsize(f) for f in image_files)
    num_files = len(image_files)
    

    # --- Return analysis summary ---
    return {
        "type": "visual/media project",
        "num_files": num_files,
        "software_used": list(software_detected),
        "skills_detected": list(skills_detected)
    }