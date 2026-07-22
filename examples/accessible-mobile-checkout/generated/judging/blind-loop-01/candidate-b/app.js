(() => {
  "use strict";

  const form = document.querySelector("#checkout-form");
  const status = document.querySelector('[data-hook="status"]');
  const errorSummary = document.querySelector('[data-hook="error-summary"]');
  const confirmation = document.querySelector('[data-hook="confirmation"]');
  const confirmationContent = document.querySelector("#confirmation-content");
  const placeOrder = document.querySelector('[data-hook="place-order"]');
  const reviewConfirmation = document.querySelector('[data-hook="review-confirmation"]');
  const storageKey = "northstar-safe-checkout";
  let placementStarted = false;

  const safeFields = [
    "contact-name",
    "contact-email",
    "contact-phone",
    "address-line1",
    "address-city",
    "address-state",
    "address-postcode",
    "address-country"
  ];

  const fieldRules = {
    "contact-name": value => value.trim().length > 0,
    "contact-email": value => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim()),
    "contact-phone": value => /^\+?[\d\s]{8,}$/.test(value.trim()),
    "address-line1": value => value.trim().length > 0,
    "address-city": value => value.trim().length > 0,
    "address-state": value => value === "NSW",
    "address-postcode": value => /^\d{4}$/.test(value.trim()),
    "address-country": value => value.trim().toLowerCase() === "australia",
    "card-number": value => value.replace(/\s/g, "") === "4111111111111111",
    "card-expiry": value => value.trim() === "12/34",
    "card-security": value => value.trim() === "123",
    "card-name": value => value.trim().toLowerCase() === "alex morgan"
  };

  const errorMessages = {
    "contact-name": "Enter the synthetic full name.",
    "contact-email": "Enter a complete email address, such as alex.morgan@example.invalid.",
    "contact-phone": "Enter the synthetic phone number with at least 8 digits.",
    "address-line1": "Enter the synthetic street address.",
    "address-city": "Enter the synthetic city or suburb.",
    "address-state": "Select NSW for this demonstration.",
    "address-postcode": "Enter the 4-digit synthetic postcode.",
    "address-country": "Enter Australia for this demonstration.",
    "card-number": "Enter the 16-digit synthetic card number shown above.",
    "card-expiry": "Enter the synthetic expiry as 12/34.",
    "card-security": "Enter the 3-digit synthetic security code.",
    "card-name": "Enter Alex Morgan as the synthetic name on card."
  };

  function fieldFor(name) {
    return document.querySelector(`[data-hook="${name}"]`);
  }

  function setStatus(message) {
    status.textContent = message;
  }

  function readSafeState() {
    try {
      const value = localStorage.getItem(storageKey);
      return value ? JSON.parse(value) : null;
    } catch {
      return null;
    }
  }

  function saveSafeState() {
    const fields = {};
    safeFields.forEach(name => {
      fields[name] = fieldFor(name).value;
    });
    const shipping = form.elements.shipping.value || "standard";
    try {
      localStorage.setItem(storageKey, JSON.stringify({ fields, shipping }));
      setStatus("Safe contact, delivery and shipping progress saved on this device. Payment details are never saved.");
    } catch {
      setStatus("Progress could not be saved. You can still complete this local demonstration.");
    }
  }

  function restoreSafeState() {
    const saved = readSafeState();
    if (!saved || !saved.fields) {
      return;
    }
    safeFields.forEach(name => {
      if (typeof saved.fields[name] === "string") {
        fieldFor(name).value = saved.fields[name];
      }
    });
    const shipping = form.querySelector(`input[name="shipping"][value="${saved.shipping}"]`);
    if (shipping) {
      shipping.checked = true;
    }
    setStatus("Safe progress restored. Re-enter synthetic payment details; they were not saved.");
  }

  function updateTotals() {
    const express = form.elements.shipping.value === "express";
    const shippingAmount = express ? "AUD 12.00" : "AUD 5.00";
    const total = express ? "AUD 100.50" : "AUD 93.50";
    document.querySelector("[data-shipping-total]").textContent = shippingAmount;
    document.querySelector('[data-hook="total"]').textContent = total;
    document.querySelector("[data-total-summary]").textContent = total;
    document.querySelector("[data-review-total]").textContent = total;
    document.querySelector("#review-shipping").textContent = express
      ? "Express — 1 to 2 business days · AUD 12.00"
      : "Standard — 3 to 5 business days · AUD 5.00";
  }

  function updateReview() {
    const values = safeFields.map(name => fieldFor(name).value.trim());
    const [name, email, phone, street, city, stateName, postcode, country] = values;
    const review = document.querySelector("#review-contact");
    if (values.every(Boolean)) {
      review.textContent = `${name} · ${email} · ${phone} · ${street}, ${city} ${stateName} ${postcode}, ${country}`;
    } else {
      review.textContent = "Enter your synthetic contact and address above.";
    }
  }

  function clearFieldError(field) {
    const error = document.querySelector(`#${field.id}-error`);
    if (!error) {
      return;
    }
    field.removeAttribute("aria-invalid");
    field.setAttribute("aria-describedby", `${field.id}-help`);
    error.hidden = true;
    error.textContent = "";
  }

  function showFieldError(field, message) {
    const error = document.querySelector(`#${field.id}-error`);
    field.setAttribute("aria-invalid", "true");
    field.setAttribute("aria-describedby", `${field.id}-help ${field.id}-error`);
    error.textContent = message;
    error.hidden = false;
  }

  function validate() {
    const problems = [];
    Object.entries(fieldRules).forEach(([name, rule]) => {
      const field = fieldFor(name);
      clearFieldError(field);
      if (!rule(field.value)) {
        const message = errorMessages[name];
        showFieldError(field, message);
        problems.push({ field, message });
      }
    });

    const reviewError = document.querySelector("#review-confirmation-error");
    reviewConfirmation.removeAttribute("aria-invalid");
    reviewConfirmation.setAttribute("aria-describedby", "review-confirmation-help");
    reviewError.hidden = true;
    reviewError.textContent = "";
    if (!reviewConfirmation.checked) {
      const message = "Review the fictional order and select the confirmation checkbox.";
      reviewConfirmation.setAttribute("aria-invalid", "true");
      reviewConfirmation.setAttribute("aria-describedby", "review-confirmation-help review-confirmation-error");
      reviewError.textContent = message;
      reviewError.hidden = false;
      problems.push({ field: reviewConfirmation, message });
    }
    return problems;
  }

  function showErrorSummary(problems) {
    const links = problems.map(problem =>
      `<li><a href="#${problem.field.id}">${problem.message}</a></li>`
    ).join("");
    errorSummary.innerHTML = `<h2>Check ${problems.length} ${problems.length === 1 ? "item" : "items"}</h2><p>Your entries are preserved. Use these links to correct each item.</p><ul>${links}</ul>`;
    errorSummary.hidden = false;
    errorSummary.focus();
    setStatus(`Order not placed. ${problems.length} ${problems.length === 1 ? "item needs" : "items need"} attention.`);
  }

  function completeOrder() {
    if (document.querySelector('[data-hook="confirmation-id"]')) {
      return;
    }
    confirmationContent.innerHTML = '<p>Confirmation ID <strong class="confirmation-id" data-hook="confirmation-id">SYN-2048</strong></p>';
    confirmation.hidden = false;
    placementStarted = false;
    placeOrder.disabled = true;
    placeOrder.setAttribute("aria-busy", "false");
    setStatus("Synthetic order placed once. Confirmation ID SYN-2048.");
    confirmation.setAttribute("tabindex", "-1");
    confirmation.focus();
  }

  form.addEventListener("submit", event => {
    event.preventDefault();
    if (placementStarted || document.querySelector('[data-hook="confirmation-id"]')) {
      setStatus("This synthetic order is already confirmed as SYN-2048. No duplicate was created.");
      return;
    }
    const problems = validate();
    if (problems.length) {
      showErrorSummary(problems);
      return;
    }
    errorSummary.hidden = true;
    errorSummary.textContent = "";
    placementStarted = true;
    placeOrder.disabled = true;
    placeOrder.setAttribute("aria-busy", "true");
    setStatus("Placing local synthetic order. Please wait.");
    window.setTimeout(completeOrder, 180);
  });

  Object.keys(fieldRules).forEach(name => {
    const field = fieldFor(name);
    field.addEventListener("input", () => {
      clearFieldError(field);
      updateReview();
    });
    field.addEventListener("change", () => {
      clearFieldError(field);
      updateReview();
    });
  });

  safeFields.forEach(name => {
    const field = fieldFor(name);
    field.addEventListener("input", saveSafeState);
    field.addEventListener("change", saveSafeState);
  });

  form.querySelectorAll('input[name="shipping"]').forEach(control => {
    control.addEventListener("change", () => {
      updateTotals();
      saveSafeState();
      form.querySelectorAll("[data-hook^=\"shipping-\"]").forEach(label => {
        label.setAttribute("aria-checked", String(label.querySelector("input").checked));
      });
    });
  });

  reviewConfirmation.addEventListener("change", () => {
    const error = document.querySelector("#review-confirmation-error");
    reviewConfirmation.removeAttribute("aria-invalid");
    reviewConfirmation.setAttribute("aria-describedby", "review-confirmation-help");
    error.hidden = true;
    error.textContent = "";
  });

  document.querySelectorAll("[data-edit-target]").forEach(button => {
    button.addEventListener("click", () => {
      const target = document.querySelector(`#${button.dataset.editTarget}`);
      target.scrollIntoView({ block: "start" });
      const firstControl = target.querySelector("input, select");
      if (firstControl) {
        firstControl.focus();
      }
      setStatus(`Editing ${button.dataset.editTarget}. Existing entries are preserved.`);
    });
  });

  document.querySelectorAll("[data-hook^=\"shipping-\"]").forEach(control => {
    const radio = control.querySelector('input[type="radio"]');
    Object.defineProperty(control, "checked", {
      configurable: true,
      get: () => radio.checked
    });
    control.addEventListener("keydown", event => {
      if (event.key === " " || event.key === "Enter") {
        event.preventDefault();
        radio.checked = true;
        radio.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
  });

  restoreSafeState();
  updateTotals();
  updateReview();
})();
