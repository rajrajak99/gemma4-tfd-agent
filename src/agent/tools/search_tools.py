"""
Search tools for TFD-Agent.
Enables fast repository exploration, code pattern matching, and file discovery.
"""
import os
import fnmatch
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

def find_files(root_dir: str, pattern: str = "*", max_results: int = 50) -> Dict[str, Any]:
    """
    Search for files matching a glob pattern starting from root_dir.
    """
    matches = []
    root = Path(root_dir)
    
    if not root.is_dir():
        return {"error": f"Directory not found: {root_dir}"}
        
    for p in root.rglob(pattern):
        # Ignore common hidden/cache directories
        rel = str(p.relative_to(root))
        if any(part.startswith(".") or part in ["__pycache__", "node_modules", "build", "dist"] for part in p.parts):
            continue
        if p.is_file():
            matches.append(rel)
            if len(matches) >= max_results:
                break
                
    return {
        "root_dir": str(root),
        "pattern": pattern,
        "total_found": len(matches),
        "files": matches
    }

def search_code(root_dir: str, query: str, file_pattern: Optional[str] = None, max_results: int = 50) -> Dict[str, Any]:
    """
    Search for text or regex pattern within files in a repository.
    Uses ripgrep if available, falling back to python scanning.
    """
    results = []
    root = Path(root_dir)
    
    # Try ripgrep first
    try:
        cmd = ["rg", "-n", "--max-count", "5", "--no-heading", query, str(root)]
        if file_pattern:
            cmd.extend(["-g", file_pattern])
            
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode in (0, 1):
            lines = proc.stdout.splitlines()[:max_results]
            for line in lines:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    file_path = os.path.relpath(parts[0], root_dir)
                    results.append({
                        "file": file_path,
                        "line": int(parts[1]),
                        "snippet": parts[2].strip()
                    })
            return {"query": query, "total_matches": len(results), "matches": results}
    except Exception:
        pass

    # Pure Python fallback
    for p in root.rglob(file_pattern or "*"):
        if p.is_file() and not any(part.startswith(".") for part in p.parts):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if query in line:
                            results.append({
                                "file": str(p.relative_to(root)),
                                "line": line_num,
                                "snippet": line.strip()
                            })
                            if len(results) >= max_results:
                                return {"query": query, "total_matches": len(results), "matches": results}
            except Exception:
                continue

    return {"query": query, "total_matches": len(results), "matches": results}
