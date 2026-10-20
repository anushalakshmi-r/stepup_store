
document.addEventListener("DOMContentLoaded", function () {
    const slides = document.querySelectorAll(".hero-slide");
    const dots = document.querySelectorAll(".hero-dot");
    const prevButton = document.querySelector(".hero-prev");
    const nextButton = document.querySelector(".hero-next");
    const hero = document.querySelector(".hero-section");

    if (!slides.length || !dots.length || !hero) return;

    let currentSlide = 0;
    let carouselTimer;

    function showSlide(index) {
        currentSlide = (index + slides.length) % slides.length;

        slides.forEach((slide, i) => {
            slide.classList.toggle("active", i === currentSlide);
        });

        dots.forEach((dot, i) => {
            dot.classList.toggle("active", i === currentSlide);
        });
    }

    function startCarousel() {
        clearInterval(carouselTimer);
        carouselTimer = setInterval(() => {
            showSlide(currentSlide + 1);
        }, 4000);
    }

    dots.forEach((dot, index) => {
        dot.addEventListener("click", () => {
            showSlide(index);
            startCarousel();
        });
    });

    nextButton.addEventListener("click", () => {
        showSlide(currentSlide + 1);
        startCarousel();
    });

    prevButton.addEventListener("click", () => {
        showSlide(currentSlide - 1);
        startCarousel();
    });

    hero.addEventListener("mouseenter", () => {
        clearInterval(carouselTimer);
    });

    hero.addEventListener("mouseleave", startCarousel);

    showSlide(0);
    startCarousel();
});
