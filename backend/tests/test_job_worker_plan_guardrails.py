import os
import re

def test_job_worker_evaluation_plan_exists():
    """
    1. Assert docs/engineering/JOB_WORKER_EVALUATION_PLAN.md exists.
    """
    plan_path = os.path.join("..", "docs", "engineering", "JOB_WORKER_EVALUATION_PLAN.md")
    if not os.path.exists(plan_path):
        # Fallback to local relative path if run from repo root
        plan_path = os.path.join("docs", "engineering", "JOB_WORKER_EVALUATION_PLAN.md")
    
    assert os.path.exists(plan_path), f"JOB_WORKER_EVALUATION_PLAN.md not found at {plan_path}"

    with open(plan_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 2. Assert it contains required sections (case-insensitive checks)
    required_sections = [
        r"Current\s+state",
        r"Non-goals",
        r"Candidate\s+async\s+workloads",
        r"Job\s+lifecycle",
        r"Worker\s+architecture\s+options",
        r"Recommended\s+rollout",
        r"Guardrails",
        r"Test\s+strategy",
        r"Definition\s+of\s+done"
    ]

    for section in required_sections:
        pattern = re.compile(section, re.IGNORECASE)
        assert pattern.search(content), f"Required section '{section}' was not found in JOB_WORKER_EVALUATION_PLAN.md"

    # 3. Assert the plan explicitly says not to implement workers in this PR
    pattern_no_workers = re.compile(r"do\s+not\s+implement\s+workers\s+in\s+this\s+PR", re.IGNORECASE)
    assert pattern_no_workers.search(content), "Plan must explicitly contain the phrase 'do not implement workers in this PR'"

    # 4. Assert the plan mentions local default remains local
    pattern_local_default = re.compile(r"local\s+default\s+remains\s+local", re.IGNORECASE)
    assert pattern_local_default.search(content), "Plan must explicitly contain the phrase 'local default remains local'"

    # 5. Assert the plan mentions no file bytes in job payloads
    pattern_no_file_bytes = re.compile(r"no\s+file\s+bytes\s+in\s+job\s+payloads", re.IGNORECASE)
    assert pattern_no_file_bytes.search(content), "Plan must explicitly contain the phrase 'no file bytes in job payloads'"
