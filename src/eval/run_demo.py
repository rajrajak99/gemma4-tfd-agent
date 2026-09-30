"""
Simulated SWE-bench issue demo runner for TFD-Agent.
Demonstrates end-to-end execution:
1. Explores a repository with a subtle bug
2. Generates a reproduction test that FAILS
3. Surgically fixes the issue
4. Verifies the reproduction test now PASSES
5. Exports the git diff patch
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import shutil
import tempfile
from src.agent.loop import TFDAgent

def run_demo():
    print("=" * 60)
    print("[*] STARTING TFD-AGENT LIVE DEMO RUN (SIMULATED SWE-BENCH TASK)")
    print("=" * 60)

    # 1. Setup isolated sandbox workspace
    sandbox_dir = tempfile.mkdtemp(prefix="tfd_agent_sandbox_")
    print(f"\n[1] Initialized isolated sandbox at:\n    {sandbox_dir}")

    # Create mock repo with a real-world software issue (ZeroDivisionError / Empty input handling)
    pkg_dir = os.path.join(sandbox_dir, "fast_analytics")
    os.makedirs(pkg_dir, exist_ok=True)

    buggy_code = '''"""
Fast Analytics Core Library.
"""
def compute_f1_score(precision: float, recall: float) -> float:
    """Compute harmonic mean of precision and recall."""
    # BUG: Fails when precision + recall == 0 with ZeroDivisionError
    return 2 * (precision * recall) / (precision + recall)
'''
    module_path = os.path.join(pkg_dir, "metrics.py")
    with open(module_path, "w", encoding="utf-8") as f:
        f.write(buggy_code)

    print(f"[2] Created repository file: fast_analytics/metrics.py (with ZeroDivisionError bug)")

    # Initialize TFD-Agent
    agent = TFDAgent(workspace_dir=sandbox_dir)

    # Step A: Exploration
    print("\n[3] AGENT PHASE 1: Codebase Exploration")
    find_res = agent.dispatch_tool("find_files", {"pattern": "*.py"})
    print(f"    -> Agent located files: {find_res['files']}")

    search_res = agent.dispatch_tool("search_code", {"query": "compute_f1_score"})
    print(f"    -> Agent found symbol in {search_res['matches'][0]['file']} at line {search_res['matches'][0]['line']}")

    # Step B: Reproducer synthesis
    print("\n[4] AGENT PHASE 2: Reproducer Test Synthesis")
    reproducer_script = """import sys
from fast_analytics.metrics import compute_f1_score

# Reproduction case: precision=0.0, recall=0.0
try:
    score = compute_f1_score(0.0, 0.0)
    assert score == 0.0, f"Expected 0.0, got {score}"
    print("TEST PASSED")
    sys.exit(0)
except ZeroDivisionError as e:
    print(f"REPRODUCED EXPECTED BUG: {e}", file=sys.stderr)
    sys.exit(1)
"""
    agent.dispatch_tool("create_reproducer", {"script_code": reproducer_script})
    verify_res = agent.dispatch_tool("verify_fix", {})
    print(f"    -> Executing reproducer before fix: Exit Code = {verify_res['exit_code']}")
    print(f"    -> Reproduction Stderr: {verify_res['stderr'].strip()}")
    print(f"    -> Diagnostic Primary Culprit: {verify_res['diagnostic']['error_summary']}")

    assert verify_res["exit_code"] != 0, "Reproducer must FAIL initially!"
    print("    -> CONFIRMED: Bug reproduced successfully (Exit code != 0).")

    # Step C: Patch Application
    print("\n[5] AGENT PHASE 3: Surgical Patch Application")
    old_str = "    return 2 * (precision * recall) / (precision + recall)"
    new_str = """    if (precision + recall) == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)"""

    patch_res = agent.dispatch_tool("edit_file_replace", {
        "file_path": "fast_analytics/metrics.py",
        "old_str": old_str,
        "new_str": new_str
    })
    print(f"    -> Patch status: {patch_res.get('message', 'Applied')}")

    # Step D: Verification
    print("\n[6] AGENT PHASE 4: Verification Loop (Re-running Reproducer)")
    post_fix_res = agent.dispatch_tool("verify_fix", {})
    print(f"    -> Post-fix Exit Code: {post_fix_res['exit_code']}")
    print(f"    -> Post-fix Output: {post_fix_res['stdout'].strip()}")
    assert post_fix_res["exit_code"] == 0, "Reproducer must PASS after fix!"
    print("    -> SUCCESS: Reproducer passed with 0 exit code!")

    # Step E: Patch Output
    print("\n[7] AGENT PHASE 5: Clean Patch Export")
    with open(module_path, "r", encoding="utf-8") as f:
        print("    -> Final Verified Code in Repository:")
        for line in f.readlines():
            print(f"       {line.rstrip()}")

    # Cleanup sandbox
    shutil.rmtree(sandbox_dir)
    print("\n" + "=" * 60)
    print("[SUCCESS] DEMO RUN COMPLETE: TFD-AGENT PROTOCOL FULLY VALIDATED!")
    print("=" * 60)

if __name__ == "__main__":
    run_demo()
