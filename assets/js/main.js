(() => {
  const header = document.querySelector(".site-header");
  const toggle = document.querySelector(".nav-toggle");
  if (header && toggle) {
    toggle.addEventListener("click", () => {
      const open = header.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  document.querySelectorAll(".has-submenu > a").forEach((a) => {
    a.addEventListener("click", (e) => {
      if (window.matchMedia("(max-width: 960px)").matches) {
        const li = a.parentElement;
        if (li.classList.contains("has-submenu")) {
          e.preventDefault();
          li.classList.toggle("is-open");
        }
      }
    });
  });

  const banner = document.querySelector("[data-cookie-banner]");
  if (banner) {
    const key = "mimu_cookie_consent";
    if (!localStorage.getItem(key)) banner.hidden = false;
    banner.querySelector("[data-cookie-accept]")?.addEventListener("click", () => {
      localStorage.setItem(key, "accepted");
      banner.hidden = true;
    });
    banner.querySelector("[data-cookie-reject]")?.addEventListener("click", () => {
      localStorage.setItem(key, "rejected");
      banner.hidden = true;
    });
  }
})();
