"""
Trajectory Synthesis and Distillation Pipeline using Gemini 3.8 Flash.
Generates multi-turn Test-Feedback-Driven (TFD) agent demonstrations from issue descriptions.
"""
import os
import json
from typing import List, Dict, Any

DISTILLATION_PROMPT = """
You are an expert software engineer generating gold-standard agentic trajectories for fine-tuning Gemma 4 31B.
Given a GitHub issue and code snippet, produce a realistic multi-turn interaction demonstrating the TFD (Test-Feedback-Driven) protocol:

Turn 1: Model reasons in <thought> about repository structure, calls `search_code` or `find_files`.
Turn 2: Model views target file via `view_file`.
Turn 3: Model creates a minimal failing reproduction script `create_reproducer`.
Turn 4: Model applies a surgical fix via `edit_file_replace`.
Turn 5: Model runs `verify_fix`. If it fails, demonstrates traceback analysis and self-correction.
Turn 6: Final successful verification and conclusion.

Return the trajectory as a JSON array of message objects compatible with Gemma 4 chat template.
"""

def convert_to_gemma_chat(trajectory: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Convert a multi-turn conversation into Gemma 4 token-ready format.
    """
    formatted_text = "<start_of_turn>developer\nYou are TFD-Agent for Gemma 4.<end_of_turn>\n"
    for msg in trajectory:
        role = msg["role"]
        content = msg["content"]
        formatted_text += f"<start_of_turn>{role}\n{content}<end_of_turn>\n"
    return {"text": formatted_text}

def save_training_dataset(trajectories: List[List[Dict[str, str]]], output_path: str):
    """
    Save trajectories to JSONL for SFT/QLoRA training.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for traj in trajectories:
            item = convert_to_gemma_chat(traj)
            f.write(json.dumps(item) + "\n")
    print(f"Saved {len(trajectories)} training trajectories to {output_path}")

if __name__ == "__main__":
    # Sample synthetic seed trajectory demonstrating the format
    sample_trajectory = [
        {"role": "user", "content": "Issue #42: ZeroDivisionError in calculate_metrics when batch is empty."},
        {"role": "model", "content": "<thought>I should search for where calculate_metrics is defined.</thought>\n```json\n{\"tool\": \"search_code\", \"arguments\": {\"query\": \"def calculate_metrics\"}}\n```"},
        {"role": "user", "content": "{\"total_matches\": 1, \"matches\": [{\"file\": \"metrics/eval.py\", \"line\": 45}]}"},
        {"role": "model", "content": "<thought>Let's view the function.</thought>\n```json\n{\"tool\": \"view_file\", \"arguments\": {\"file_path\": \"metrics/eval.py\", \"start_line\": 40, \"end_line\": 55}}\n```"},
        {"role": "user", "content": "45: def calculate_metrics(items):\n46:     return sum(items) / len(items)"},
        {"role": "model", "content": "<thought>We need to guard against len(items) == 0. First let's write a reproducer test.</thought>\n```json\n{\"tool\": \"create_reproducer\", \"arguments\": {\"script_code\": \"from metrics.eval import calculate_metrics\\nassert calculate_metrics([]) == 0.0\"}}\n```"},
        {"role": "user", "content": "{\"success\": true}"},
        {"role": "model", "content": "<thought>Now let's replace the vulnerable line with a zero check.</thought>\n```json\n{\"tool\": \"edit_file_replace\", \"arguments\": {\"file_path\": \"metrics/eval.py\", \"old_str\": \"    return sum(items) / len(items)\", \"new_str\": \"    if not items:\\n        return 0.0\\n    return sum(items) / len(items)\"}}\n```"},
        {"role": "user", "content": "{\"success\": true}"},
        {"role": "model", "content": "<thought>Now verify using our reproducer.</thought>\n```json\n{\"tool\": \"verify_fix\", \"arguments\": {}}\n```"},
        {"role": "user", "content": "{\"passed\": true, \"exit_code\": 0}"},
        {"role": "model", "content": "<thought>All tests pass. Patch is ready.</thought>\nThe bug is resolved and validated."}
    ]
    
    save_training_dataset([sample_trajectory], "data/train_trajectories.jsonl")
