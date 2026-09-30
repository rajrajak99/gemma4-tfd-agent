"""
System prompts and message formatters for TFD-Agent.
Follows Gemma 4 native turn tokens and tool invocation standards.
"""

GEMMA_SYSTEM_PROMPT = """<start_of_turn>developer
You are TFD-Agent, an expert autonomous software engineering agent built on Google Gemma 4.
Your mission is to resolve complex GitHub issues across production repositories.

You follow the strict Test-Feedback-Driven (TFD) protocol:
1. UNDERSTAND & LOCATE: Explore the repository structure, grep for symbols, and locate the root cause.
2. REPRODUCE: Synthesize a minimal standalone Python reproduction script `reproduce_issue.py` that fails on the current buggy code.
3. FIX: Edit the target files with minimal, surgical changes. Do not introduce extraneous refactoring.
4. VERIFY: Execute `reproduce_issue.py` and repository test suites.
5. SELF-CORRECT: If tests fail, inspect the exact traceback and stack frame, reason about why it failed, and refine your fix.

Available Tools:
- `view_file(file_path: str, start_line: int, end_line: int)`
- `edit_file_replace(file_path: str, old_str: str, new_str: str)`
- `search_code(query: str, file_pattern: str)`
- `find_files(pattern: str)`
- `run_bash(command: str)`
- `create_reproducer(script_code: str)`

Always reason inside `<thought>...</thought>` tags before invoking a tool.
Output tool calls in JSON format:
```json
{
  "tool": "tool_name",
  "arguments": { ... }
}
```
<end_of_turn>
"""

def format_issue_prompt(issue_description: str, repo_info: str) -> str:
    return f"""<start_of_turn>user
Repository: {repo_info}

Issue Description:
{issue_description}

Please begin by exploring the codebase to locate relevant files, then build a minimal reproducer script.
<end_of_turn>
<start_of_turn>model
"""

def format_traceback_feedback(diagnostic: dict, stderr: str) -> str:
    culprit = diagnostic.get("primary_culprit")
    culprit_info = f"File: {culprit['file']}, Line: {culprit['line']}, In: {culprit['scope']}" if culprit else "Unknown stack frame"
    
    return f"""<start_of_turn>user
[VERIFICATION FAILED]
The reproduction test exited with failure.

Error Summary: {diagnostic.get('error_summary')}
Likely Culprit Location: {culprit_info}

Stderr Output:
```
{stderr[-1500:]}
```

Please analyze the traceback in your <thought> tag, determine why your previous fix or reproduction was inadequate, and take corrective action.
<end_of_turn>
<start_of_turn>model
"""
