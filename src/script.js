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
  const tabsContainer = document.querySelector("[data-tabs]");
  const tabs = tabsContainer
    ? Array.from(tabsContainer.querySelectorAll(".portfolio-tab"))
    : [];
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let index = 0;
  let autoplayId;
  let currentFilter = "all";

  const visibleSlides = () =>
    slides.filter(
      (slide) => currentFilter === "all" || slide.dataset.category === currentFilter
    );

  const slidesPerView = () => {
    if (window.innerWidth >= 900) return 3;
    if (window.innerWidth >= 640) return 2;
    return 1;
  };

  const maxIndex = () => Math.max(0, visibleSlides().length - slidesPerView());

  const updateNavVisibility = () => {
    const showNav = maxIndex() > 0;
    [previousButton, nextButton].forEach((button) => {
      if (button) button.style.visibility = showNav ? "" : "hidden";
    });
  };

  const updateCarousel = () => {
    if (!track) return;
    const visible = visibleSlides();
    if (!visible.length) return;

    index = Math.min(index, maxIndex());
    const slide = visible[0];
    const gap = Number.parseFloat(getComputedStyle(track).gap) || 0;
    const offset = index * (slide.getBoundingClientRect().width + gap);
    track.style.transform = `translateX(-${offset}px)`;

    dotsContainer?.querySelectorAll("button").forEach((dot, dotIndex) => {
      dot.classList.toggle("active", dotIndex === index);
      dot.setAttribute("aria-current", dotIndex === index ? "true" : "false");
    });

    updateNavVisibility();
  };

  const goTo = (nextIndex) => {
    const max = maxIndex();
    index = nextIndex < 0 ? max : nextIndex > max ? 0 : nextIndex;
    updateCarousel();
  };

  const buildDots = () => {
    if (!dotsContainer) return;
    dotsContainer.innerHTML = "";

    const max = maxIndex();
    if (max <= 0) return;

    for (let dotIndex = 0; dotIndex <= max; dotIndex += 1) {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.setAttribute("aria-label", `Ver proyecto ${dotIndex + 1}`);
      dot.addEventListener("click", () => goTo(dotIndex));
      dotsContainer.append(dot);
    }
  };

  const applyFilter = (filter) => {
    currentFilter = filter;
    slides.forEach((slide) => {
      const match = filter === "all" || slide.dataset.category === filter;
      slide.style.display = match ? "" : "none";
    });
    index = 0;
    buildDots();
    updateCarousel();
    if (autoplayId) startAutoplay();
  };

  const startAutoplay = () => {
    if (prefersReducedMotion) return;
    window.clearInterval(autoplayId);
    if (maxIndex() <= 0) return;
    autoplayId = window.setInterval(() => goTo(index + 1), 4200);
  };

  previousButton?.addEventListener("click", () => goTo(index - 1));
  nextButton?.addEventListener("click", () => goTo(index + 1));

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const filter = tab.dataset.filter || "all";
      tabs.forEach((other) => {
        const isActive = other === tab;
        other.classList.toggle("active", isActive);
        other.setAttribute("aria-selected", String(isActive));
      });
      applyFilter(filter);
    });
  });

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

const packagesNav = document.querySelector("[data-packages-nav]");
const packagesCanvas = document.querySelector("[data-packages-canvas]");

if (packagesNav && packagesCanvas) {
  const navItems = Array.from(packagesNav.querySelectorAll(".packages-nav-item"));
  const capsules = Array.from(packagesCanvas.querySelectorAll(".packages-capsule"));

  const showPackage = (key) => {
    navItems.forEach((item) => {
      const isActive = item.dataset.package === key;
      item.classList.toggle("active", isActive);
      item.setAttribute("aria-selected", String(isActive));
    });
    capsules.forEach((capsule) => {
      capsule.classList.toggle("active", capsule.dataset.packageContent === key);
    });
  };

  navItems.forEach((item) => {
    item.addEventListener("click", () => {
      const key = item.dataset.package;
      if (key) showPackage(key);
    });
  });

  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (event) => {
      const href = anchor.getAttribute("href") || "";
      const id = href.slice(1);
      const target = navItems.find((item) => item.dataset.package === id);
      if (target) {
        event.preventDefault();
        showPackage(id);
        document
          .getElementById("paquetes")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });
}

const contactForm = document.querySelector("[data-contact-form]");

if (contactForm) {
  contactForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!contactForm.checkValidity()) {
      contactForm.reportValidity();
      return;
    }

    const data = new FormData(contactForm);
    const get = (key) => String(data.get(key) || "").trim();

    const lines = [
      "Hola LUMKO, me gustaría cotizar un proyecto.",
      "",
      `*Nombre:* ${get("nombre")}`,
      `*Teléfono:* ${get("telefono")}`,
    ];

    if (get("email")) lines.push(`*Email:* ${get("email")}`);
    lines.push(`*Producto de interés:* ${get("paquete")}`);
    lines.push(`*Presupuesto:* ${get("presupuesto")}`);
    if (get("plazo")) lines.push(`*Plazo:* ${get("plazo")}`);
    if (get("mensaje")) {
      lines.push("");
      lines.push(`*Detalles:* ${get("mensaje")}`);
    }

    const text = encodeURIComponent(lines.join("\n"));
    const phone = (contactForm.dataset.whatsapp || "").replace(/\D/g, "");
    window.open(`https://wa.me/${phone}?text=${text}`, "_blank", "noopener");
  });
}
