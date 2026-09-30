"""
Sandboxed bash runner for TFD-Agent.
Safely executes terminal commands, test runners, and captures standard streams.
"""
import os
import subprocess
from typing import Dict, Any

def run_bash(command: str, cwd: str, timeout_seconds: int = 60) -> Dict[str, Any]:
    """
    Execute a shell command with timeout and bounded output capture.
    """
    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        # Prevent context blowup by capping output length
        stdout = proc.stdout[-4000:] if len(proc.stdout) > 4000 else proc.stdout
        stderr = proc.stderr[-4000:] if len(proc.stderr) > 4000 else proc.stderr
        
        return {
            "exit_code": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "success": proc.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout_seconds} seconds.",
            "success": False
        }
    except Exception as exc:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Execution error: {str(exc)}",
            "success": False
        }
