"""
Core Execution Loop for TFD-Agent.
Coordinates model reasoning turns, tool dispatching, verification cycles, and patch export.
"""
import os
import json
import re
from typing import Dict, Any, List, Optional
from .tools.file_tools import view_file, edit_file_replace
from .tools.search_tools import find_files, search_code
from .tools.bash_runner import run_bash
from .verifier import VerifierEngine
from .prompts import GEMMA_SYSTEM_PROMPT, format_issue_prompt, format_traceback_feedback

class TFDAgent:
    def __init__(self, workspace_dir: str, model_client=None, max_iterations: int = 30):
        self.workspace_dir = workspace_dir
        self.model_client = model_client
        self.max_iterations = max_iterations
        self.verifier = VerifierEngine(workspace_dir)
        self.history: List[Dict[str, str]] = []

    def dispatch_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch tool calls to respective tool implementations."""
        try:
            if tool_name == "view_file":
                fpath = os.path.join(self.workspace_dir, args["file_path"])
                return view_file(fpath, args.get("start_line"), args.get("end_line"))
                
            elif tool_name == "edit_file_replace":
                fpath = os.path.join(self.workspace_dir, args["file_path"])
                return edit_file_replace(fpath, args["old_str"], args["new_str"])
                
            elif tool_name == "search_code":
                return search_code(self.workspace_dir, args["query"], args.get("file_pattern"))
                
            elif tool_name == "find_files":
                return find_files(self.workspace_dir, args.get("pattern", "*"))
                
            elif tool_name == "run_bash":
                return run_bash(args["command"], cwd=self.workspace_dir)
                
            elif tool_name == "create_reproducer":
                return self.verifier.setup_reproducer(args["script_code"])
                
            elif tool_name == "verify_fix":
                return self.verifier.execute_reproducer()
                
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as exc:
            return {"error": f"Tool execution failed: {str(exc)}"}

    def extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON tool call from model response."""
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Fallback to direct json object search
        bracket_match = re.search(r"(\{[\s\S]*\"tool\"[\s\S]*\})", text)
        if bracket_match:
            try:
                return json.loads(bracket_match.group(1))
            except json.JSONDecodeError:
                pass
        return None

    def export_patch(self) -> str:
        """Generate git diff representing the final patch."""
        # Cleanup reproducer before generating patch so it's not included in submission
        self.verifier.cleanup()
        res = run_bash("git diff", cwd=self.workspace_dir)
        return res.get("stdout", "")
