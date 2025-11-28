#!/usr/bin/env python3
"""
Git Commit Message Agent

Automatically generates commit messages based on staged changes.
Usage: python commit_agent.py [--auto-commit]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_git_command(cmd: List[str]) -> Tuple[str, int]:
    """Run a git command and return output and exit code."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip(), result.returncode
    except FileNotFoundError:
        print("Error: git command not found. Please install git.")
        sys.exit(1)


def get_staged_files() -> List[str]:
    """Get list of staged files."""
    output, exit_code = run_git_command(["diff", "--cached", "--name-status"])
    if exit_code != 0 or not output:
        return []
    
    files = []
    for line in output.split("\n"):
        if line.strip():
            # Format: STATUS\tFILE_PATH
            parts = line.split("\t", 1)
            if len(parts) == 2:
                status, file_path = parts
                files.append((status, file_path))
    return files


def get_staged_diff() -> str:
    """Get the diff of staged changes."""
    output, _ = run_git_command(["diff", "--cached"])
    return output


def analyze_changes(files: List[Tuple[str, str]]) -> dict:
    """Analyze staged changes and categorize them."""
    analysis = {
        "new_files": [],
        "modified_files": [],
        "deleted_files": [],
        "file_types": {},
        "directories": set(),
    }
    
    for status, file_path in files:
        path = Path(file_path)
        file_type = path.suffix or "no_extension"
        directory = str(path.parent) if path.parent != Path(".") else "root"
        
        analysis["directories"].add(directory)
        
        if status.startswith("A"):
            analysis["new_files"].append(file_path)
        elif status.startswith("M"):
            analysis["modified_files"].append(file_path)
        elif status.startswith("D"):
            analysis["deleted_files"].append(file_path)
        
        analysis["file_types"][file_type] = analysis["file_types"].get(file_type, 0) + 1
    
    return analysis


def generate_commit_message(analysis: dict, diff: str) -> str:
    """Generate a commit message based on the analysis."""
    new_files = analysis["new_files"]
    modified_files = analysis["modified_files"]
    deleted_files = analysis["deleted_files"]
    
    # Determine the main change type
    if new_files and not modified_files and not deleted_files:
        change_type = "Add"
    elif modified_files and not new_files and not deleted_files:
        change_type = "Update"
    elif deleted_files:
        change_type = "Remove"
    else:
        change_type = "Update"
    
    # Generate title based on files
    title_parts = []
    
    # Check for common patterns
    if any("test" in f.lower() for f in new_files + modified_files):
        title_parts.append("tests")
    if any("api" in f.lower() for f in new_files + modified_files):
        title_parts.append("API")
    if any("agent" in f.lower() for f in new_files + modified_files):
        title_parts.append("agent")
    if any("ui" in f.lower() or "app" in f.lower() for f in new_files + modified_files):
        title_parts.append("UI")
    if any(f.endswith(".sh") for f in new_files + modified_files):
        title_parts.append("scripts")
    if any(f.endswith(".md") for f in new_files + modified_files):
        title_parts.append("documentation")
    if any(".gitignore" in f for f in new_files + modified_files):
        title_parts.append("gitignore")
    if any("requirements" in f.lower() for f in new_files + modified_files):
        title_parts.append("dependencies")
    
    # If no specific patterns, use file count
    if not title_parts:
        total_changes = len(new_files) + len(modified_files) + len(deleted_files)
        if total_changes == 1:
            changed_file = (new_files + modified_files + deleted_files)[0]
            title_parts.append(Path(changed_file).name)
        else:
            title_parts.append(f"{total_changes} files")
    
    title = f"{change_type}: {', '.join(title_parts)}"
    
    # Generate body
    body_lines = []
    
    if new_files:
        body_lines.append("New files:")
        for f in new_files[:10]:  # Limit to 10 files
            body_lines.append(f"- {f}")
        if len(new_files) > 10:
            body_lines.append(f"- ... and {len(new_files) - 10} more")
    
    if modified_files:
        body_lines.append("Modified files:")
        for f in modified_files[:10]:
            body_lines.append(f"- {f}")
        if len(modified_files) > 10:
            body_lines.append(f"- ... and {len(modified_files) - 10} more")
    
    if deleted_files:
        body_lines.append("Deleted files:")
        for f in deleted_files[:10]:
            body_lines.append(f"- {f}")
        if len(deleted_files) > 10:
            body_lines.append(f"- ... and {len(deleted_files) - 10} more")
    
    # Add file type summary
    if analysis["file_types"]:
        file_types_str = ", ".join(
            f"{ext or 'no ext'}({count})" 
            for ext, count in sorted(analysis["file_types"].items())
        )
        body_lines.append(f"\nFile types: {file_types_str}")
    
    body = "\n".join(body_lines) if body_lines else ""
    
    return f"{title}\n\n{body}".strip()


def main():
    parser = argparse.ArgumentParser(
        description="Generate commit message from staged changes"
    )
    parser.add_argument(
        "--auto-commit",
        action="store_true",
        help="Automatically commit with the generated message",
    )
    parser.add_argument(
        "--edit",
        action="store_true",
        help="Open editor to edit the commit message before committing",
    )
    args = parser.parse_args()
    
    # Check if we're in a git repository
    _, exit_code = run_git_command(["rev-parse", "--git-dir"])
    if exit_code != 0:
        print("Error: Not in a git repository.")
        sys.exit(1)
    
    # Check if there are staged changes
    staged_files = get_staged_files()
    if not staged_files:
        print("No staged changes found. Run 'git add' first.")
        sys.exit(1)
    
    # Analyze changes
    print("Analyzing staged changes...")
    analysis = analyze_changes(staged_files)
    diff = get_staged_diff()
    
    # Generate commit message
    commit_message = generate_commit_message(analysis, diff)
    
    # Display the message
    print("\n" + "=" * 70)
    print("Generated commit message:")
    print("=" * 70)
    print(commit_message)
    print("=" * 70 + "\n")
    
    if args.auto_commit:
        if args.edit:
            # Use git commit with --edit flag
            result = subprocess.run(
                ["git", "commit", "-e", "-F", "-"],
                input=commit_message,
                text=True,
            )
            sys.exit(result.returncode)
        else:
            # Commit directly
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
            )
            if result.returncode == 0:
                print("✓ Committed successfully!")
            sys.exit(result.returncode)
    else:
        print("To commit with this message, run:")
        print(f"  git commit -m \"{commit_message.split(chr(10))[0]}\"")
        print("\nOr use --auto-commit flag to commit automatically.")


if __name__ == "__main__":
    main()

