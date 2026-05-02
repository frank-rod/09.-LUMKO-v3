const menuButton = document.querySelector(".menu-toggle");
const menu = document.querySelector("[data-menu]");
const header = document.querySelector("[data-header]");

const updateHeaderState = () => {
  if (!header) return;
  const scrolled = window.scrollY > 8 || (menu && menu.classList.contains("open"));
  header.classList.toggle("is-scrolled", Boolean(scrolled));
};

window.addEventListener("scroll", updateHeaderState, { passive: true });
updateHeaderState();

if (menuButton && menu) {
  menuButton.addEventListener("click", () => {
    const isOpen = menu.classList.toggle("open");
    menuButton.setAttribute("aria-expanded", String(isOpen));
    updateHeaderState();
  });

  menu.addEventListener("click", (event) => {
    if (event.target instanceof HTMLAnchorElement) {
      menu.classList.remove("open");
      menuButton.setAttribute("aria-expanded", "false");
      updateHeaderState();
    }
  });
}

const revealItems = document.querySelectorAll(".reveal");

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.16 }
  );

  revealItems.forEach((item) => observer.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}

const carousel = document.querySelector("[data-carousel]");

if (carousel) {
  const track = carousel.querySelector("[data-track]");
  const slides = Array.from(carousel.querySelectorAll(".project-card"));
  const previousButton = carousel.querySelector("[data-prev]");
  const nextButton = carousel.querySelector("[data-next]");
  const dotsContainer = carousel.querySelector("[data-dots]");
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let index = 0;
  let autoplayId;

  const slidesPerView = () => {
    if (window.innerWidth >= 900) return 3;
    if (window.innerWidth >= 640) return 2;
    return 1;
  };

  const maxIndex = () => Math.max(0, slides.length - slidesPerView());

  const updateCarousel = () => {
    if (!track || !slides.length) return;

    index = Math.min(index, maxIndex());
    const slide = slides[0];
    const gap = Number.parseFloat(getComputedStyle(track).gap) || 0;
    const offset = index * (slide.getBoundingClientRect().width + gap);
    track.style.transform = `translateX(-${offset}px)`;

    dotsContainer?.querySelectorAll("button").forEach((dot, dotIndex) => {
      dot.classList.toggle("active", dotIndex === index);
      dot.setAttribute("aria-current", dotIndex === index ? "true" : "false");
    });
  };

  const goTo = (nextIndex) => {
    index = nextIndex < 0 ? maxIndex() : nextIndex > maxIndex() ? 0 : nextIndex;
    updateCarousel();
  };

  const buildDots = () => {
    if (!dotsContainer) return;
    dotsContainer.innerHTML = "";

    for (let dotIndex = 0; dotIndex <= maxIndex(); dotIndex += 1) {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.setAttribute("aria-label", `Ver proyecto ${dotIndex + 1}`);
      dot.addEventListener("click", () => goTo(dotIndex));
      dotsContainer.append(dot);
    }
  };

  const startAutoplay = () => {
    if (prefersReducedMotion) return;
    window.clearInterval(autoplayId);
    autoplayId = window.setInterval(() => goTo(index + 1), 4200);
  };

  previousButton?.addEventListener("click", () => goTo(index - 1));
  nextButton?.addEventListener("click", () => goTo(index + 1));

  carousel.addEventListener("mouseenter", () => window.clearInterval(autoplayId));
  carousel.addEventListener("mouseleave", startAutoplay);
  carousel.addEventListener("focusin", () => window.clearInterval(autoplayId));
  carousel.addEventListener("focusout", startAutoplay);

  window.addEventListener("resize", () => {
    buildDots();
    updateCarousel();
  });

  buildDots();
  updateCarousel();
  startAutoplay();
}
