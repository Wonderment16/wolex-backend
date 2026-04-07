const form = document.querySelector(".auth-form");
const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirm-password");
const errorText = document.getElementById("password-error");

form.addEventListener("submit", function (e) {
  if (password.value !== confirmPassword.value) {
    e.preventDefault();
    errorText.textContent = "Passwords do not match.";
  } else {
    errorText.textContent = "";
  }
});

const photoInput = document.getElementById("photo");
const fileName = document.querySelector(".file-name");

photoInput.addEventListener("change", function(){
if(this.files.length > 0){
fileName.textContent = this.files[0].name;
}
});