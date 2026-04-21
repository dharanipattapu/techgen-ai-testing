# 🤖 AI Test Case Generator & Execution System

An intelligent full-stack application that automatically generates, analyzes, and executes software test cases using AI.

This system helps QA engineers and developers save time by converting:

* 📄 Text descriptions
* 📑 PDF/SRS documents
* 💻 Source code

into structured, high-quality test cases.

---

## 🚀 Features

### 🔹 Test Case Generation

* Generate test cases from **plain text descriptions**
* Extract and generate from **PDF/SRS documents**
* Analyze **source code (Python, JS, HTML, etc.)**
* Covers:

  * Functional
  * Edge cases
  * Error handling
  * Security scenarios

---

### 🔹 Code Analysis & Validation

* Detects **syntax errors** before processing
* Performs **logic validation**
* AI-based code understanding

---

### 🔹 Test Execution Engine

* Executes generated test cases against uploaded code
* Provides:

  * ✅ Pass/Fail results
  * 📊 Execution summary
  * 📌 Detailed reasoning

---

### 🔹 PDF Report Generation

* Generates professional reports with:

  * Test cases
  * Execution results
  * Statistics

---

### 🔹 Email Integration

* Send reports directly via email
* Supports PDF attachments

---

### 🔹 Modern UI Dashboard

* Interactive frontend (HTML, CSS, JS)
* Clean and responsive design
* Real-time status updates

---

## 🛠️ Tech Stack

### Backend

* Python (Flask)
* AI Model (Groq API - LLaMA 3)
* PDF Processing (pypdf)
* Report Generation (reportlab)

### Frontend

* HTML5
* CSS3
* JavaScript (Vanilla)

---

## 📂 Project Structure

```
techgen-ai-testing/
│
├── backend/
│   ├── app.py                # Main Flask backend
│   ├── ai_model.py           # AI test case generation logic
│   ├── code_analyzer.py      # Code structure analysis
│   ├── test_executor.py      # AI-based execution engine
│   ├── file_parser.py        # PDF text extraction
│   ├── pdf_generator.py      # Report creation
│   ├── email_sender.py       # Email integration
│   ├── requirements.txt      # Backend dependencies
│
├── frontend/
│   ├── index.html            # UI structure
│   ├── script.js             # Frontend logic
│   ├── style.css             # Styling
│
├── .gitignore
├── README.md
```

---

## ⚙️ Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/ai-test-case-generator.git
cd ai-test-case-generator
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Set environment variables

```bash
export GROQ_API_KEY=your_api_key
export EMAIL_ADDRESS=your_email@gmail.com
export EMAIL_PASSWORD=your_app_password
```

---

## ▶️ Run the Application

```bash
python app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

---

## 📸 Example Workflow

1. Enter system description OR upload code/PDF
2. Generate test cases using AI
3. Execute test cases
4. Download PDF report or send via email

---

## 🔐 Security Notes

* Never expose your API keys
* Use environment variables for credentials
* Gmail requires **App Password**, not your main password

---

## 📌 Future Enhancements

* CI/CD integration (GitHub Actions)
* Support for more languages
* Real-time test execution visualization
* Database integration for history tracking

---

## 🤝 Contributing

Pull requests are welcome!
For major changes, please open an issue first.

---

## 📄 License

This project is open-source and available under the MIT License.

---

## 👨‍💻 Author

Developed by **Dharani Sree**

---

⭐ If you like this project, give it a star!
