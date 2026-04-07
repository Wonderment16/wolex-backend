console.log("Forgot password script loaded");

const form = document.getElementById("forgot-form");
const message = document.getElementById("forgot-message");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value;

  // Basic email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    message.style.color = "red";
    message.textContent = "Please enter a valid email address.";
    return;
  }

  console.log("Submitting forgot password request for email:", email);

  try {
    const response = await fetch("http://127.0.0.1:8000/api/auth/password-reset/request/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email })
    });

    const data = await response.json();

    if (response.ok) {
      message.style.color = "green";
      message.textContent = data.message || "Reset email sent.";
    } else {
      message.style.color = "red";
      message.textContent = data.detail || "Request failed.";
    }

    } catch (error) {
      message.style.color = "red";
      message.textContent = "Server connection failed.";
    }
  });