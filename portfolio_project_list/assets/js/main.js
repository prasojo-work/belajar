/* ==========================================================================
   Interaksi kecil: menu mobile, header saat scroll, dan reveal on scroll.
   Tanpa library — cukup buka index.html di browser.
   ========================================================================== */
(function () {
  "use strict";

  var header = document.querySelector(".site-header");
  var nav = document.getElementById("nav");
  var toggle = document.querySelector(".menu-toggle");
  var main = document.getElementById("main");
  var footer = document.querySelector(".footer");

  /* --- Header: beri latar setelah halaman digulir ------------------------ */
  var ticking = false;

  function updateHeader() {
    header.classList.toggle("is-scrolled", window.scrollY > 16);
    ticking = false;
  }

  window.addEventListener(
    "scroll",
    function () {
      if (!ticking) {
        window.requestAnimationFrame(updateHeader);
        ticking = true;
      }
    },
    { passive: true }
  );
  updateHeader();

  /* --- Menu mobile ------------------------------------------------------- */
  function setNav(open) {
    if (!nav || !toggle) return;

    nav.classList.toggle("is-open", open);
    document.body.classList.toggle("nav-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Tutup menu" : "Buka menu");

    /* Cegah konten di belakang menu ikut menerima fokus keyboard. */
    if (main) main.inert = open;
    if (footer) footer.inert = open;
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      setNav(!nav.classList.contains("is-open"));
    });

    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        setNav(false);
      });
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        setNav(false);
        toggle.focus();
      }
    });

    var desktop = window.matchMedia("(min-width: 821px)");
    var onChange = function (event) {
      if (event.matches) setNav(false);
    };

    if (desktop.addEventListener) {
      desktop.addEventListener("change", onChange);
    } else if (desktop.addListener) {
      desktop.addListener(onChange);
    }
  }

  /* --- Reveal saat elemen masuk viewport --------------------------------- */
  var reveals = document.querySelectorAll(".reveal");

  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );

    reveals.forEach(function (element) {
      observer.observe(element);
    });
  } else {
    reveals.forEach(function (element) {
      element.classList.add("is-visible");
    });
  }

  /* --- Tahun di footer --------------------------------------------------- */
  var year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());
})();
