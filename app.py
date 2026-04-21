import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
 
from ai_model import (
    generate_test_cases_from_description,
    generate_test_cases_from_code,
    generate_test_cases_from_pdf,
    validate_code_logic,
)
from file_parser import extract_text_from_pdf
from pdf_generator import create_pdf
from email_sender import send_email
from test_executor import execute_tests
 
app = Flask(__name__)
CORS(app)
 
 
@app.route('/')
def home():
    return "AI Testing System Running"
 
 
# ── DESCRIPTION INPUT ──────────────────────────────────────────────────────────
@app.route('/generate-tests', methods=['POST'])
def generate_tests():
    data = request.get_json()
 
    if not data or "description" not in data:
        return jsonify({"error": "Missing 'description' field"}), 400
 
    text = data.get("description", "").strip()
    if not text:
        return jsonify({"error": "Description is empty"}), 400
 
    try:
        tests = generate_test_cases_from_description(text)
        if not tests:
            return jsonify({"error": "No test cases generated. Try a more detailed description."}), 400
        return jsonify({"test_cases": tests})
    except Exception as e:
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500
 
 
# ── PDF / SRS UPLOAD ───────────────────────────────────────────────────────────
@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
 
        file = request.files['file']
 
        if file.filename == '':
            return jsonify({"error": "Empty file name"}), 400
 
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Only PDF files are supported"}), 400
 
        text = extract_text_from_pdf(file)
 
        if not text or not text.strip() or text.startswith("Error") or text == "No readable text found":
            return jsonify({"error": "Could not extract text from PDF. Ensure it contains readable text."}), 400
 
        tests = generate_test_cases_from_pdf(text)
        if not tests:
            return jsonify({"error": "No test cases could be generated from this document."}), 400
 
        return jsonify({"test_cases": tests})
 
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
# ── CODE FILE UPLOAD ───────────────────────────────────────────────────────────
@app.route('/upload-code', methods=['POST'])
def upload_code():
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No files uploaded"}), 400
 
        files = request.files.getlist('files')
        if not files:
            return jsonify({"error": "No files selected"}), 400
 
        files_dict = {}
        uploaded_names = []
        syntax_errors = []
 
        for file in files:
            if file.filename == '':
                continue
            code = file.read().decode('utf-8', errors='ignore')
            if not code.strip():
                continue
 
            # ── Syntax validation for Python files ──────────────────────────
            if file.filename.lower().endswith('.py'):
                try:
                    import ast
                    ast.parse(code)
                except SyntaxError as e:
                    syntax_errors.append({
                        "file": file.filename,
                        "line": e.lineno,
                        "column": e.offset,
                        "error": e.msg,
                        "text": e.text.strip() if e.text else None,
                        "detail": (
                            f"Line {e.lineno}"
                            + (f", column {e.offset}" if e.offset else "")
                            + f": {e.msg}"
                            + (f" → `{e.text.strip()}`" if e.text else "")
                        )
                    })
                    continue  # Skip this file — do not add to files_dict
 
            files_dict[file.filename] = code
            uploaded_names.append(file.filename)
 
        # ── If ANY file had a syntax error, reject the whole request ────────
        if syntax_errors:
            error_lines = []
            for se in syntax_errors:
                error_lines.append(
                    f"• {se['file']}: SyntaxError at {se['detail']}"
                )
            return jsonify({
                "error": "Cannot generate test cases — the uploaded code contains syntax errors. "
                         "Please fix the errors and re-upload.",
                "syntax_errors": syntax_errors,
                "error_summary": "\n".join(error_lines)
            }), 422
 
        if not files_dict:
            return jsonify({"error": "No readable content found in uploaded files"}), 400
 
        # ── Logic validation — catch bugs before generating test cases ───────
        logic_errors = validate_code_logic(files_dict)
        if logic_errors:
            error_lines = []
            for le in logic_errors:
                loc = f" (line {le['line']})" if le.get('line') else ""
                error_lines.append(
                    f"• [{le['file']}{loc}] {le['issue']}: {le['detail']}"
                    + (f"\n  Code: `{le['code_snippet']}`" if le.get('code_snippet') else "")
                )
            return jsonify({
                "error": "Cannot generate test cases — the uploaded code contains logic errors. "
                         "Please fix the errors and re-upload.",
                "logic_errors": logic_errors,
                "error_summary": "\n".join(error_lines)
            }), 422
 
        tests = generate_test_cases_from_code(files_dict)
        if not tests:
            return jsonify({"error": "No test cases could be generated from the uploaded code."}), 400
 
        return jsonify({"test_cases": tests, "files": uploaded_names})
 
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
# ── RUN TESTS — AI analyses real code against each test case ──────────────────
@app.route('/run-tests', methods=['POST'])
def run_tests_endpoint():
    """
    Accept test cases + optional source code files.
    The AI reads the actual code and determines pass/fail for every test case
    based on what is really implemented.
 
    Accepts multipart/form-data:
      - test_cases  (JSON string, required)
      - files[]     (source code files, optional but strongly recommended)
 
    Also accepts application/json for backward compatibility:
      - { "test_cases": [...] }   (no code context — AI reasons from test titles only)
    """
    # ── Parse test cases ──────────────────────────────────────────────────────
    test_cases = []
    code_files = {}
 
    content_type = request.content_type or ""
 
    if "multipart/form-data" in content_type:
        # Multipart: test cases as JSON string field + code as file uploads
        tc_raw = request.form.get("test_cases", "").strip()
        if not tc_raw:
            return jsonify({"error": "Missing 'test_cases' field"}), 400
        try:
            test_cases = json_parse(tc_raw)
        except Exception:
            return jsonify({"error": "Invalid JSON in 'test_cases' field"}), 400
 
        # Read uploaded source files
        for file in request.files.getlist("files"):
            if file.filename:
                code = file.read().decode("utf-8", errors="ignore")
                if code.strip():
                    code_files[file.filename] = code
 
    else:
        # JSON body — no code files (backward compat)
        data = request.get_json()
        if not data or "test_cases" not in data:
            return jsonify({"error": "Missing 'test_cases' field"}), 400
        test_cases = data.get("test_cases", [])
 
    if not test_cases:
        return jsonify({"error": "test_cases list is empty"}), 400
 
    try:
        results = execute_tests(test_cases, code_files)
        passed  = sum(1 for r in results if r["status"] == "Passed")
        failed  = len(results) - passed
 
        return jsonify({
            "results": results,
            "summary": {
                "total":     len(results),
                "passed":    passed,
                "failed":    failed,
                "pass_rate": round((passed / len(results)) * 100, 1) if results else 0,
            }
        })
    except Exception as e:
        return jsonify({"error": f"Execution failed: {str(e)}"}), 500
 
 
# ── PDF DOWNLOAD ───────────────────────────────────────────────────────────────
@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    data = request.get_json()
 
    if not data or "test_cases" not in data:
        return jsonify({"error": "Missing 'test_cases' field"}), 400
 
    try:
        pdf_bytes = create_pdf(data.get("test_cases", []))
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='testcases.pdf'
        )
    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500
 
 
# ── SEND EMAIL ─────────────────────────────────────────────────────────────────
@app.route('/send-email', methods=['POST'])
def email():
    data = request.get_json()
 
    if not data:
        return jsonify({"error": "No data provided"}), 400
 
    receiver   = data.get("email", "").strip()
    test_cases = data.get("test_cases", [])
 
    if not receiver:
        return jsonify({"error": "Missing recipient email"}), 400
    if not test_cases:
        return jsonify({"error": "No test cases provided"}), 400
 
    try:
        pdf_bytes = create_pdf(test_cases)
        send_email(receiver, pdf_bytes)
        return jsonify({"message": f"Email sent successfully to {receiver}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
# ── HELPERS ────────────────────────────────────────────────────────────────────
import json as _json
 
def json_parse(s):
    return _json.loads(s)
 
 
if __name__ == '__main__':
    app.run(debug=True)
    