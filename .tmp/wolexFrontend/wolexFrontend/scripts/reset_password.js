console.log("Reset password script loaded");

const form = document.getElementById("reset-form");
const message = document.getElementById("reset-message");

const params = new URLSearchParams(window.location.search);
const uid = params.get("uid");
const token = params.get("token");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirm-password").value;

  // Basic password validation
  if (password.length < 8) {
    message.style.color = "red";
    message.textContent = "Password must be at least 8 characters long.";
    return;
  }

  if (password !== confirmPassword) {
    message.style.color = "red";
    message.textContent = "Passwords do not match.";
    return;
  }

  if (!uid || !token) {
  message.style.color = "red";
  message.textContent = "Invalid or broken reset link.";
  return;
}


  try {
    const response = await fetch("http://127.0.0.1:8000/api/auth/password-reset/confirm/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        uid,
        token,
        new_password: password
      })
    });

    const data = await response.json();

    if (response.ok) {
      message.style.color = "green";
      message.textContent = "Password reset successful.";
    } else {
      message.style.color = "red";
      message.textContent = data.error || data.errors || "Reset failed.";
    }
  } catch (error) {
    message.style.color = "red";
    message.textContent = "Something went wrong.";
  }
});






