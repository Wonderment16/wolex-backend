console.log("Login script loaded");

const loginForm = document.getElementById("login-form");
const errorBox = document.getElementById("login-error");

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    console.log("Form submitted, attempting login...");

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("http://127.0.0.1:8000/api/auth/token/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + localStorage.getItem("token")
            },
            body: JSON.stringify({ email, password })
        });

        // 1. Check if the response is actually JSON before parsing
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            const text = await response.text(); // Get the HTML error for debugging
            console.error("Server returned non-JSON response:", text);
            errorBox.textContent = "Server error (Security/CSRF check failed)";
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            console.log("Login failed:", data);
            errorBox.textContent = data.detail || "Invalid email or password";
            return;
        }

        // 2. Success! Store tokens
        console.log("Login successful, tokens received.");
        localStorage.setItem("access", data.access);
        localStorage.setItem("refresh", data.refresh);
        
        // Redirect to dashboard
        window.location.href = "../pages/dashboard.html";

    } catch (error) {
        console.error("Fetch error:", error);
        errorBox.textContent = "Server connection failed";
    }
});