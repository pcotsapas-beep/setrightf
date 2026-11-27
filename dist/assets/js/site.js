/* Set Right Flatwork LLC — site behaviour (no dependencies) */
(function () {
  "use strict";

  /* ---- Copyright year ---- */
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });

  /* ---- Mobile navigation ---- */
  var toggle = document.querySelector(".menu-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    var setOpen = function (open) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      nav.classList.toggle("is-open", open);
      document.body.classList.toggle("menu-open", open);
    };
    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) { setOpen(false); toggle.focus(); }
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth > 880 && nav.classList.contains("is-open")) setOpen(false);
    });
  }

  /* ---- Project gallery: filters ---- */
  var filterBar = document.querySelector("[data-filters]");
  var tiles = Array.prototype.slice.call(document.querySelectorAll(".masonry .tile"));
  if (filterBar && tiles.length) {
    filterBar.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-filter]");
      if (!btn) return;
      var f = btn.getAttribute("data-filter");
      filterBar.querySelectorAll("button").forEach(function (b) {
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
      var shown = 0;
      tiles.forEach(function (t) {
        var cats = (t.getAttribute("data-cat") || "").split(" ");
        var show = f === "all" || cats.indexOf(f) !== -1;
        t.hidden = !show;
        if (show) shown++;
      });
      var live = document.getElementById("filter-status");
      if (live) live.textContent = shown + (shown === 1 ? " image shown" : " images shown");
    });
  }

  /* ---- Project gallery: lightbox ---- */
  var lb = document.getElementById("lightbox");
  if (lb && tiles.length && typeof lb.showModal === "function") {
    var lbImg = lb.querySelector("img");
    var lbTitle = lb.querySelector("[data-lb-title]");
    var lbText = lb.querySelector("[data-lb-text]");
    var current = 0;
    var visible = function () { return tiles.filter(function (t) { return !t.hidden; }); };
    var show = function (tile) {
      var b = tile.querySelector("button");
      lbImg.src = b.getAttribute("data-full");
      lbImg.alt = tile.querySelector("img").alt;
      lbTitle.textContent = b.getAttribute("data-title");
      lbText.textContent = b.getAttribute("data-text");
    };
    tiles.forEach(function (tile) {
      tile.querySelector("button").addEventListener("click", function () {
        var v = visible(); current = v.indexOf(tile);
        show(tile); lb.showModal();
      });
    });
    var step = function (d) {
      var v = visible(); if (!v.length) return;
      current = (current + d + v.length) % v.length; show(v[current]);
    };
    lb.querySelector("[data-lb-prev]").addEventListener("click", function () { step(-1); });
    lb.querySelector("[data-lb-next]").addEventListener("click", function () { step(1); });
    lb.querySelector("[data-lb-close]").addEventListener("click", function () { lb.close(); });
    lb.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") step(-1);
      if (e.key === "ArrowRight") step(1);
    });
    lb.addEventListener("click", function (e) { if (e.target === lb) lb.close(); });
  } else if (tiles.length) {
    /* No <dialog> support: open the full image in the same tab instead */
    tiles.forEach(function (tile) {
      var b = tile.querySelector("button");
      b.addEventListener("click", function () { window.location.href = b.getAttribute("data-full"); });
    });
  }

  /* ---- Planning range calculator (Products page) ---- */
  var calc = document.getElementById("calc");
  if (calc) {
    var out = document.getElementById("calc-range");
    var area = document.getElementById("calc-area");
    var fmt = function (n) { return "$" + Math.round(n).toLocaleString("en-US"); };
    var run = function () {
      var opt = calc.service.options[calc.service.selectedIndex];
      var lo = parseFloat(opt.getAttribute("data-lo"));
      var hi = parseFloat(opt.getAttribute("data-hi"));
      var L = parseFloat(calc.length.value), W = parseFloat(calc.width.value);
      if (!(L > 0) || !(W > 0)) {
        out.textContent = "Enter length and width";
        area.textContent = "Use feet. For an L-shaped area, add the two rectangles separately.";
        return;
      }
      var sq = L * W;
      out.textContent = fmt(sq * lo) + " – " + fmt(sq * hi);
      area.textContent = Math.round(sq).toLocaleString("en-US") + " sq. ft. of " + opt.textContent.trim() + " at $" + lo + "–$" + hi + " per sq. ft.";
    };
    calc.addEventListener("input", run);
    calc.addEventListener("submit", function (e) { e.preventDefault(); run(); });
    run();
  }

  /* ---- Estimate request form ---- */
  var form = document.getElementById("estimate-form");
  if (form) {
    var status = document.getElementById("form-status");
    var endpoint = (form.getAttribute("data-endpoint") || "").trim();

    var setError = function (field, msg) {
      var input = form.elements[field];
      var err = document.getElementById(field + "-error");
      if (!input || !err) return;
      err.textContent = msg || "";
      if (msg) input.setAttribute("aria-invalid", "true"); else input.removeAttribute("aria-invalid");
    };

    var validate = function () {
      var ok = true, first = null;
      var need = function (name, test, msg) {
        var el = form.elements[name];
        var good = test(el);
        setError(name, good ? "" : msg);
        if (!good) { ok = false; if (!first) first = el; }
      };
      need("name", function (el) { return el.value.trim().length > 1; }, "Enter your full name.");
      need("email", function (el) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(el.value.trim()); }, "Enter an email address like name@example.com.");
      need("phone", function (el) { var d = el.value.replace(/\D/g, ""); return d.length === 0 || d.length >= 10; }, "Enter a 10-digit phone number, or leave this blank.");
      need("project_type", function (el) { return el.value !== ""; }, "Choose the type of project.");
      need("location", function (el) { return el.value.trim().length > 1; }, "Enter the project city or neighborhood.");
      need("description", function (el) { return el.value.trim().length >= 10; }, "Describe the project in a sentence or two.");
      need("consent", function (el) { return el.checked; }, "Check the box to let us use your details to respond.");
      if (first) first.focus();
      return ok;
    };

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      status.className = "form-status";
      status.textContent = "";
      if (!validate()) return;

      if (!endpoint) {
        /* No form backend is configured. Be honest: nothing was sent. */
        status.className = "form-status is-info";
        status.textContent = "Your details have not been sent: online requests are not connected yet. Please call 650-250-6345 or email info@setrightflatwork.com to request your free estimate. Your answers are still in the form if you want to refer to them on the call.";
        status.focus();
        return;
      }

      var btn = form.querySelector("button[type=submit]");
      btn.disabled = true;
      var label = btn.textContent;
      btn.textContent = "Sending…";
      fetch(endpoint, { method: "POST", body: new FormData(form), headers: { Accept: "application/json" } })
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          status.className = "form-status is-ok";
          status.textContent = "Request sent. Thank you — Set Right Flatwork will review your project details and get back to you.";
          form.reset();
        })
        .catch(function () {
          status.className = "form-status is-err";
          status.textContent = "Your request could not be sent. Please try again, call 650-250-6345, or email info@setrightflatwork.com.";
        })
        .then(function () { btn.disabled = false; btn.textContent = label; status.focus(); });
    });
  }
})();
