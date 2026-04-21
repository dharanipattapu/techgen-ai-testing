import ast
import re
 
# =========================
# PYTHON AST ANALYSIS
# =========================
def analyze_python(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Python syntax error: {str(e)}\n"
 
    result = ""
 
    for node in ast.walk(tree):
 
        # FUNCTIONS
        if isinstance(node, ast.FunctionDef):
            args = [arg.arg for arg in node.args.args]
            result += f"Python function '{node.name}' with inputs {args} should execute correctly\n"
 
        # ASYNC FUNCTIONS
        elif isinstance(node, ast.AsyncFunctionDef):
            args = [arg.arg for arg in node.args.args]
            result += f"Async Python function '{node.name}' with inputs {args} should handle async execution\n"
 
        # CLASSES
        elif isinstance(node, ast.ClassDef):
            result += f"Python class '{node.name}' should initialize and behave correctly\n"
 
    return result if result else "No analyzable Python constructs found.\n"
 
 
# =========================
# JAVA ANALYSIS
# =========================
def analyze_java(code):
    methods = re.findall(r'(public|private|protected)\s+\w+\s+(\w+)\s*\(', code)
    classes = re.findall(r'class\s+(\w+)', code)
 
    result = ""
 
    for cls in classes:
        result += f"Java class '{cls}' should instantiate and behave correctly\n"
 
    for _, m in methods:
        result += f"Java method '{m}' should execute and return expected result\n"
 
    return result if result else "No analyzable Java constructs found.\n"
 
 
# =========================
# JAVASCRIPT ANALYSIS
# =========================
def analyze_js(code):
    # Named functions
    named = re.findall(r'function\s+(\w+)\s*\(', code)
    # Arrow functions assigned to variables
    arrow = re.findall(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:\(.*?\)|[\w]+)\s*=>', code)
    # Class definitions
    classes = re.findall(r'class\s+(\w+)', code)
 
    result = ""
 
    for cls in classes:
        result += f"JavaScript class '{cls}' should instantiate and behave correctly\n"
 
    for f in named + arrow:
        result += f"JavaScript function '{f}' should execute and return expected result\n"
 
    return result if result else "No analyzable JavaScript constructs found.\n"
 
 
# =========================
# HTML ANALYSIS
# =========================
def analyze_html(code):
    forms = len(re.findall(r'<form', code, re.IGNORECASE))
    inputs = len(re.findall(r'<input', code, re.IGNORECASE))
    buttons = len(re.findall(r'<button', code, re.IGNORECASE))
    links = len(re.findall(r'<a\s', code, re.IGNORECASE))
 
    result = ""
 
    if forms:
        result += f"{forms} HTML form(s) detected — should submit and validate correctly\n"
    if inputs:
        result += f"{inputs} input field(s) detected — should accept and validate user input\n"
    if buttons:
        result += f"{buttons} button(s) detected — should trigger correct actions when clicked\n"
    if links:
        result += f"{links} link(s) detected — should navigate to correct destinations\n"
 
    return result if result else "No significant HTML elements found.\n"
 
 
# =========================
# CSS ANALYSIS
# =========================
def analyze_css(code):
    selectors = re.findall(r'([.#]?[\w-]+)\s*\{', code)
    media_queries = len(re.findall(r'@media', code, re.IGNORECASE))
 
    result = ""
 
    if selectors:
        result += f"{len(selectors)} CSS selector(s) detected — styles should render correctly\n"
    if media_queries:
        result += f"{media_queries} media query(ies) detected — responsive layout should adapt correctly\n"
 
    return result if result else "No significant CSS rules found.\n"
 
 
# =========================
# MAIN ENTRY
# =========================
def analyze_code_file(code, filename):
    if not code or not code.strip():
        return f"File '{filename}' is empty or unreadable.\n"
 
    filename_lower = filename.lower()
 
    try:
        if filename_lower.endswith(".py"):
            return analyze_python(code)
 
        elif filename_lower.endswith(".java"):
            return analyze_java(code)
 
        elif filename_lower.endswith(".js"):
            return analyze_js(code)
 
        elif filename_lower.endswith(".html") or filename_lower.endswith(".htm"):
            return analyze_html(code)
 
        elif filename_lower.endswith(".css"):
            return analyze_css(code)
 
        else:
            return f"Generic execution expected for file: {filename}\n"
 
    except Exception as e:
        return f"Error analyzing '{filename}': {str(e)}\n"