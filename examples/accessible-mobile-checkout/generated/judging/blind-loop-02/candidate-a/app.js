(() => {
  "use strict";

  const form = document.querySelector("#checkout-form");
  const status = document.querySelector('[data-hook="status"]');
  const errorSummary = document.querySelector('[data-hook="error-summary"]');
  const confirmation = document.querySelector('[data-hook="confirmation"]');
  const confirmationContent = document.querySelector("#confirmation-content");
  const placeOrder = document.querySelector('[data-hook="place-order"]');
  const reviewConfirmation = document.querySelector('[data-hook="review-confirmation"]');
  const compactCompleted = document.querySelector("#compact-completed");
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
    "contact-name": value => value.trim().length >= 2,
    "contact-email": value => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim()),
    "contact-phone": value => /^\+?[\d\s()-]{8,}$/.test(value.trim()) && value.replace(/\D/g, "").length >= 8,
    "address-line1": value => value.trim().length >= 3,
    "address-city": value => value.trim().length >= 2,
    "address-state": value => /^[A-Za-z][A-Za-z .'-]{1,29}$/.test(value.trim()),
    "address-postcode": value => /^\d{4}$/.test(value.trim()),
    "address-country": value => /^[A-Za-z][A-Za-z .'-]{1,39}$/.test(value.trim()),
    "card-number": value => /^\d{16}$/.test(value.replace(/[\s-]/g, "")),
    "card-expiry": value => /^(0[1-9]|1[0-2])\/\d{2}$/.test(value.trim()),
    "card-security": value => /^\d{3,4}$/.test(value.trim()),
    "card-name": value => value.trim().length >= 2
  };

  const errorMessages = {
    "contact-name": "Enter a synthetic full name with at least 2 characters.",
    "contact-email": "Enter a complete email address, such as alex.morgan@example.invalid.",
    "contact-phone": "Enter the synthetic phone number with at least 8 digits.",
    "address-line1": "Enter a synthetic street address with at least 3 characters.",
    "address-city": "Enter a synthetic city or suburb with at least 2 characters.",
    "address-state": "Enter a synthetic state or region, such as NSW.",
    "address-postcode": "Enter the 4-digit synthetic postcode.",
    "address-country": "Enter a synthetic country name, such as Australia.",
    "card-number": "Enter 16 synthetic digits; spaces and hyphens are accepted.",
    "card-expiry": "Enter a synthetic expiry in MM/YY format, such as 12/34.",
    "card-security": "Enter a 3- or 4-digit synthetic security code, such as 123.",
    "card-name": "Enter a synthetic name on card with at least 2 characters."
  };

  const sectionFields = {
    contact: ["contact-name", "contact-email", "contact-phone"],
    delivery: ["address-line1", "address-city", "address-state", "address-postcode", "address-country"],
    shipping: [],
    payment: ["card-number", "card-expiry", "card-security", "card-name"]
  };

  const problemGroups = {
    contact: { label: "Contact", fields: sectionFields.contact },
    delivery: { label: "Delivery address", fields: sectionFields.delivery },
    payment: { label: "Synthetic payment", fields: sectionFields.payment },
    review: { label: "Review", fields: ["review-confirmation"] }
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

  function sectionIsComplete(id) {
      if (id === "shipping") {
        return Boolean(form.elements.shipping.value);
      }
      return sectionFields[id].every(name => fieldRules[name](fieldFor(name).value));
    }

    function sectionSummary(id) {
      if (id === "contact") {
        return `${fieldFor("contact-name").value.trim()} · ${fieldFor("contact-email").value.trim()}`;
      }
      if (id === "delivery") {
        return `${fieldFor("address-city").value.trim()} ${fieldFor("address-state").value.trim()} ${fieldFor("address-postcode").value.trim()}`;
      }
      if (id === "shipping") {
        return form.elements.shipping.value === "express"
          ? "Express — 1 to 2 business days · AUD 12.00"
          : "Standard — 3 to 5 business days · AUD 5.00";
      }
      return "Synthetic card details entered; ending digits are shown only at review.";
    }

    function setSectionCompacted(id, compacted) {
      const section = document.querySelector(`#${id}`);
      const body = section.querySelector("[data-section-body]");
      const summary = section.querySelector("[data-completed-summary]");
      const state = section.querySelector("[data-section-state]");
      const complete = sectionIsComplete(id);
      const shouldCompact = Boolean(compacted && complete && !section.contains(document.activeElement));
      section.dataset.compacted = String(shouldCompact);
      body.hidden = shouldCompact;
      summary.hidden = !shouldCompact;
      const summaryText = summary.querySelector("[data-summary-text]");
      if (summaryText) {
        summaryText.textContent = complete ? sectionSummary(id) : "";
      }
      state.textContent = complete ? (shouldCompact ? "Complete · compacted" : "Complete") : "";
    }

    function refreshCompactSections() {
      Object.keys(sectionFields).forEach(id => setSectionCompacted(id, compactCompleted.checked));
    }

    function openSection(id, focus = true) {
      setSectionCompacted(id, false);
      const section = document.querySelector(`#${id}`);
      section.scrollIntoView({ block: "start" });
      if (focus) {
        const firstControl = section.querySelector("input, select");
        if (firstControl) {
          firstControl.focus();
        }
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
        problems.push({ field, message, name });
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
      problems.push({ field: reviewConfirmation, message, name: "review-confirmation" });
    }
    return problems;
  }

  function showErrorSummary(problems) {
    const allLinks = problems.map(problem =>
      `<li><a href="#${problem.field.id}">${problem.message}</a></li>`
    ).join("");
    const groupedLinks = Object.values(problemGroups).map(group => {
      const groupProblems = problems.filter(problem => group.fields.includes(problem.name));
      if (!groupProblems.length) {
        return "";
      }
      const first = groupProblems[0];
      const count = `${groupProblems.length} ${groupProblems.length === 1 ? "item" : "items"}`;
      return `<li><a href="#${first.field.id}">${group.label}: ${count} need attention</a></li>`;
    }).join("");
    errorSummary.innerHTML = `<h2>Check ${problems.length} ${problems.length === 1 ? "item" : "items"} in ${Object.values(problemGroups).filter(group => problems.some(problem => group.fields.includes(problem.name))).length} sections</h2><p>Your entries are preserved. Start with one link per affected section, or expand the full list.</p><ul>${groupedLinks}</ul><details><summary>Show all ${problems.length} corrections</summary><ul>${allLinks}</ul></details>`;
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
      problems.forEach(problem => {
        const section = problem.field.closest(".task-section");
        if (section && section.id in sectionFields) {
          setSectionCompacted(section.id, false);
        }
      });
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
      refreshCompactSections();
    });
    field.addEventListener("change", () => {
      clearFieldError(field);
      updateReview();
      refreshCompactSections();
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
      refreshCompactSections();
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
      openSection(button.dataset.editTarget);
      setStatus(`Editing ${button.dataset.editTarget}. Existing entries are preserved.`);
    });
  });

  document.querySelectorAll("[data-edit-section]").forEach(button => {
    button.addEventListener("click", () => {
      const id = button.dataset.editSection;
      openSection(id);
      setStatus(`Editing ${id}. Existing entries are preserved.`);
    });
  });

  compactCompleted.addEventListener("change", () => {
    refreshCompactSections();
    setStatus(compactCompleted.checked
      ? "Compact view on. Completed sections use short summaries and remain directly editable."
      : "Compact view off. All checkout fields are expanded.");
  });

  Object.keys(sectionFields).forEach(id => {
    const section = document.querySelector(`#${id}`);
    section.addEventListener("focusout", event => {
      window.setTimeout(() => {
        if (compactCompleted.checked && !section.contains(document.activeElement)) {
          setSectionCompacted(id, true);
        }
      }, 0);
    });
  });

  restoreSafeState();
  updateTotals();
  updateReview();
  refreshCompactSections();
})();
