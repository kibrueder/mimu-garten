/*! Mimu Garten static clone — Elementor nav + Swiper carousels */
(function () {
  function updateMobileDropdownPosition(btn) {
    var widget = btn.closest(".elementor-nav-menu--stretch");
    if (!widget) return;
    var dropdown = btn.nextElementSibling;
    if (!dropdown || !dropdown.classList.contains("elementor-nav-menu__container")) return;

    if (window.matchMedia("(min-width: 1025px)").matches) {
      ["top", "max-height"].forEach(function (prop) {
        dropdown.style.removeProperty(prop);
      });
      widget.style.removeProperty("--menu-height");
      return;
    }

    var rect = btn.getBoundingClientRect();
    dropdown.style.top = rect.bottom + "px";
    dropdown.style.maxHeight = "calc(100vh - " + rect.bottom + "px)";
  }

  function setMenuHeight(btn) {
    var widget = btn.closest(".elementor-widget-nav-menu");
    var dropdown = btn.nextElementSibling;
    if (!widget || !dropdown) return;
    var available = window.innerHeight - btn.getBoundingClientRect().bottom;
    widget.style.setProperty("--menu-height", Math.min(dropdown.scrollHeight, available) + "px");
  }

  function toggleMenu(btn) {
    var widget = btn.closest(".elementor-widget-nav-menu");
    if (!widget) return;
    var open = !btn.classList.contains("elementor-active");
    btn.classList.toggle("elementor-active", open);
    widget.classList.toggle("elementor-active", open);
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    var dropdown = btn.nextElementSibling;
    if (dropdown && dropdown.classList.contains("elementor-nav-menu__container")) {
      dropdown.setAttribute("aria-hidden", open ? "false" : "true");
      updateMobileDropdownPosition(btn);
      if (open) setMenuHeight(btn);
    }
  }

  function closeMenus(exceptBtn) {
    document.querySelectorAll(".elementor-menu-toggle.elementor-active").forEach(function (btn) {
      if (btn !== exceptBtn) {
        btn.classList.remove("elementor-active");
        var widget = btn.closest(".elementor-widget-nav-menu");
        if (widget) widget.classList.remove("elementor-active");
        btn.setAttribute("aria-expanded", "false");
        var dropdown = btn.nextElementSibling;
        if (dropdown) dropdown.setAttribute("aria-hidden", "true");
        updateMobileDropdownPosition(btn);
      }
    });
  }

  function initMenus() {
    document.querySelectorAll(".elementor-menu-toggle").forEach(function (btn) {
      if (btn.dataset.mimuBound) return;
      btn.dataset.mimuBound = "1";
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (!btn.classList.contains("elementor-active")) closeMenus(btn);
        toggleMenu(btn);
      });
      btn.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          toggleMenu(btn);
        }
      });
    });

    document.querySelectorAll(".menu-item-has-children > a.elementor-item").forEach(function (link) {
      if (link.dataset.mimuSubBound) return;
      link.dataset.mimuSubBound = "1";
      link.addEventListener("click", function (e) {
        if (window.matchMedia("(min-width: 1025px)").matches) return;
        var li = link.parentElement;
        if (!li || !li.classList.contains("menu-item-has-children")) return;
        if (li.closest(".elementor-nav-menu--dropdown")) {
          e.preventDefault();
          li.classList.toggle("mimu-submenu-open");
        }
      });
    });
  }

  function initSwipers() {
    if (typeof Swiper === "undefined") return;
    document.querySelectorAll(".elementor-main-swiper").forEach(function (el) {
      if (el.dataset.mimuSwiper) return;
      el.dataset.mimuSwiper = "1";
      var widget = el.closest(".elementor-widget-testimonial-carousel, .elementor-widget-carousel");
      var slides = el.querySelectorAll(".swiper-slide").length;
      var settings = {};
      if (widget && widget.getAttribute("data-settings")) {
        try {
          settings = JSON.parse(widget.getAttribute("data-settings").replace(/&quot;/g, '"'));
        } catch (err) {}
      }
      var spv = parseInt(settings.slides_per_view, 10) || 3;
      new Swiper(el, {
        slidesPerView: 1,
        spaceBetween: 20,
        loop: slides > spv,
        autoplay: settings.autoplay === "yes" ? { delay: parseInt(settings.autoplay_speed, 10) || 5000, disableOnInteraction: false } : false,
        pagination: { el: el.querySelector(".swiper-pagination"), clickable: true },
        breakpoints: {
          768: { slidesPerView: Math.min(2, slides), spaceBetween: 10 },
          1025: { slidesPerView: Math.min(spv, slides), spaceBetween: 20 },
        },
      });
    });
  }

  function initContactForms() {
    document.querySelectorAll("form.elementor-form").forEach(function (form) {
      if (form.dataset.mimuMailto) return;
      form.dataset.mimuMailto = "1";
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var data = new FormData(form);
        var name = String(data.get("form_fields[name]") || "").trim();
        var email = String(data.get("form_fields[email]") || "").trim();
        var phone = String(data.get("form_fields[field_551bb03]") || "").trim();
        var message = String(data.get("form_fields[message]") || "").trim();
        var nl = (document.documentElement.lang || "").toLowerCase().indexOf("nl") === 0;
        if (!email) {
          alert(nl ? "Vul uw e-mailadres in." : "Bitte geben Sie Ihre E-Mail-Adresse ein.");
          return;
        }
        if (!message) {
          alert(nl ? "Vul uw bericht in." : "Bitte geben Sie Ihre Nachricht ein.");
          return;
        }
        var subject = nl ? "Contactaanvraag mimugarten.nl" : "Kontaktanfrage mimugarten.nl";
        var lines = [];
        if (name) lines.push((nl ? "Naam: " : "Name: ") + name);
        lines.push((nl ? "E-mail: " : "E-Mail: ") + email);
        if (phone) lines.push((nl ? "Telefoon: " : "Telefon: ") + phone);
        lines.push("");
        lines.push(message);
        window.location.href =
          "mailto:info@mimugarten.nl?subject=" +
          encodeURIComponent(subject) +
          "&body=" +
          encodeURIComponent(lines.join("\n"));
      });
    });
  }

  function initLangSwitcher() {
    document.querySelectorAll(".trp-language-switcher .trp-language-item").forEach(function (a) {
      try {
        var u = new URL(a.href, window.location.origin);
        u.search = "";
        a.href = u.pathname + u.hash;
      } catch (err) {}
    });
  }

  function initAccordions() {
    document.querySelectorAll(".e-n-accordion").forEach(function (accordion) {
      var widget = accordion.closest(".elementor-widget-n-accordion");
      var settings = {};
      if (widget && widget.getAttribute("data-settings")) {
        try {
          settings = JSON.parse(widget.getAttribute("data-settings").replace(/&quot;/g, '"'));
        } catch (err) {}
      }
      var oneOnly = settings.max_items_expended === "one";
      var items = accordion.querySelectorAll("details.e-n-accordion-item");

      items.forEach(function (details) {
        if (details.dataset.mimuAccordionBound) return;
        details.dataset.mimuAccordionBound = "1";

        var summary = details.querySelector("summary.e-n-accordion-item-title");
        if (summary) {
          summary.setAttribute("aria-expanded", details.open ? "true" : "false");
        }

        details.addEventListener("toggle", function () {
          if (summary) {
            summary.setAttribute("aria-expanded", details.open ? "true" : "false");
          }
          if (details.open && oneOnly) {
            items.forEach(function (other) {
              if (other !== details) other.open = false;
            });
          }
        });
      });
    });
  }

  function boot() {
    initMenus();
    initAccordions();
    initContactForms();
    initLangSwitcher();
    initSwipers();
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".elementor-widget-nav-menu")) closeMenus();
    });
    window.addEventListener("resize", repositionOpenMenus);
    window.addEventListener("scroll", repositionOpenMenus, { passive: true });
  }

  function repositionOpenMenus() {
    document.querySelectorAll(".elementor-menu-toggle.elementor-active").forEach(function (btn) {
      updateMobileDropdownPosition(btn);
      setMenuHeight(btn);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
