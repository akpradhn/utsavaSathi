#!/usr/bin/env python3
"""
Git Commit Message Agent

Automatically generates commit messages based on staged changes.
Usage: python commit_agent.py [--auto-commit]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


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


def analyze_diff_content(diff: str, files: List[Tuple[str, str]]) -> Dict[str, Dict]:
    """Analyze the actual diff content to understand what changed."""
    file_analysis = {}
    
    # Split diff by file
    current_file = None
    current_diff = []
    
    for line in diff.split("\n"):
        # Match file header: diff --git a/path b/path or --- a/path / +++ b/path
        if line.startswith("diff --git"):
            if current_file and current_diff:
                file_analysis[current_file] = analyze_file_diff(current_file, "\n".join(current_diff))
            # Extract filename from diff --git a/file b/file
            match = re.search(r"diff --git a/(.+?) b/(.+?)$", line)
            if match:
                current_file = match.group(2)
                current_diff = [line]
            else:
                current_file = None
                current_diff = []
        elif current_file:
            current_diff.append(line)
    
    # Process last file
    if current_file and current_diff:
        file_analysis[current_file] = analyze_file_diff(current_file, "\n".join(current_diff))
    
    return file_analysis


def analyze_file_diff(file_path: str, diff_content: str) -> Dict:
    """Analyze diff for a single file to extract meaningful changes."""
    analysis = {
        "additions": 0,
        "deletions": 0,
        "functions_added": [],
        "functions_modified": [],
        "imports_added": [],
        "imports_removed": [],
        "config_changes": [],
        "key_changes": [],
    }
    
    lines = diff_content.split("\n")
    in_hunk = False
    
    for line in lines:
        # Count additions and deletions
        if line.startswith("+") and not line.startswith("+++"):
            analysis["additions"] += 1
            content = line[1:].strip()
            
            # Detect function definitions
            func_match = re.search(r"^(?:def|async def|class)\s+(\w+)", content)
            if func_match:
                analysis["functions_added"].append(func_match.group(1))
            
            # Detect imports
            if content.startswith("import ") or content.startswith("from "):
                analysis["imports_added"].append(content)
            
            # Detect configuration changes
            if "=" in content and not content.startswith("#"):
                key_match = re.search(r"^(\w+)\s*=", content)
                if key_match:
                    analysis["config_changes"].append(f"Added: {key_match.group(1)}")
            
        elif line.startswith("-") and not line.startswith("---"):
            analysis["deletions"] += 1
            content = line[1:].strip()
            
            # Detect removed functions
            func_match = re.search(r"^(?:def|async def|class)\s+(\w+)", content)
            if func_match:
                analysis["functions_modified"].append(func_match.group(1))
            
            # Detect removed imports
            if content.startswith("import ") or content.startswith("from "):
                analysis["imports_removed"].append(content)
            
            # Detect removed configuration
            if "=" in content and not content.startswith("#"):
                key_match = re.search(r"^(\w+)\s*=", content)
                if key_match:
                    analysis["config_changes"].append(f"Removed: {key_match.group(1)}")
    
    return analysis


def generate_text_description(analysis: dict, diff_analysis: Dict[str, Dict], files: List[Tuple[str, str]]) -> str:
    """Generate a human-readable description of the changes."""
    descriptions = []
    
    new_files = analysis["new_files"]
    modified_files = analysis["modified_files"]
    deleted_files = analysis["deleted_files"]
    
    # Describe new files
    if new_files:
        for file_path in new_files:
            path = Path(file_path)
            file_analysis = diff_analysis.get(file_path, {})
            
            if path.suffix == ".py":
                funcs = file_analysis.get("functions_added", [])
                if funcs:
                    descriptions.append(f"Added {path.name} with {len(funcs)} function(s): {', '.join(funcs[:3])}")
                else:
                    descriptions.append(f"Added {path.name}")
            elif path.suffix == ".sh":
                descriptions.append(f"Added {path.name} script")
            elif path.suffix == ".md":
                descriptions.append(f"Added {path.name} documentation")
            elif path.name == ".gitignore":
                descriptions.append("Added .gitignore with project exclusions")
            elif "requirements" in path.name.lower():
                descriptions.append("Added/updated dependencies")
            else:
                descriptions.append(f"Added {path.name}")
    
    # Describe modified files
    if modified_files:
        for file_path in modified_files:
            path = Path(file_path)
            file_analysis = diff_analysis.get(file_path, {})
            additions = file_analysis.get("additions", 0)
            deletions = file_analysis.get("deletions", 0)
            funcs_added = file_analysis.get("functions_added", [])
            funcs_modified = file_analysis.get("functions_modified", [])
            
            if path.suffix == ".py":
                changes = []
                if funcs_added:
                    changes.append(f"added {len(funcs_added)} function(s)")
                if funcs_modified:
                    changes.append(f"modified {len(funcs_modified)} function(s)")
                if additions > 0 or deletions > 0:
                    if not changes:
                        changes.append(f"{additions} addition(s), {deletions} deletion(s)")
                
                if changes:
                    descriptions.append(f"Updated {path.name}: {', '.join(changes)}")
                else:
                    descriptions.append(f"Updated {path.name}")
            else:
                if additions > 0 or deletions > 0:
                    descriptions.append(f"Updated {path.name} ({additions} additions, {deletions} deletions)")
                else:
                    descriptions.append(f"Updated {path.name}")
    
    # Describe deleted files
    if deleted_files:
        for file_path in deleted_files:
            descriptions.append(f"Removed {Path(file_path).name}")
    
    return "\n".join(descriptions) if descriptions else "Updated files"


def generate_commit_message(analysis: dict, diff: str, files: List[Tuple[str, str]]) -> str:
    """Generate a commit message based on the analysis and diff content."""
    new_files = analysis["new_files"]
    modified_files = analysis["modified_files"]
    deleted_files = analysis["deleted_files"]
    
    # Analyze diff content to understand what actually changed
    diff_analysis = analyze_diff_content(diff, files)
    
    # Generate descriptive text about changes
    description_text = generate_text_description(analysis, diff_analysis, files)
    
    # Determine the main change type
    if new_files and not modified_files and not deleted_files:
        change_type = "Add"
    elif modified_files and not new_files and not deleted_files:
        change_type = "Update"
    elif deleted_files:
        change_type = "Remove"
    else:
        change_type = "Update"
    
    # Generate title based on files and content
    title_parts = []
    
    # Check for common patterns in file names
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
    
    # Analyze diff for more context
    total_additions = sum(da.get("additions", 0) for da in diff_analysis.values())
    total_deletions = sum(da.get("deletions", 0) for da in diff_analysis.values())
    
    # If no specific patterns, use file count or diff stats
    if not title_parts:
        total_changes = len(new_files) + len(modified_files) + len(deleted_files)
        if total_changes == 1:
            changed_file = (new_files + modified_files + deleted_files)[0]
            title_parts.append(Path(changed_file).name)
        else:
            title_parts.append(f"{total_changes} files")
    
    title = f"{change_type}: {', '.join(title_parts)}"
    
    # Generate body with meaningful descriptions
    body_lines = []
    
    # Add the generated description text
    if description_text:
        body_lines.append(description_text)
    
    # Add summary statistics if significant
    if total_additions > 0 or total_deletions > 0:
        body_lines.append(f"\nChanges: +{total_additions} additions, -{total_deletions} deletions")
    
    # Add function-level details for Python files
    python_changes = []
    for file_path, file_analysis in diff_analysis.items():
        if Path(file_path).suffix == ".py":
            funcs_added = file_analysis.get("functions_added", [])
            funcs_modified = file_analysis.get("functions_modified", [])
            if funcs_added or funcs_modified:
                file_name = Path(file_path).name
                details = []
                if funcs_added:
                    details.append(f"added: {', '.join(funcs_added[:5])}")
                if funcs_modified:
                    details.append(f"modified: {', '.join(funcs_modified[:5])}")
                if details:
                    python_changes.append(f"{file_name}: {', '.join(details)}")
    
    if python_changes:
        body_lines.append("\nFunction changes:")
        for change in python_changes[:5]:  # Limit to 5 files
            body_lines.append(f"- {change}")
    
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
    commit_message = generate_commit_message(analysis, diff, staged_files)
    
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

