"""
Verifier and Traceback Self-Correction Engine for TFD-Agent.
Manages reproduction script synthesis, verification runs, and structured error diagnostics.
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
from .tools.bash_runner import run_bash

class TracebackParser:
    """
    Parses Python tracebacks to extract actionable diagnostic signals for the agent.
    """
    @staticmethod
    def parse(stderr: str) -> Dict[str, Any]:
        frames = []
        pattern = r'File "([^"]+)", line (\d+), in (.+)'
        for match in re.finditer(pattern, stderr):
            frames.append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "scope": match.group(3)
            })
            
        error_lines = [l.strip() for l in stderr.splitlines() if l.strip()]
        error_type_msg = error_lines[-1] if error_lines else "Unknown Error"
        
        return {
            "has_traceback": len(frames) > 0,
            "error_summary": error_type_msg,
            "failing_frames": frames,
            "primary_culprit": frames[-1] if frames else None
        }

class VerifierEngine:
    """
    Orchestrates the Test-Feedback loop:
    1. Verify issue reproduction (must FAIL initially)
    2. Verify patch fix (must PASS after modification)
    """
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.reproducer_path = os.path.join(workspace_dir, "reproduce_issue.py")

    def setup_reproducer(self, script_code: str) -> Dict[str, Any]:
        """
        Write the reproduction script to the repository root.
        """
        try:
            with open(self.reproducer_path, "w", encoding="utf-8") as f:
                f.write(script_code)
            return {"success": True, "reproducer_file": self.reproducer_path}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def execute_reproducer(self, python_cmd: str = "python") -> Dict[str, Any]:
        """
        Run the reproducer script and return structured results.
        """
        if not os.path.exists(self.reproducer_path):
            return {"success": False, "error": "Reproducer script does not exist."}
            
        res = run_bash(f"{python_cmd} reproduce_issue.py", cwd=self.workspace_dir, timeout_seconds=45)
        parsed_err = TracebackParser.parse(res["stderr"])
        
        return {
            "passed": res["success"],
            "exit_code": res["exit_code"],
            "stdout": res["stdout"],
            "stderr": res["stderr"],
            "diagnostic": parsed_err
        }

    def cleanup(self):
        """Remove temporary reproducer script before submitting patch."""
        if os.path.exists(self.reproducer_path):
            os.remove(self.reproducer_path)
