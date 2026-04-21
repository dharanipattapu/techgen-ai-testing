
try:
    from pypdf import PdfReader          # preferred (actively maintained)
except ImportError:
    from PyPDF2 import PdfReader         # fallback for older installs
 
 
def extract_text_from_pdf(file) -> str:
    """
    Extract all text from a PDF file object or file path.
 
    Args:
        file: A file-like object (e.g. from Flask request.files) or a file path string.
 
    Returns:
        Extracted text string, or an error message if extraction fails.
    """
    try:
        pdf = PdfReader(file)
 
        if len(pdf.pages) == 0:
            return "No readable text found"
 
        text = ""
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
 
        return text.strip() if text.strip() else "No readable text found"
 
    except Exception as e:
        return f"Error reading PDF: {str(e)}"