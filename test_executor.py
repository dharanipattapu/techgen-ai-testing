import re
import json
import os
from groq import Groq
 
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"
 
 
# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────
 
_SYSTEM_EXECUTOR = """You are an expert QA engineer and code reviewer performing intelligent test execution analysis.
 
You will be given:
1. Source code from one or more files
2. A list of test cases (each with a title, steps, expected result, priority, and type)
 
Your job: For EACH test case, carefully read the actual source code and determine whether that test case would PASS or FAIL based on what the code actually implements.
 
Rules:
- Read the real code logic — check if the function/route/feature the test case targets actually exists and works correctly
- PASS means: the code correctly implements what the test case expects
- FAIL means: the code is missing the feature, has a bug, wrong logic, missing validation, missing error handling, or does not match the expected result
- Be specific in your message — reference the actual function name, variable, route, or line of logic you found (or didn't find)
- Do NOT be random — base every verdict on real code evidence
- If the code file for that test case type is not present, mark as Failed with reason "Relevant code not found in uploaded files"
 
Respond ONLY with a valid JSON array. No preamble, no markdown, no explanation.
 
Format:
[
  {
    "title": "exact title from input",
    "status": "Passed" or "Failed",
    "priority": "exact priority from input",
    "type": "exact type from input",
    "message": "specific reason referencing actual code — what you found or what is missing/wrong"
  }
]"""
 
 
# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
 
def _sanitize_json(raw: str) -> str:
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'```\s*$', '', raw, flags=re.MULTILINE)
    raw = raw.strip()
    raw = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw)
 
    def fix_newlines(m):
        return m.group(0).replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
 
    raw = re.sub(r'"(?:[^"\\]|\\.)*"', fix_newlines, raw, flags=re.DOTALL)
    return raw
 
 
def _build_code_context(code_files: dict) -> str:
    """Format uploaded code files into a readable context block."""
    if not code_files:
        return "No source code files provided."
    parts = []
    for filename, code in code_files.items():
        # Truncate very large files to stay within token limits
        truncated = code[:5000]
        if len(code) > 5000:
            truncated += f"\n... [truncated — {len(code) - 5000} more chars]"
        parts.append(f"=== FILE: {filename} ===\n{truncated}")
    return "\n\n".join(parts)
 
 
def _build_test_cases_context(test_cases: list) -> str:
    """Format test cases into a numbered list for the prompt."""
    lines = []
    for i, t in enumerate(test_cases, 1):
        lines.append(
            f"Test {i}:\n"
            f"  Title: {t.get('title', '')}\n"
            f"  Steps: {t.get('steps', '')}\n"
            f"  Expected: {t.get('expected', '')}\n"
            f"  Priority: {t.get('priority', 'Medium')}\n"
            f"  Type: {t.get('type', 'Functional')}"
        )
    return "\n\n".join(lines)
 
 
def _fallback_results(test_cases: list, error_msg: str) -> list:
    """Return error results if AI call fails, preserving all test case data."""
    return [
        {
            "title":    t.get("title", "Unknown Test"),
            "status":   "Failed",
            "priority": t.get("priority", "Medium"),
            "type":     t.get("type", "Functional"),
            "message":  f"Analysis error: {error_msg}",
        }
        for t in test_cases
    ]
 
 
# ─────────────────────────────────────────────────────────────────────────────
# BATCH EXECUTOR — splits into chunks to stay within token limits
# ─────────────────────────────────────────────────────────────────────────────
 
def _analyze_batch(test_cases: list, code_context: str) -> list:
    """Send one batch of test cases to the AI for analysis."""
    tc_context = _build_test_cases_context(test_cases)
 
    user_content = (
        f"SOURCE CODE:\n{code_context}\n\n"
        f"TEST CASES TO EVALUATE:\n{tc_context}\n\n"
        f"Analyze each test case against the source code above. "
        f"Return a JSON array with exactly {len(test_cases)} results."
    )
 
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": _SYSTEM_EXECUTOR},
            {"role": "user",   "content": user_content},
        ]
    )
 
    raw = response.choices[0].message.content.strip()
    raw = _sanitize_json(raw)
 
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            raise ValueError("No valid JSON array in model response")
        data = json.loads(_sanitize_json(match.group()))
 
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array")
 
    return data
 
 
def _merge_results(ai_results: list, original_cases: list) -> list:
    """
    Merge AI results back with original test cases.
    - Preserves exact title/priority/type from originals
    - Falls back gracefully if AI returned fewer results than expected
    """
    # Build a lookup by title for fast matching
    ai_map = {}
    for r in ai_results:
        title = str(r.get("title", "")).strip()
        if title:
            ai_map[title] = r
 
    merged = []
    for t in original_cases:
        orig_title    = str(t.get("title", "")).strip()
        orig_priority = t.get("priority", "Medium")
        orig_type     = t.get("type", "Functional")
 
        # Try exact match first, then partial match
        ai_result = ai_map.get(orig_title)
        if not ai_result:
            for key, val in ai_map.items():
                if orig_title.lower() in key.lower() or key.lower() in orig_title.lower():
                    ai_result = val
                    break
 
        if ai_result:
            status  = ai_result.get("status", "Failed")
            message = ai_result.get("message", "No analysis returned.")
            # Normalise status to exactly Passed/Failed
            if "pass" in status.lower():
                status = "Passed"
            else:
                status = "Failed"
        else:
            status  = "Failed"
            message = "AI did not return a result for this test case."
 
        merged.append({
            "title":    orig_title or "Unknown Test",
            "status":   status,
            "priority": orig_priority,
            "type":     orig_type,
            "message":  message,
        })
 
    return merged
 
 
# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────
 
def execute_tests(test_cases: list, code_files: dict = None) -> list:
    """
    Execute test cases using AI analysis of the actual source code.
 
    Args:
        test_cases: List of test case dicts (title, steps, expected, priority, type).
        code_files: Dict of {filename: code_string} — the project source code to test against.
                    If empty/None, the AI will assess based on test case content alone.
 
    Returns:
        List of result dicts with title, status, priority, type, message.
    """
    if not test_cases:
        return []
 
    code_context = _build_code_context(code_files or {})
 
    # Split into batches of 8 to stay within token limits
    BATCH_SIZE = 8
    all_ai_results = []
 
    batches = [test_cases[i:i + BATCH_SIZE] for i in range(0, len(test_cases), BATCH_SIZE)]
 
    for batch_num, batch in enumerate(batches, 1):
        try:
            batch_results = _analyze_batch(batch, code_context)
            all_ai_results.extend(batch_results)
        except Exception as e:
            # If a batch fails, fill with error results for that batch only
            error_msg = str(e)[:120]
            all_ai_results.extend(
                [{"title": t.get("title", ""), "status": "Failed",
                  "priority": t.get("priority", "Medium"), "type": t.get("type", "Functional"),
                  "message": f"AI analysis failed for batch {batch_num}: {error_msg}"}
                 for t in batch]
            )
 
    # Merge AI results back to original test cases (handles any title mismatches)
    return _merge_results(all_ai_results, test_cases)