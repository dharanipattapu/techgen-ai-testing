import re
import json
import os
from groq import Groq
 
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile" 
 
 
# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
 
def _clean(text: str) -> str:
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\.{2,}', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
 
 
def _sanitize_json(raw: str) -> str:
    """Clean raw model output so it can be safely parsed as JSON."""
    # Strip markdown code fences
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'```\s*$', '', raw, flags=re.MULTILINE)
    raw = raw.strip()
 
    # Remove invalid control characters (keep \n \r \t which are valid in JSON strings)
    raw = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw)
 
    # Replace literal (unescaped) newlines inside JSON string values with \n
    # This handles cases where the model puts real line breaks inside "steps" values
    def fix_newlines(m):
        return m.group(0).replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
 
    # Match content between quotes (simple heuristic for string values)
    raw = re.sub(r'"(?:[^"\\]|\\.)*"', fix_newlines, raw, flags=re.DOTALL)
 
    return raw
 
 
def _call_groq(system_prompt: str, user_content: str) -> list:
    """Call Groq and return a validated list of test case dicts."""
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content}
        ]
    )
 
    raw = response.choices[0].message.content.strip()
    raw = _sanitize_json(raw)
 
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Last resort: extract just the JSON array portion
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            raise ValueError("No valid JSON array found in model response")
        data = json.loads(_sanitize_json(match.group()))
 
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array from model")
 
    validated = []
    for t in data:
        if isinstance(t, dict) and "title" in t and "steps" in t and "expected" in t:
            validated.append({
                "title":    str(t.get("title", "")).strip(),
                "steps":    str(t.get("steps", "")).strip(),
                "expected": str(t.get("expected", "")).strip(),
                "priority": t.get("priority", "Medium"),
                "type":     t.get("type", "Functional"),
            })
    return validated
 
 
# ─────────────────────────────────────────────
# SYSTEM PROMPTS — one per input mode
# ─────────────────────────────────────────────
 
_SYSTEM_DESCRIPTION = """You are a senior QA engineer. The user gives you a plain-text description of a software system or feature.
 
Your job: read the description carefully and produce SPECIFIC, ACCURATE test cases that directly test the functionality described.
 
Rules:
- Every test case MUST reference actual details from the description (feature names, fields, actions, roles, data types, etc.)
- Do NOT produce generic tests like "Validate system functionality" — make each title specific to what is described
- Steps must be concrete and numbered, referencing real elements from the input
- Expected result must describe the exact outcome, not just "system behaves as expected"
- Produce 8–14 test cases covering: happy paths, edge cases, error handling, boundary values, security where relevant
- priority: "High" for auth/data/security/core flows, "Medium" for standard features, "Low" for UI/cosmetic
- type: one of Functional | Security | Performance | Reliability | UI | API | Integration
 
Respond ONLY with a valid JSON array — no preamble, no markdown, no code fences, no explanation.
 
Format:
[
  {
    "title": "specific title referencing actual feature from description",
    "steps": "1. specific step\n2. specific step\n3. specific step",
    "expected": "exact concrete expected outcome",
    "priority": "High|Medium|Low",
    "type": "Functional|Security|Performance|Reliability|UI|API|Integration"
  }
]"""
 
 
_SYSTEM_CODE = """You are a senior QA / SDET engineer. The user gives you source code from one or more files.
 
Your job: read the actual code and produce test cases that DIRECTLY test that specific code.
 
Rules:
- Name real functions, classes, routes, or variables from the code in your test titles and steps
- For API/Flask routes: test valid payloads, missing fields, wrong types, auth failures, edge cases per endpoint
- For Python functions: test normal inputs, None/empty inputs, boundary values, exception paths, return values
- For JavaScript functions: test DOM interactions, async calls, error states, return values
- For HTML: test form submission, button clicks, input validation, navigation
- For CSS: test responsive breakpoints, selector specificity, media query behavior
- DO NOT produce generic tests — every test must trace back to a specific function/route/element in the code
- Produce 10–15 test cases
- priority: "High" for security/data/critical logic, "Medium" for feature paths, "Low" for helpers/UI
- type: one of Functional | Security | Performance | Reliability | UI | API | Integration | Unit
 
Respond ONLY with a valid JSON array — no preamble, no markdown, no code fences, no explanation.
 
Format:
[
  {
    "title": "specific title naming the actual function/route/element being tested",
    "steps": "1. specific step\n2. specific step\n3. specific step",
    "expected": "exact concrete expected outcome",
    "priority": "High|Medium|Low",
    "type": "Functional|Security|Performance|Reliability|UI|API|Integration|Unit"
  }
]"""
 
 
_SYSTEM_PDF = """You are a senior QA engineer. The user gives you text extracted from a requirements or SRS document.
 
Your job: identify every testable requirement and produce specific, traceable test cases.
 
Rules:
- Map each test case to an actual requirement from the document — use the same terminology
- Use exact feature/field/rule language from the document in your titles and steps
- Cover: normal flow, invalid inputs, boundary conditions, business rule validation, error handling
- Produce 10–15 test cases
- priority: "High" for auth/payment/data integrity/security requirements, "Medium" for core features, "Low" for UI/display
- type: one of Functional | Security | Performance | Reliability | UI | API | Integration
 
Respond ONLY with a valid JSON array — no preamble, no markdown, no code fences, no explanation.
 
Format:
[
  {
    "title": "specific title quoting or referencing the requirement being tested",
    "steps": "1. specific step\n2. specific step\n3. specific step",
    "expected": "exact concrete expected outcome",
    "priority": "High|Medium|Low",
    "type": "Functional|Security|Performance|Reliability|UI|API|Integration"
  }
]"""
 
 
# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────
 
def generate_test_cases_from_description(text: str) -> list:
    """Generate test cases from a plain-text system description."""
    if not text or not text.strip():
        return []
    text = _clean(text)
    return _call_groq(
        _SYSTEM_DESCRIPTION,
        f"System description to generate test cases for:\n\n{text[:8000]}"
    )
 
 
def generate_test_cases_from_code(files: dict) -> list:
    """
    Generate test cases directly from source code files.
    files: dict mapping {filename: code_string}
    """
    if not files:
        return []
 
    parts = []
    for filename, code in files.items():
        parts.append(f"=== FILE: {filename} ===\n{code[:4000]}")
 
    combined = "\n\n".join(parts)
    return _call_groq(
        _SYSTEM_CODE,
        f"Source code to generate test cases for:\n\n{combined[:10000]}"
    )
 
 
def generate_test_cases_from_pdf(text: str) -> list:
    """Generate test cases from PDF-extracted requirements text."""
    if not text or not text.strip():
        return []
    text = _clean(text)
    return _call_groq(
        _SYSTEM_PDF,
        f"Requirements document to generate test cases for:\n\n{text[:8000]}"
    )
 
 
# Kept for backward compat — routes to description mode
def generate_test_cases(text: str) -> list:
    return generate_test_cases_from_description(text)
 
 
# ─────────────────────────────────────────────
# LOGIC VALIDATOR
# ─────────────────────────────────────────────
 
_SYSTEM_LOGIC_VALIDATOR = """You are an expert code reviewer. The user gives you source code from one or more files.
 
Your job: carefully read the code logic and detect ANY logical errors, bugs, or incorrect implementations.
 
Look for:
- Wrong loop conditions (e.g. while num < 0 when it should be while num > 0)
- Wrong operators (e.g. / instead of // for integer division causing infinite loops)
- Wrong variable used in output (e.g. printing the wrong variable)
- Incorrect algorithm logic (wrong formula, wrong accumulation, missing steps)
- Off-by-one errors
- Variables never updated correctly inside loops
- Conditions that make blocks unreachable or cause infinite loops
- Wrong return values or missing return statements
- Any other logic that would cause incorrect or unexpected behavior at runtime
 
Rules:
- Be strict — if the logic is wrong, report it even if syntax is valid
- Cite the EXACT line or expression that is wrong and explain WHY it is wrong
- If the code is completely correct, return an empty array []
- Do NOT report style issues, naming conventions, or missing comments — only real logic bugs
 
Respond ONLY with a valid JSON array. No preamble, no markdown, no code fences.
 
Format:
[
  {
    "file": "filename where the error is",
    "line": <line number as integer, or null if unknown>,
    "issue": "short label for the bug (e.g. Wrong loop condition)",
    "detail": "exact explanation — what the code does vs what it should do",
    "code_snippet": "the exact wrong line or expression from the code"
  }
]"""
 
 
def validate_code_logic(files: dict) -> list:
    """
    Use the AI to detect logic errors in source code before generating test cases.
 
    Args:
        files: dict mapping {filename: code_string}
 
    Returns:
        List of logic error dicts. Empty list means no errors found.
    """
    if not files:
        return []
 
    parts = []
    for filename, code in files.items():
        parts.append(f"=== FILE: {filename} ===\n{code[:4000]}")
    combined = "\n\n".join(parts)
 
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": _SYSTEM_LOGIC_VALIDATOR},
            {"role": "user",   "content": f"Review this code for logic errors:\n\n{combined}"}
        ]
    )
 
    raw = response.choices[0].message.content.strip()
    raw = _sanitize_json(raw)
 
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            return []  # If we can't parse the response, don't block — fail open
        try:
            data = json.loads(_sanitize_json(match.group()))
        except Exception:
            return []
 
    if not isinstance(data, list):
        return []
 
    # Normalise each entry
    validated = []
    for item in data:
        if isinstance(item, dict) and "issue" in item and "detail" in item:
            validated.append({
                "file":         str(item.get("file", "unknown")).strip(),
                "line":         item.get("line"),
                "issue":        str(item.get("issue", "Logic Error")).strip(),
                "detail":       str(item.get("detail", "")).strip(),
                "code_snippet": str(item.get("code_snippet", "")).strip(),
            })
 
    return validated