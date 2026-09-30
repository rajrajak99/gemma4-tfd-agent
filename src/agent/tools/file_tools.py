"""
File manipulation tools for TFD-Agent.
Provides safe viewing, line-bounded reading, and surgical editing.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

def view_file(file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
    """
    View file contents with line numbers.
    """
    p = Path(file_path)
    if not p.is_file():
        return {"error": f"File not found: {file_path}"}
    
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        s = max(1, start_line or 1)
        e = min(total_lines, end_line or total_lines)
        
        if s > total_lines:
            return {"error": f"start_line {s} exceeds total lines ({total_lines})"}
        
        numbered = [f"{i}: {lines[i-1]}" for i in range(s, e + 1)]
        return {
            "file_path": str(p),
            "total_lines": total_lines,
            "start_line": s,
            "end_line": e,
            "content": "".join(numbered)
        }
    except Exception as exc:
        return {"error": f"Failed to read file: {str(exc)}"}

def edit_file_replace(file_path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """
    Surgically replace exact string occurrence in a target file.
    """
    p = Path(file_path)
    if not p.is_file():
        return {"error": f"File not found: {file_path}"}
    
    try:
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
            
        count = content.count(old_str)
        if count == 0:
            return {"error": "Target old_str not found in file. Ensure exact whitespace and indentation."}
        if count > 1:
            return {"error": f"Target old_str occurs {count} times. Provide more surrounding context to make it unique."}
            
        updated = content.replace(old_str, new_str, 1)
        with open(p, "w", encoding="utf-8") as f:
            f.write(updated)
            
        return {
            "success": True,
            "file_path": str(p),
            "message": "Replacement applied successfully."
        }
    except Exception as exc:
        return {"error": f"Failed to edit file: {str(exc)}"}
