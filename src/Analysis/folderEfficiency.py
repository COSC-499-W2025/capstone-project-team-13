# src/Analysis/folder_efficiency.py

import os
from typing import Dict, Any, List
from tqdm import tqdm
from .codeEfficiency import grade_efficiency
from src.Settings.config import EXT_SUPERTYPES  # import the mapping

# Only include extensions classified as "code"
CODE_EXTENSIONS = [ext for ext, typ in EXT_SUPERTYPES.items() if typ == "code"]

def is_code_file(filename: str) -> bool:
    return any(filename.endswith(ext) for ext in CODE_EXTENSIONS)

def grade_folder(folder_path: str) -> Dict[str, Any]:
    """
    Recursively grades all code files in a folder and aggregates results.
    Shows a progress bar.
    """
    file_results = []

    # Collect all code files first for tqdm
    code_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if is_code_file(file):
                code_files.append(os.path.join(root, file))

    # Process files with progress bar
    for file_path in tqdm(code_files, desc="Grading files", unit="file"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            result = grade_efficiency(code, file_path)
            file_results.append(result)
        except Exception as e:
            file_results.append({
                "file_path": file_path,
                "time_score": None,
                "space_score": None,
                "efficiency_score": None,
                "max_loop_depth": None,
                "total_loops": None,
                "notes": [f"Failed to read or parse file: {e}"]
            })

    return aggregate_results(file_results)

def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate results across all files, returning only final summary.
    """
    agg = {
        "num_files": len(results),
        "avg_time_score": None,
        "avg_space_score": None,
        "avg_efficiency_score": None,
        "total_loops": 0,
        "max_loop_depth": 0,
    }

    time_scores = []
    space_scores = []
    eff_scores = []

    for r in results:
        if r.get("time_score") is not None:
            time_scores.append(r["time_score"])
        if r.get("space_score") is not None:
            space_scores.append(r["space_score"])
        if r.get("efficiency_score") is not None:
            eff_scores.append(r["efficiency_score"])
        if r.get("total_loops") is not None:
            agg["total_loops"] += r["total_loops"]
        if r.get("max_loop_depth") is not None:
            agg["max_loop_depth"] = max(agg["max_loop_depth"], r["max_loop_depth"])

    if time_scores:
        agg["avg_time_score"] = round(sum(time_scores) / len(time_scores), 2)
    if space_scores:
        agg["avg_space_score"] = round(sum(space_scores) / len(space_scores), 2)
    if eff_scores:
        agg["avg_efficiency_score"] = round(sum(eff_scores) / len(eff_scores), 2)

    return agg

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Grade code efficiency for all files in a folder")
    parser.add_argument("folder", help="Path to the folder to grade")
    args = parser.parse_args()

    summary = grade_folder(args.folder)
    print("=== Folder Efficiency Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v}")
