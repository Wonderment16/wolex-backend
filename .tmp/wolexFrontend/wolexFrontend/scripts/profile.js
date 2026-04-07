const form = document.getElementById("profile-form");
const errorBox = document.getElementById("profile-error");

form.addEventListener("submit", async (e) => {

  e.preventDefault();

  const token = localStorage.getItem("access");

  const dob = document.getElementById("dob").value;
  const job = document.getElementById("job").value;
  const photo = document.getElementById("photo").files[0];

  const formData = new FormData();
  formData.append("dob", dob);
  formData.append("job", job);

  if (photo) {
    formData.append("photo", photo);
  }

  try {

    const response = await fetch("http://127.0.0.1:8000/accounts/profile/", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      errorBox.textContent = "Could not save profile.";
      return;
    }

    window.location.href = "dashboard.html";

  } catch (err) {

    errorBox.textContent = "Server connection failed.";

  }

});