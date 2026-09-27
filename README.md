# 🧠 TFD-Agent: Test-Feedback-Driven Autonomous Software Engineering in Google Gemma 4

[![Kaggle Track](https://img.shields.io/badge/Kaggle-Gemma%204%20Paper%20Track-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper)
[![Model](https://img.shields.io/badge/Base%20Model-Gemma%204%2031B%20Dense-8E75FF?logo=google&logoColor=white)](https://huggingface.co/google/gemma-4-31b-it)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

Official research codebase and artifacts for **"TFD-Agent: Advancing Autonomous Software Engineering on Edge Hardware via Test-Feedback-Driven Self-Correction in Gemma 4"** submitted to the Google DeepMind *Gemma 4 Developer Agent Paper Track* (Kaggle 2026).

**Author:** Raja Rajak ([@rajrajak99](https://www.kaggle.com/rajrajak99))  
**Research Writeup:** [Read Paper on Kaggle](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/writeups/tfd-agent-advancing-autonomous-software-engineeri)

---

## 📌 Overview

Autonomous software engineering agents increasingly rely on closed cloud APIs (GPT-5/6, Claude Opus). While capable, these models incur severe financial costs, introduce intellectual property privacy risks, and cannot run offline on local developer machines. 

**TFD-Agent** (Test-Feedback-Driven Agent) provides a disciplined, closed-loop scaffolding around Google's open-weight **Gemma 4 31B Dense** (`gemma-4-31b-it-qat-w4a16-ct`), achieving state-of-the-art autonomous problem resolution on single-GPU workstation hardware.

```
                    ┌────────────────────────────┐
                    │      GitHub Issue Spec     │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │    1. Codebase Locator     │
                    │   (rg + AST Code Search)   │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │    2. Reproducer Engine    │
                    │   (Synthesize & Run Test)  │
                    └─────────────┬──────────────┘
                                  │
                     Did reproduction FAIL? (Expected)
                                  ├── NO  ──► Refine Reproducer
                                  └── YES
                                  ▼
                    ┌────────────────────────────┐
                    │     3. Patch Generator     │
                    │  (Surgical String Replace) │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │    4. Verification Loop    │
                    │   (Run Reproducer + Repo)  │
                    └─────────────┬──────────────┘
                                  │
                         All Tests Pass?
                                  ├── YES ──► Export Validated Diff
                                  └── NO
                                  ▼
                    ┌────────────────────────────┐
                    │   5. Traceback Analyzer    │
                    │  (Extract Culprit Frame)   │
                    └─────────────┬──────────────┘
                                  │
                                  └──► (Feedback Loop to Step 3)
```

---

## 🚀 Key Innovations

1. **Test-First Reproducer Engine:** Unlike standard agents that blindly modify code, TFD-Agent autonomously writes and runs a minimal standalone test (`reproduce_issue.py`) confirming the bug (Exit Code != 0) *before* touching production code.
2. **Execution-Traceback Self-Correction:** When candidate patches fail, the `TracebackParser` extracts exact culprit frames, exception classes, and variables, feeding surgical diagnosis directly back into Gemma 4's `<thought>` planning loop.
3. **All-Linear QLoRA Post-Training:** Fine-tuned on multi-turn software engineering trajectories across all linear layers (`q, k, v, o, gate, up, down_proj`) with rank $r=16, \alpha=32$ on single workstation hardware.
4. **Context Token Efficiency:** Dynamic search pruning and surgical unified diffs reduce context token consumption by **49.5%** compared to standard ReAct implementations.

---

## 📊 Empirical Results (SWE-bench Lite)

Evaluated across standard SWE-bench Lite instances on Google Gemma 4 31B:

| System / Model Configuration | Pass@1 Rate (%) | Context Tokens (Mean) | Compute Constraint |
| :--- | :---: | :---: | :---: |
| Direct Zero-Shot (Gemma 4 31B) | 18.2% | 14,200 | Single Workstation |
| Standard ReAct Loop (Gemma 4 31B) | 29.5% | 38,400 | Single Workstation |
| SWE-agent Baseline (Gemma 4 31B) | 33.1% | 34,100 | Single Workstation |
| TFD-Agent (Prompt-Only) | 39.7% | 22,800 | Single Workstation |
| **TFD-Agent + QLoRA (Ours - Full)** | **45.6%** | **19,400** | **Single Workstation** |

> **Highlights:** **+2.5× performance jump** over baseline zero-shot; **+12.5% advantage** over standard SWE-agent; **49.5% token reduction**.

---

## 🛠️ Repository Structure

```
gemma4-tfd-agent/
├── agent.yaml                 # Kaggle Competition root agent configuration
├── requirements.txt           # Python environment dependencies
├── paper/
│   └── draft.md               # Full research paper writeup text
├── src/
│   ├── agent/
│   │   ├── loop.py            # Closed-loop execution controller
│   │   ├── prompts.py         # Disciplined system prompts with <thought> enforcement
│   │   ├── verifier.py        # Sandboxed test runner & TracebackParser
│   │   └── tools/             # Surgical file edit, search, and reproduction tools
│   ├── training/
│   │   └── train_qlora.py     # Parameter-efficient QLoRA fine-tuning script
│   └── eval/
│       └── benchmark.py       # SWE-bench Lite test runner and metric reporter
└── tests/                     # Unit test verification suite
```

---

## ⚡ Quick Start

### 1. Installation
```bash
git clone https://github.com/rajrajak99/gemma4-tfd-agent.git
cd gemma4-tfd-agent
pip install -r requirements.txt
```

### 2. Run TFD-Agent on an Issue
```python
from src.agent.loop import TFDAgent

agent = TFDAgent(config_path="agent.yaml")
result = agent.solve_issue(
    issue_description="ZeroDivisionError in calculate_precision_recall when tp+fp == 0",
    repo_path="./target_repository"
)

if result.is_resolved:
    print("Issue successfully resolved!")
    print(result.git_patch)
```

### 3. Verify Agent Scaffolding
```bash
pytest tests/
```

---

## 📜 Citation & Attribution

If you reference or build upon this research:

```bibtex
@article{rajak2026tfdagent,
  title   = {TFD-Agent: Advancing Autonomous Software Engineering on Edge Hardware via Test-Feedback-Driven Self-Correction in Gemma 4},
  author  = {Rajak, Raja},
  journal = {Google - The Gemma 4 Developer Agent Paper Track (Kaggle)},
  year    = {2026},
  url     = {https://github.com/rajrajak99/gemma4-tfd-agent}
}
```

---

## 📄 License
This project is open-sourced under the [Apache 2.0 License](LICENSE).
