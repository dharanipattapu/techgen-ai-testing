import smtplib
import os
from email.message import EmailMessage
 
# Configure before running:
#   export EMAIL_ADDRESS=yourgmail@gmail.com
#   export EMAIL_PASSWORD=your_16char_app_password   ← Gmail App Password, NOT account password
 
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
 
 
def send_email(
    receiver: str,
    pdf_bytes: bytes,
    subject: str = "AI Generated Test Cases",
    filename: str = "testcases.pdf",
):
    """
    Send an email with a PDF attachment.
 
    Args:
        receiver:  Recipient email address.
        pdf_bytes: PDF content as bytes.
        subject:   Email subject line.
        filename:  Name of the attached PDF file.
    """
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise ValueError(
            "Email credentials not set. "
            "Run: export EMAIL_ADDRESS=you@gmail.com && export EMAIL_PASSWORD=xxxx"
        )
 
    if not receiver or "@" not in receiver:
        raise ValueError(f"Invalid recipient address: '{receiver}'")
 
    if not pdf_bytes:
        raise ValueError("PDF content is empty.")
 
    # Choose body text based on report type
    if "Execution" in subject or "execution" in filename:
        body_text = (
            "Hello,\n\n"
            "Please find attached the AI-powered test execution report.\n\n"
            "This report includes:\n"
            "  • Full pass/fail results for every test case\n"
            "  • AI analysis messages explaining each verdict\n"
            "  • Summary statistics (total, passed, failed, pass rate)\n"
            "  • Priority and type breakdowns\n\n"
            "Regards,\nTECHGEN AI Testing System"
        )
    else:
        body_text = (
            "Hello,\n\n"
            "Please find the AI-generated test cases attached as a PDF.\n\n"
            "Regards,\nTECHGEN AI Testing System"
        )
 
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From']    = EMAIL_ADDRESS
    msg['To']      = receiver
    msg.set_content(body_text)
    msg.add_attachment(
        pdf_bytes,
        maintype='application',
        subtype='pdf',
        filename=filename,
    )
 
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)