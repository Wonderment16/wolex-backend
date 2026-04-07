console.log("Signup script loaded.");

const signupForm = document.getElementById("signup-form");
const errorBox = document.getElementById("signup-error");

signupForm.addEventListener("submit", async function (e) {

    e.preventDefault();

    errorBox.textContent = "";

    const firstName = document.getElementById("first_name").value.trim();
    const lastName = document.getElementById("last_name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const confirmPassword = document.getElementById("confirm-password").value.trim();

    if (password !== confirmPassword) {
        errorBox.textContent = "Passwords do not match.";
        return;
    }

    try {

        const response = await fetch("http://127.0.0.1:8000/api/auth/register/", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                first_name: firstName,
            /*    last_name: lastName, */
                email: email,
                password: password
            })

        });

        const data = await response.json();

        if (!response.ok) {

            errorBox.textContent = data.detail || "Signup failed.";
            return;
        }

        console.log("Signup success:", data);

        alert("Account created successfully!");

        window.location.href = "login.html";

    } catch (error) {

        console.error(error);

        errorBox.textContent = "Server connection failed.";

    }

});
