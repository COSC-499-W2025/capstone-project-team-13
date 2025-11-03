import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src")))

from src.Analysis.visualMediaAnalyzer import analyze_visual_project

# Create dummy test folder
TEST_FOLDER = "PortfolioTest"

# Create folder if it doesn't exist
os.makedirs(TEST_FOLDER, exist_ok=True)

# Define dummy files extensions to replicate different media projects
dummy_files = [
    "portrait_final.psd",
    "lighting_render.png",
    "texture_paint.jpg",
    "character_model.blend",
    "ui_mockup.fig",
    "animation_clip.mp4",
    "logo_design.ai"
]

# Create empty placeholder files
for file_name in dummy_files:
    file_path = os.path.join(TEST_FOLDER, file_name)
    # Only create if it doesn't exist to avoid overwriting
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("")  # empty

# Run the visual analyzer 
result = analyze_visual_project(TEST_FOLDER)

print("\n--- Visual Project Analysis ---")
print(f"Number of files: {result['num_files']}")
print(f"Software detected: {', '.join(result['software_used'])}")
print(f"Skills detected: {', '.join(result['skills_detected'])}")
