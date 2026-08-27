const API_URL = "http://127.0.0.1:8000";

const loginForm = document.getElementById("loginForm");
const resumeForm = document.getElementById("resumeForm");

const loginResult = document.getElementById("loginResult");
const uploadResult = document.getElementById("uploadResult");
const securityResult = document.getElementById("securityResult");

function showError(element, message) {
    element.textContent = `Error: ${message}`;
    element.className = "message error";
}

function showSuccess(element, message) {
    element.textContent = message;
    element.className = "message success";
}

async function readResponse(response) {
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "The server returned an error.");
    }

    return data;
}


loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    loginResult.textContent = "Processing login...";
    loginResult.className = "message";

    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    const formData = new FormData();
    formData.append("email", email);
    formData.append("password", password);

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: "POST",
            body: formData
        });

        const result = await readResponse(response);

        if (result.status === "success") {
            showSuccess(loginResult, result.message);
        } else {
            showError(loginResult, result.message);
        }
    } catch (error) {
        showError(loginResult, error.message);
    }
});


resumeForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    uploadResult.textContent = "Uploading resume...";
    uploadResult.className = "message";

    const email = document.getElementById("resumeEmail").value;
    const fileInput = document.getElementById("resumeFile");

    if (!fileInput.files.length) {
        showError(uploadResult, "Please select a resume file.");
        return;
    }

    const formData = new FormData();
    formData.append("email", email);
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch(`${API_URL}/upload-resume`, {
            method: "POST",
            body: formData
        });

        const result = await readResponse(response);

        if (result.status === "success") {
            showSuccess(
                uploadResult,
                `${result.message}. Stored file: ${result.stored_filename}`
            );
        } else {
            showError(uploadResult, result.reason);
        }
    } catch (error) {
        showError(uploadResult, error.message);
    }
});


document.getElementById("logsButton").addEventListener("click", async function () {
    securityResult.textContent = "Loading activity logs...";

    try {
        const response = await fetch(`${API_URL}/logs`);
        const result = await readResponse(response);

        securityResult.textContent = JSON.stringify(result, null, 2);
    } catch (error) {
        securityResult.textContent = `Error: ${error.message}`;
    }
});


document.getElementById("analyzeButton").addEventListener("click", async function () {
    securityResult.textContent = "Analyzing logs...";

    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: "POST"
        });

        const result = await readResponse(response);

        securityResult.textContent = JSON.stringify(result, null, 2);
    } catch (error) {
        securityResult.textContent = `Error: ${error.message}`;
    }
});


document.getElementById("alertsButton").addEventListener("click", async function () {
    securityResult.textContent = "Loading alerts...";

    try {
        const response = await fetch(`${API_URL}/alerts`);
        const result = await readResponse(response);

        securityResult.textContent = JSON.stringify(result, null, 2);
    } catch (error) {
        securityResult.textContent = `Error: ${error.message}`;
    }
});