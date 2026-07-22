(function () {
  "use strict";

  // Northstar Goods — Synthetic checkout demonstration (Resumable Wizard)
  // All state, storage, and totals below refer to fictional synthetic data only.
  //
  // Interaction model: a step-by-step wizard where exactly one step is the active
  // "primary task" at a time (named progress + a single active Continue control),
  // but a step that has already been completed stays reachable and editable rather
  // than being torn out of the page — a "resumable, progressively revealed" wizard.
  // Steps that have not yet been reached are hidden accessibly (aria-hidden, removed
  // from tab order, and visually collapsed) until the wizard journey reaches them.

  var STORAGE_KEY = "northstar-wizard-checkout-v1";

  var SAFE_FIELD_IDS = [
    "contact-name", "contact-email", "contact-phone",
    "address-line1", "address-city", "address-state", "address-postcode", "address-country"
  ];

  var STEP_FIELDS = {
    1: ["contact-name", "contact-email", "contact-phone"],
    2: ["address-line1", "address-city", "address-state", "address-postcode", "address-country"],
    3: ["card-number", "card-expiry", "card-security", "card-name"]
  };

  var FIELD_STEP = {};
  Object.keys(STEP_FIELDS).forEach(function (step) {
    STEP_FIELDS[step].forEach(function (id) { FIELD_STEP[id] = Number(step); });
  });

  var ALL_VALIDATABLE_FIELDS = STEP_FIELDS[1].concat(STEP_FIELDS[2], STEP_FIELDS[3]);

  var FOCUSABLE_SELECTOR = "button, input, select, textarea, a[href]";

  var state = {
    highestRevealed: 1,
    currentFocus: 1,
    orderPlaced: false
  };

  function $(selector) { return document.querySelector(selector); }
  function byId(id) { return document.getElementById(id); }
  function val(id) { var el = byId(id); return el ? el.value.trim() : ""; }

  function setStatus(text) {
    var region = $('[data-hook="status"]');
    if (region) region.textContent = text;
  }

  // --- Validation -----------------------------------------------------

  function fieldMessage(id, value) {
    switch (id) {
      case "contact-name":
        return value ? "" : "Enter your full name.";
      case "contact-email":
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? "" : "Enter a valid email address, like name@example.com.";
      case "contact-phone":
        return value.replace(/\D/g, "").length >= 7 ? "" : "Enter a valid phone number.";
      case "address-line1":
        return value ? "" : "Enter your street address.";
      case "address-city":
        return value ? "" : "Enter your city or suburb.";
      case "address-state":
        return value ? "" : "Enter your state or territory.";
      case "address-postcode":
        return /^\d{4}$/.test(value) ? "" : "Enter a 4-digit postcode.";
      case "address-country":
        return value ? "" : "Enter your country.";
      case "card-number":
        return /^\d{12,19}$/.test(value.replace(/\s+/g, "")) ? "" : "Enter a valid card number.";
      case "card-expiry":
        return /^(0[1-9]|1[0-2])\/\d{2}$/.test(value) ? "" : "Enter the expiry as MM/YY.";
      case "card-security":
        return /^\d{3,4}$/.test(value) ? "" : "Enter the 3 or 4 digit security code.";
      case "card-name":
        return value ? "" : "Enter the name on the card.";
      default:
        return "";
    }
  }

  function computeErrors(fieldIds) {
    var errors = [];
    fieldIds.forEach(function (id) {
      var msg = fieldMessage(id, val(id));
      if (msg) errors.push({ fieldId: id, stepNum: FIELD_STEP[id] || null, message: msg });
    });
    return errors;
  }

  function computeAllErrors() {
    var errors = computeErrors(ALL_VALIDATABLE_FIELDS);
    var shippingChecked = document.querySelector('input[name="shipping-method"]:checked');
    if (!shippingChecked) {
      errors.push({ fieldId: "shipping-standard", stepNum: null, message: "Choose a shipping method." });
    }
    var reviewBox = byId("review-confirmation");
    if (reviewBox && !reviewBox.checked) {
      errors.push({ fieldId: "review-confirmation", stepNum: 4, message: "Confirm you have reviewed your order before placing it." });
    }
    return errors;
  }

  function applyFieldState(id, message) {
    var el = byId(id);
    if (!el) return;
    var errorEl = byId(id + "-error");
    var helpId = id + "-help";
    if (message) {
      el.setAttribute("aria-invalid", "true");
      el.setAttribute("aria-describedby", helpId + " " + id + "-error");
      if (errorEl) { errorEl.textContent = message; errorEl.hidden = false; }
    } else {
      el.setAttribute("aria-invalid", "false");
      el.setAttribute("aria-describedby", helpId);
      if (errorEl) { errorEl.textContent = ""; errorEl.hidden = true; }
    }
  }

  function applyStatesFor(fieldIds, errors) {
    var map = {};
    errors.forEach(function (e) { map[e.fieldId] = e.message; });
    fieldIds.forEach(function (id) { applyFieldState(id, map[id] || ""); });
  }

  function focusTarget(fieldId) {
    var el = byId(fieldId) || document.querySelector('[data-hook="' + fieldId + '"]');
    if (el) el.focus();
  }

  // --- Error summary ----------------------------------------------------

  function renderErrorSummary(errors) {
    var box = $('[data-hook="error-summary"]');
    if (!box) return;
    box.innerHTML = "";
    var heading = document.createElement("p");
    heading.className = "error-summary-heading";
    heading.textContent = "There " + (errors.length === 1 ? "is" : "are") + " " + errors.length +
      " problem" + (errors.length === 1 ? "" : "s") + " to fix before this synthetic order can be placed:";
    box.appendChild(heading);
    var list = document.createElement("ul");
    errors.forEach(function (err) {
      var li = document.createElement("li");
      var link = document.createElement("button");
      link.type = "button";
      link.className = "error-link";
      link.textContent = err.message;
      link.addEventListener("click", function () {
        if (err.stepNum) goToStep(err.stepNum);
        focusTarget(err.fieldId);
      });
      li.appendChild(link);
      list.appendChild(li);
    });
    box.appendChild(list);
    box.hidden = false;
  }

  function clearErrorSummary() {
    var box = $('[data-hook="error-summary"]');
    if (!box) return;
    box.hidden = true;
    box.innerHTML = "";
  }

  // --- Step navigation ----------------------------------------------------
  //
  // Only one step is the *active* task at a time (named progress + a single
  // active Continue control), but once a step has been reached it stays
  // accessibly visible and operable so its fields can still be reviewed and
  // corrected later in the journey — a completed step is never torn back out
  // of the page. Steps beyond the point the wizard journey has reached are
  // hidden accessibly: aria-hidden, removed from the tab order, and visually
  // collapsed to zero size.

  function setSectionRevealed(section, revealed) {
    if (revealed) {
      section.classList.remove("step-pending");
      section.removeAttribute("aria-hidden");
      section.querySelectorAll(FOCUSABLE_SELECTOR).forEach(function (el) {
        el.classList.remove("pending-control");
        el.removeAttribute("tabindex");
      });
    } else {
      section.classList.add("step-pending");
      section.setAttribute("aria-hidden", "true");
      section.querySelectorAll(FOCUSABLE_SELECTOR).forEach(function (el) {
        el.classList.add("pending-control");
        el.setAttribute("tabindex", "-1");
      });
    }
  }

  function applyStepVisibility() {
    document.querySelectorAll(".step").forEach(function (section) {
      var stepNum = Number(section.dataset.step);
      setSectionRevealed(section, stepNum <= state.highestRevealed);
    });
    document.querySelectorAll('[data-action="continue"]').forEach(function (btn) {
      var stepNum = Number(btn.dataset.step);
      // Only the single frontier step (the furthest step reached, not yet
      // continued past) keeps an active Continue control. Earlier, already
      // completed steps remain visible for editing but do not repeat their
      // own Continue control.
      btn.hidden = !(stepNum === state.highestRevealed && stepNum < 4);
    });
  }

  function updateProgress(stepNum, placed) {
    var progress = $('[data-hook="progress"]');
    var labels = { 1: "Contact details", 2: "Delivery address", 3: "Payment", 4: "Review & place order" };
    if (progress) {
      progress.setAttribute("aria-valuenow", String(stepNum));
      progress.setAttribute("aria-valuetext", placed ?
        "Order placed. Confirmation SYN-2048." :
        "Step " + stepNum + " of 4: " + labels[stepNum]);
    }
    document.querySelectorAll(".progress-step").forEach(function (item) {
      var n = Number(item.dataset.step);
      item.classList.toggle("is-current", n === stepNum && !placed);
      item.classList.toggle("is-complete", n < stepNum || !!placed);
    });
  }

  function goToStep(stepNum) {
    stepNum = Math.max(1, Math.min(4, stepNum));
    if (stepNum > state.highestRevealed) state.highestRevealed = stepNum;
    state.currentFocus = stepNum;
    applyStepVisibility();
    updateProgress(stepNum);
    if (stepNum === 4) populateReview();
    var heading = document.querySelector('.step[data-step="' + stepNum + '"] h2');
    if (heading) heading.focus();
    persistState();
  }

  function handleContinue(stepNum) {
    var fieldIds = STEP_FIELDS[stepNum] || [];
    var errors = computeErrors(fieldIds);
    applyStatesFor(fieldIds, errors);
    if (errors.length) {
      setStatus("Step " + stepNum + " saved. " + errors.length +
        " item" + (errors.length === 1 ? "" : "s") + " still " +
        (errors.length === 1 ? "needs" : "need") +
        " attention — you can continue now and fix " +
        (errors.length === 1 ? "it" : "them") + " before placing your order.");
    } else {
      setStatus("Step " + stepNum + " complete.");
    }
    goToStep(stepNum + 1);
  }

  function handleBack(stepNum) {
    goToStep(stepNum - 1);
  }

  function handleEdit(targetStep) {
    goToStep(Number(targetStep));
  }

  function handleEditShipping() {
    var fieldset = document.querySelector(".shipping-picker fieldset");
    var legend = fieldset ? fieldset.querySelector("legend") : null;
    var firstRadio = byId("shipping-standard");
    if (fieldset && fieldset.scrollIntoView) fieldset.scrollIntoView({ block: "center" });
    if (firstRadio) firstRadio.focus();
    else if (legend) legend.focus();
    setStatus("Shipping method is in the order summary above. Choose Standard or Express, then return to review.");
  }

  // --- Review + totals ----------------------------------------------------

  function shippingMethod() {
    var checked = document.querySelector('input[name="shipping-method"]:checked');
    return checked ? checked.value : "standard";
  }

  function updateTotal() {
    var method = shippingMethod();
    var shippingAmount = method === "express" ? 12.00 : 5.00;
    var total = 80.00 + 8.50 + shippingAmount;
    var totalEl = $('[data-hook="total"]');
    var shippingDisplay = byId("shipping-amount-display");
    if (totalEl) totalEl.textContent = "Total: AUD " + total.toFixed(2);
    if (shippingDisplay) shippingDisplay.textContent = "AUD " + shippingAmount.toFixed(2);
  }

  function populateReview() {
    setText('[data-review-field="contact"]', [val("contact-name"), val("contact-email"), val("contact-phone")]
      .filter(Boolean).join(" · ") || "Not entered yet");
    var addressParts = [val("address-line1")];
    var cityLine = [val("address-city"), val("address-state"), val("address-postcode")].filter(Boolean).join(" ");
    if (cityLine) addressParts.push(cityLine);
    if (val("address-country")) addressParts.push(val("address-country"));
    setText('[data-review-field="address"]', addressParts.filter(Boolean).join(", ") || "Not entered yet");
    var method = shippingMethod();
    setText('[data-review-field="shipping"]', method === "express" ?
      "Express — 1 to 2 business days — AUD 12.00" : "Standard — 3 to 5 business days — AUD 5.00");
    var cardNumber = val("card-number").replace(/\s+/g, "");
    var last4 = cardNumber.length >= 4 ? cardNumber.slice(-4) : "";
    var expiry = val("card-expiry");
    if (cardNumber && expiry) {
      setText('[data-review-field="payment"]', "Synthetic card ending " + last4 + ", expires " + expiry);
    } else {
      setText('[data-review-field="payment"]', "Not entered yet");
    }
    setText('[data-review-field="confirmation-name"]', val("contact-name") || "there");
  }

  function setText(selector, text) {
    var el = document.querySelector(selector);
    if (el) el.textContent = text;
  }

  // --- Placement ----------------------------------------------------

  function handlePlaceOrder(event) {
    event.preventDefault();
    if (state.orderPlaced) return;
    var errors = computeAllErrors();
    applyStatesFor(ALL_VALIDATABLE_FIELDS, errors);
    if (errors.length) {
      renderErrorSummary(errors);
      var first = errors[0];
      if (first.stepNum) {
        goToStep(first.stepNum);
      }
      focusTarget(first.fieldId);
      setStatus("There " + (errors.length === 1 ? "is" : "are") + " " + errors.length +
        " problem" + (errors.length === 1 ? "" : "s") + " to fix before we can place your order.");
      return;
    }
    clearErrorSummary();
    beginPlacement();
  }

  function beginPlacement() {
    var button = $('[data-hook="place-order"]');
    if (button) button.setAttribute("aria-busy", "true");
    setStatus("Placing your order…");
    window.setTimeout(function () {
      state.orderPlaced = true;
      if (button) {
        button.removeAttribute("aria-busy");
        button.setAttribute("aria-disabled", "true");
      }
      showConfirmation();
    }, 120);
  }

  function showConfirmation() {
    // Keep the review step (and its Place order control) visible and reachable
    // rather than tearing it out of the page, so focus/keyboard state remains
    // meaningful after a completed order. The form is guarded against further
    // submission by the orderPlaced flag and aria-disabled on Place order.
    populateReview();
    var box = $('[data-hook="confirmation"]');
    if (box) {
      box.hidden = false;
      box.focus();
    }
    var idEl = $('[data-hook="confirmation-id"]');
    if (idEl) idEl.textContent = "SYN-2048";
    updateProgress(4, true);
    setStatus("Order placed. Confirmation SYN-2048.");
    try { window.localStorage.removeItem(STORAGE_KEY); } catch (e) { /* storage unavailable */ }
  }

  // --- Persistence (safe fields only; never payment) ----------------------------------------------------

  function persistState() {
    try {
      var data = {};
      SAFE_FIELD_IDS.forEach(function (id) { data[id] = val(id); });
      data.shippingMethod = shippingMethod();
      data.currentStep = state.currentFocus;
      data.highestRevealed = state.highestRevealed;
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) { /* storage unavailable; resume is a convenience, not required */ }
  }

  function hydrateFromStorage() {
    var raw = null;
    try { raw = window.localStorage.getItem(STORAGE_KEY); } catch (e) { raw = null; }
    if (!raw) return;
    var saved;
    try { saved = JSON.parse(raw); } catch (e) { return; }
    if (!saved || typeof saved !== "object") return;
    var restoredAny = false;
    SAFE_FIELD_IDS.forEach(function (id) {
      if (typeof saved[id] === "string" && saved[id]) {
        var el = byId(id);
        if (el) { el.value = saved[id]; restoredAny = true; }
      }
    });
    if (saved.shippingMethod === "express") {
      byId("shipping-express").checked = true;
    } else {
      byId("shipping-standard").checked = true;
    }
    if (Number.isInteger(saved.highestRevealed) && saved.highestRevealed >= 1 && saved.highestRevealed <= 4) {
      state.highestRevealed = saved.highestRevealed;
    }
    if (Number.isInteger(saved.currentStep) && saved.currentStep >= 1 && saved.currentStep <= 4) {
      state.currentFocus = saved.currentStep;
    }
    if (state.currentFocus > state.highestRevealed) state.highestRevealed = state.currentFocus;
    if (restoredAny) {
      setStatus("Resumed your saved progress. Payment details are never saved and must be re-entered.");
    }
  }

  // --- Wiring ----------------------------------------------------

  function wireEvents() {
    document.querySelectorAll('[data-action="continue"]').forEach(function (btn) {
      btn.addEventListener("click", function () { handleContinue(Number(btn.dataset.step)); });
    });
    document.querySelectorAll('[data-action="back"]').forEach(function (btn) {
      btn.addEventListener("click", function () { handleBack(Number(btn.dataset.step)); });
    });
    document.querySelectorAll('[data-action="edit"]').forEach(function (btn) {
      btn.addEventListener("click", function () { handleEdit(btn.dataset.target); });
    });
    document.querySelectorAll('[data-action="edit-shipping"]').forEach(function (btn) {
      btn.addEventListener("click", handleEditShipping);
    });
    var toggle = document.querySelector('[data-action="toggle-summary"]');
    if (toggle) {
      toggle.addEventListener("click", function () {
        var details = byId("summary-details");
        var expanded = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!expanded));
        toggle.textContent = expanded ? "Show item details" : "Hide item details";
        if (details) details.hidden = expanded;
      });
    }
    var saveNow = document.querySelector('[data-action="save-now"]');
    if (saveNow) {
      saveNow.addEventListener("click", function () {
        persistState();
        setStatus("Progress saved on this device. You can safely close this tab and resume later. Payment details are never saved.");
      });
    }
    var clearProgress = document.querySelector('[data-action="clear-progress"]');
    if (clearProgress) {
      clearProgress.addEventListener("click", function () {
        try { window.localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
        window.location.reload();
      });
    }

    SAFE_FIELD_IDS.forEach(function (id) {
      var el = byId(id);
      if (el) el.addEventListener("input", persistState);
    });
    document.querySelectorAll('input[name="shipping-method"]').forEach(function (radio) {
      radio.addEventListener("change", function () {
        updateTotal();
        persistState();
      });
    });

    var form = byId("wizard-form");
    if (form) form.addEventListener("submit", handlePlaceOrder);
  }

  function init() {
    wireEvents();
    hydrateFromStorage();
    applyStepVisibility();
    updateProgress(state.currentFocus);
    if (state.currentFocus === 4 || state.highestRevealed >= 4) populateReview();
    updateTotal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
