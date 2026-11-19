/* Nepal Shipping & Sourcing — site script.
   No dependencies. No innerHTML: all dynamic text is set with textContent. */
(function () {
  "use strict";

  var doc = document.documentElement;
  doc.classList.remove("no-js");
  doc.classList.add("js");

  /* ---------- Mobile navigation ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  var desktop = window.matchMedia("(min-width: 62rem)");

  function setNav(open) {
    if (!toggle || !nav) return;
    toggle.setAttribute("aria-expanded", String(open));
    nav.setAttribute("data-open", String(open));
    toggle.querySelector(".nav-toggle__label").textContent = open ? "Close" : "Menu";
  }

  if (toggle && nav) {
    setNav(false);
    toggle.addEventListener("click", function () {
      setNav(toggle.getAttribute("aria-expanded") !== "true");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        setNav(false);
        toggle.focus();
      }
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setNav(false);
    });
    var onChange = function () { if (desktop.matches) setNav(false); };
    if (desktop.addEventListener) desktop.addEventListener("change", onChange);
  }

  /* ---------- Content review mode (?review) ---------- */
  var params;
  try { params = new URLSearchParams(window.location.search); } catch (e) { params = null; }
  if (params && params.has("review")) {
    doc.classList.add("review-mode");
    var count = document.querySelectorAll("[data-placeholder]").length;
    var banner = document.createElement("p");
    banner.className = "review-banner";
    banner.setAttribute("role", "status");
    banner.textContent = "Review mode: " + count + " item(s) on this page need confirmation before launch. " +
      "See COMPANY-CONTENT-CHECKLIST.md.";
    document.body.appendChild(banner);
  }

  /* ---------- Inquiry form (contact page) ---------- */
  var form = document.getElementById("inquiry-form");
  if (!form) return;

  var TOPICS = {
    "air-freight": "Air freight",
    "sea-freight": "Sea freight",
    "land-transport": "Land transport",
    "freight-forwarding": "Freight forwarding",
    "import-export": "Import and export assistance",
    "customs": "Customs coordination",
    "cargo-handling": "Cargo handling and packing",
    "sourcing": "Product sourcing",
    "other": "Something else"
  };

  var recipient = form.getAttribute("data-recipient") || "";
  var topicSelect = form.querySelector("#f-topic");
  var summary = document.getElementById("form-errors");
  var summaryList = summary ? summary.querySelector("ul") : null;
  var status = document.getElementById("form-status");
  var statusTitle = status ? status.querySelector("[data-status-title]") : null;
  var statusText = status ? status.querySelector("[data-status-text]") : null;
  var copyBtn = document.getElementById("copy-message");
  var lastMessage = "";

  // Preselect topic from ?topic=… (allowlisted keys only; anything else is ignored).
  if (params && topicSelect) {
    var t = params.get("topic");
    if (t && Object.prototype.hasOwnProperty.call(TOPICS, t)) topicSelect.value = t;
  }

  var EMAIL_RE = /^[^\s@<>()[\]\\,;:"]+@[^\s@<>()[\]\\,;:"]+\.[A-Za-z]{2,}$/;

  var rules = [
    { id: "f-name", test: function (v) { return v.length >= 2; }, msg: "Enter your name." },
    { id: "f-email", test: function (v) { return EMAIL_RE.test(v); }, msg: "Enter an email address in the format name@example.com." },
    { id: "f-topic", test: function (v) { return Object.prototype.hasOwnProperty.call(TOPICS, v); }, msg: "Choose what your inquiry is about." },
    { id: "f-message", test: function (v) { return v.length >= 20; }, msg: "Describe your shipment or product in at least 20 characters." }
  ];

  // Strip control characters (except newlines/tabs) and trim; cap length.
  function clean(value, max) {
    return String(value || "")
      .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "")
      .trim()
      .slice(0, max);
  }

  function field(id) { return document.getElementById(id); }

  function setError(input, message) {
    var err = document.getElementById(input.id + "-error");
    if (message) {
      input.setAttribute("aria-invalid", "true");
      if (err) err.textContent = message;
    } else {
      input.removeAttribute("aria-invalid");
      if (err) err.textContent = "";
    }
  }

  function validate() {
    var errors = [];
    rules.forEach(function (r) {
      var input = field(r.id);
      if (!input) return;
      var ok = r.test(clean(input.value, 2000));
      setError(input, ok ? "" : r.msg);
      if (!ok) errors.push({ input: input, msg: r.msg });
    });
    return errors;
  }

  function showSummary(errors) {
    if (!summary || !summaryList) return;
    while (summaryList.firstChild) summaryList.removeChild(summaryList.firstChild);
    if (!errors.length) { summary.hidden = true; return; }
    errors.forEach(function (e) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "#" + e.input.id;
      a.textContent = e.msg;
      a.addEventListener("click", function (ev) { ev.preventDefault(); e.input.focus(); });
      li.appendChild(a);
      summaryList.appendChild(li);
    });
    summary.hidden = false;
    summary.focus();
  }

  // After a failed submit, clear each field's error as soon as its value becomes
  // valid while the user types. Errors are only ever *added* on submit: changing
  // layout on blur would move the submit button between mousedown and mouseup
  // and swallow the click.
  var attempted = false;
  function clearIfValid(e) {
    if (!attempted || e.target.getAttribute("aria-invalid") !== "true") return;
    var rule = rules.filter(function (r) { return r.id === e.target.id; })[0];
    if (rule && rule.test(clean(e.target.value, 2000))) setError(e.target, "");
  }
  form.addEventListener("input", clearIfValid);
  form.addEventListener("change", clearIfValid);

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    attempted = true;

    // Honeypot: real visitors never see or fill this field.
    var trap = field("f-website");
    if (trap && trap.value) return;

    var errors = validate();
    showSummary(errors);
    if (errors.length) return;

    var name = clean(field("f-name").value, 100);
    var company = clean(field("f-company").value, 120);
    var email = clean(field("f-email").value, 160);
    var country = clean(field("f-country").value, 80);
    var topic = TOPICS[field("f-topic").value];
    var message = clean(field("f-message").value, 1500);

    var subject = "Website inquiry: " + topic + " (" + name + ")";
    var lines = [
      "Name: " + name,
      company ? "Company: " + company : null,
      "Email: " + email,
      country ? "Country: " + country : null,
      "Inquiry about: " + topic,
      "",
      message,
      "",
      "Sent from the inquiry form on the Nepal Shipping & Sourcing website."
    ].filter(function (l) { return l !== null; });
    lastMessage = "To: " + recipient + "\nSubject: " + subject + "\n\n" + lines.join("\n");

    var href = "mailto:" + recipient +
      "?subject=" + encodeURIComponent(subject) +
      "&body=" + encodeURIComponent(lines.join("\r\n"));

    if (status) {
      status.hidden = false;
      status.classList.remove("form-status--error");
      statusTitle.textContent = "Your email is ready to send";
      statusText.textContent = "Your email app should now show the message addressed to " + recipient +
        ". Check it and press send. If no email app opened, copy the message and send it from your usual email account.";
      status.focus();
    }
    window.location.href = href;
  });

  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      if (!lastMessage) return;
      var done = function () { copyBtn.textContent = "Message copied"; };
      var fail = function () {
        if (status) {
          status.classList.add("form-status--error");
          statusTitle.textContent = "Copy did not work in this browser";
          statusText.textContent = "Select your message in the form above, copy it, and email it to " + recipient + ".";
        }
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(lastMessage).then(done, fail);
      } else {
        fail();
      }
    });
  }
})();
