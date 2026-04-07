console.log("Wolex landing page loaded");

const reveals = document.querySelectorAll(".reveal");

function revealOnScroll() {
    const windowHeight = window.innerHeight;

    reveals.forEach((item) => {
    const elementTop = item.getBoundingClientRect().top;
    const visiblePoint = 100;

        if (elementTop < windowHeight - visiblePoint) {
            item.classList.add("active");
    }
});
}

window.addEventListener("scroll", revealOnScroll);
window.addEventListener("load", revealOnScroll);