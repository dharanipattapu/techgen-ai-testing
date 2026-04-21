console.log("AI Testing Dashboard loaded");
 
let generatedTests = [];
 
// ── TAB SWITCHING ────────────────────────────────────────────────────────────
function openTab(tab) {
    ["desc", "srs", "code"].forEach(id => {
        document.getElementById(id).style.display = "none";
    });
    document.getElementById(tab).style.display = "block";
}
 
// ── STATUS BAR ───────────────────────────────────────────────────────────────
function showStatus(msg, type = "info") {
    const bar = document.getElementById("statusBar");
    bar.textContent = msg;
    bar.className = "status-bar " + type;
    bar.style.display = "block";
}
 
// ── ENABLE ACTION BUTTONS ────────────────────────────────────────────────────
function enableActionButtons() {
    document.getElementById("pdfBtn").disabled   = false;
    document.getElementById("emailBtn").disabled = false;
}
 
// ── DESCRIPTION → GENERATE ──────────────────────────────────────────────────
function generateTests() {
    const text = document.getElementById("inputText").value.trim();
    if (!text) { alert("Please enter a system description first."); return; }
 
    showStatus("⏳ AI is generating test cases… this may take a few seconds.", "info");
 
    fetch("http://127.0.0.1:5000/generate-tests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: text })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) { showStatus("❌ " + data.error, "error"); return; }
        display(data.test_cases);
        showStatus(`✅ ${data.test_cases.length} test cases generated.`, "success");
    })
    .catch(() => showStatus("❌ Backend not responding. Start Flask with: python app.py", "error"));
}
 
// ── PDF UPLOAD → GENERATE ────────────────────────────────────────────────────
function uploadPDF() {
    const file = document.getElementById("pdfFile").files[0];
    if (!file) { alert("Please select a PDF file first."); return; }
    if (!file.name.toLowerCase().endsWith(".pdf")) { alert("Only PDF files are supported."); return; }
 
    const fd = new FormData();
    fd.append("file", file);
 
    showStatus("⏳ Parsing PDF… AI is generating test cases.", "info");
 
    fetch("http://127.0.0.1:5000/upload-pdf", { method: "POST", body: fd })
    .then(r => r.json())
    .then(data => {
        if (data.error) { showStatus("❌ " + data.error, "error"); return; }
        display(data.test_cases);
        showStatus(`✅ ${data.test_cases.length} test cases generated from PDF.`, "success");
    })
    .catch(() => showStatus("❌ Upload failed. Make sure Flask is running.", "error"));
}
 
// ── CODE UPLOAD → GENERATE ───────────────────────────────────────────────────
function uploadCode() {
    const files = document.getElementById("codeFile").files;
    if (!files || files.length === 0) { alert("Please select at least one code file."); return; }
 
    const fd = new FormData();
    const names = [];
    for (let i = 0; i < files.length; i++) {
        fd.append("files", files[i]);
        names.push(files[i].name);
    }
 
    showUploadedFiles(names);
    showStatus("⏳ AI is reading your code and generating test cases…", "info");
 
    fetch("http://127.0.0.1:5000/upload-code", { method: "POST", body: fd })
    .then(r => r.json())
    .then(data => {
        if (data.error) { showStatus("❌ " + data.error, "error"); return; }
        display(data.test_cases);
        showStatus(`✅ ${data.test_cases.length} test cases generated from ${data.files.length} file(s).`, "success");
    })
    .catch(() => showStatus("❌ Upload failed. Make sure Flask is running.", "error"));
}
 
function showUploadedFiles(files) {
    const div = document.getElementById("uploadedFiles");
    div.innerHTML = "<h4>📂 Uploaded Files:</h4><ul>" +
        files.map(f => `<li>${f}</li>`).join("") + "</ul>";
}
 
// ── DOWNLOAD PDF — receives binary blob, triggers browser save ───────────────
function downloadPDF() {
    if (!generatedTests.length) { alert("No test cases to export."); return; }
 
    showStatus("⏳ Generating PDF…", "info");
 
    fetch("http://127.0.0.1:5000/download-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ test_cases: generatedTests })
    })
    .then(res => {
        if (!res.ok) return res.json().then(d => { throw new Error(d.error || "PDF failed"); });
        return res.blob();
    })
    .then(blob => {
        const url = URL.createObjectURL(blob);
        const a   = document.createElement("a");
        a.href     = url;
        a.download = "testcases.pdf";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showStatus("✅ PDF downloaded.", "success");
    })
    .catch(err => showStatus("❌ " + err.message, "error"));
}
 
// ── EMAIL MODAL ──────────────────────────────────────────────────────────────
function openEmailModal()  { document.getElementById("emailModal").style.display = "flex"; }
function closeEmailModal() { document.getElementById("emailModal").style.display = "none"; }
 
function sendEmail() {
    const email = document.getElementById("emailInput").value.trim();
    if (!email || !email.includes("@")) { alert("Enter a valid email address."); return; }
    if (!generatedTests.length) { alert("Generate test cases first."); return; }
 
    showStatus("⏳ Sending email…", "info");
    closeEmailModal();
 
    // Send test_cases directly — server generates PDF and emails it
    fetch("http://127.0.0.1:5000/send-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, test_cases: generatedTests })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) { showStatus("❌ " + data.error, "error"); return; }
        showStatus("✅ " + data.message, "success");
    })
    .catch(() => showStatus("❌ Failed to send email.", "error"));
}
 
// ── RENDER TABLE ─────────────────────────────────────────────────────────────
function display(tests) {
    if (!tests || !tests.length) {
        showStatus("⚠ No test cases returned. Try a more detailed input.", "error");
        return;
    }
 
    generatedTests = tests;
    const tbody = document.querySelector("#testTable tbody");
    tbody.innerHTML = "";
 
    tests.forEach((t, i) => {
        const cls = t.priority === "High" ? "high" : t.priority === "Medium" ? "medium" : "low";
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${i + 1}</td>
            <td>${t.title || "N/A"}</td>
            <td>${(t.steps || "").replace(/\n/g, "<br>")}</td>
            <td>${t.expected || "N/A"}</td>
            <td class="${cls}">${t.priority || "Low"}</td>
            <td>${t.type || "Functional"}</td>`;
        tbody.appendChild(row);
    });
 
    document.getElementById("testResults").style.display = "block";
    document.getElementById("testCount").textContent = tests.length + " tests";
    enableActionButtons();
}