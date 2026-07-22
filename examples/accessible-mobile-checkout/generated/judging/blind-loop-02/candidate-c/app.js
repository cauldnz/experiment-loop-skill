document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('checkout-form');
  const errorSummary = document.querySelector('[data-hook="error-summary"]');
  const errorList = document.getElementById('error-list');
  const statusRegion = document.querySelector('[data-hook="status"]');
  const confirmationRegion = document.querySelector('[data-hook="confirmation"]');
  const submitBtn = document.querySelector('[data-hook="place-order"]');
  const checkoutRoot = document.querySelector('[data-hook="checkout-root"]');
  const reviewCheckbox = document.getElementById('review-confirmation');

  const STORAGE_KEY = 'northstar-checkout-progress';
  let placementStarted = false;

  function loadProgress() {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    let restored = false;
    const inputs = form.querySelectorAll('input:not([type="radio"]):not([type="checkbox"])');
    inputs.forEach(input => {
      if (input.id.startsWith('card-number') || input.id.startsWith('card-expiry') || input.id.startsWith('card-security') || input.id === 'card-name') {
        return; 
      }
      if (data[input.id]) {
        input.value = data[input.id];
        restored = true;
      }
    });

    if (data['shipping-method']) {
      const radio = document.querySelector(`input[name="shipping-method"][value="${data['shipping-method']}"]`);
      if (radio) {
        radio.checked = true;
        updateTotals(data['shipping-method']);
        restored = true;
      }
    }

    ['contact', 'address', 'shipping', 'payment'].forEach(section => {
      updateSectionStatus(section, false);
    });

    if (restored) {
      statusRegion.textContent = 'Draft progress restored safely. Payment details are never saved.';
    }
  }

  function saveProgress() {
    const data = {};
    const inputs = form.querySelectorAll('input:not([type="radio"]):not([type="checkbox"])');
    inputs.forEach(input => {
      if (input.id.startsWith('card-number') || input.id.startsWith('card-expiry') || input.id.startsWith('card-security') || input.id === 'card-name') {
        return;
      }
      data[input.id] = input.value;
    });
    
    const shippingRadio = document.querySelector('input[name="shipping-method"]:checked');
    if (shippingRadio) {
      data['shipping-method'] = shippingRadio.value;
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }

  function updateTotals(method) {
    const totalEl = document.querySelector('[data-hook="total"]');
    const methodDisplay = document.getElementById('shipping-method-display');
    if (method === 'express') {
      totalEl.textContent = 'AUD 100.50';
      if (methodDisplay) methodDisplay.textContent = 'Express';
    } else {
      totalEl.textContent = 'AUD 93.50';
      if (methodDisplay) methodDisplay.textContent = 'Standard';
    }
  }

  form.querySelectorAll('input').forEach(input => {
    input.addEventListener('input', () => { 
      saveProgress(); 
      updateSectionStatusByInput(input);
      if (input.id !== 'review-confirmation' && reviewCheckbox) {
        reviewCheckbox.checked = false;
      }
    });
    input.addEventListener('change', () => { 
      saveProgress(); 
      if (input.name === 'shipping-method') {
        updateTotals(input.value);
      }
      updateSectionStatusByInput(input);
      if (input.id !== 'review-confirmation' && reviewCheckbox) {
        reviewCheckbox.checked = false;
      }
    });
    input.addEventListener('blur', () => {
      updateSectionStatusByInput(input);
    });
  });

  function updateSectionStatusByInput(input) {
    const section = input.closest('.task-card');
    if (section) {
      const sectionName = section.getAttribute('data-hook').replace('-section', '');
      updateSectionStatus(sectionName);
    }
  }

  function updateSectionStatus(sectionName, announce = true) {
    const sectionEl = document.querySelector(`[data-hook="${sectionName}-section"]`);
    if (!sectionEl) return;
    const inputs = sectionEl.querySelectorAll('input');
    let isComplete = true;

    inputs.forEach(input => {
      if (input.required && !input.value.trim() && input.type !== 'radio' && input.type !== 'checkbox') {
        isComplete = false;
      }
    });

    if (sectionName === 'shipping') {
      const checked = document.querySelector('input[name="shipping-method"]:checked');
      if (!checked) {
        isComplete = false;
      }
    }

    const statusEl = document.getElementById(`${sectionName}-status`);
    if (statusEl) {
      const wasComplete = statusEl.classList.contains('complete');
      if (isComplete) {
        statusEl.textContent = 'Complete';
        statusEl.classList.add('complete');
        if (!wasComplete && announce) {
          statusRegion.textContent = `${sectionName} section is now complete.`;
        }
      } else {
        statusEl.textContent = 'Incomplete';
        statusEl.classList.remove('complete');
      }
    }
    return isComplete;
  }

  function showError(input, message) {
    input.setAttribute('aria-invalid', 'true');
    const errorSpan = document.getElementById(`${input.id}-error`);
    if (errorSpan) {
      errorSpan.textContent = message;
      errorSpan.classList.remove('hidden');
      let describedby = input.getAttribute('aria-describedby') || '';
      const errorId = errorSpan.id;
      if (!describedby.includes(errorId)) {
        input.setAttribute('aria-describedby', `${describedby} ${errorId}`.trim());
      }
    }
  }

  function clearError(input) {
    input.removeAttribute('aria-invalid');
    const errorSpan = document.getElementById(`${input.id}-error`);
    if (errorSpan) {
      errorSpan.textContent = '';
      errorSpan.classList.add('hidden');
      let describedby = input.getAttribute('aria-describedby') || '';
      const errorId = errorSpan.id;
      describedby = describedby.replace(errorId, '').trim();
      if (describedby) {
        input.setAttribute('aria-describedby', describedby);
      } else {
        input.removeAttribute('aria-describedby');
      }
    }
  }

  const editLinks = document.querySelectorAll('.edit-link');
  editLinks.forEach(link => {
    link.addEventListener('click', () => {
      const target = link.getAttribute('data-target');
      openAccordion(target);
      const section = document.querySelector(`[data-hook="${target}-section"]`);
      if (section) {
        const firstInput = section.querySelector('input');
        if (firstInput) {
          firstInput.focus();
        } else {
          section.setAttribute('tabindex', '-1');
          section.focus();
        }
      }
    });
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    errorList.innerHTML = '';
    errorSummary.classList.add('hidden');
    let hasErrors = false;
    const allInputs = form.querySelectorAll('input');

    allInputs.forEach(clearError);

    allInputs.forEach(input => {
      let isInvalid = false;
      let msg = '';
      if (input.required) {
        if (input.type === 'radio') {
          const checked = form.querySelector(`input[name="${input.name}"]:checked`);
          if (!checked) {
            isInvalid = true;
            msg = 'Please select an option';
          }
        } else if (input.type === 'checkbox') {
          if (!input.checked) {
            isInvalid = true;
            msg = 'You must confirm to proceed';
          }
        } else if (!input.value.trim()) {
          isInvalid = true;
          msg = 'Please enter a value';
        }
      }

      if (input.type === 'email' && input.value && !input.value.includes('@')) {
        isInvalid = true;
        msg = 'Please enter a valid email address';
      }

      if (isInvalid) {
        hasErrors = true;
        showError(input, msg);
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = `#${input.id}`;
        
        const label = document.querySelector(`label[for="${input.id}"]`);
        const fieldName = label ? label.textContent : input.name;
        a.textContent = `${fieldName}: ${msg}`;
        
        a.addEventListener('click', (ev) => {
          ev.preventDefault();
          input.focus();
        });

        li.appendChild(a);
        errorList.appendChild(li);
      }
    });

    if (!reviewCheckbox.checked) {
      hasErrors = true;
    }

    if (hasErrors) {
      errorSummary.classList.remove('hidden');
      errorSummary.focus();
      statusRegion.textContent = 'There are errors in the form. Please correct them to proceed.';
      return;
    }

    if (placementStarted) return;
    placementStarted = true;

    submitBtn.disabled = true;
    checkoutRoot.setAttribute('aria-busy', 'true');
    statusRegion.textContent = 'Processing your order...';

    // Replace 500ms with a deterministic short tick.
    const timeoutDuration = 10; 

    setTimeout(() => {
      checkoutRoot.removeAttribute('aria-busy');
      confirmationRegion.classList.remove('hidden');
      document.querySelector('[data-hook="confirmation-id"]').textContent = 'SYN-2048';
      confirmationRegion.focus();
      statusRegion.textContent = 'Order successfully placed.';
      localStorage.removeItem(STORAGE_KEY);
      placementStarted = false;
    }, timeoutDuration);
  });

  // Accordion Logic
  const accordions = ['contact', 'address', 'shipping', 'payment'];
  
  function openAccordion(targetId) {
    accordions.forEach(acc => {
      const content = document.getElementById(`${acc}-content`);
      const btn = document.getElementById(`${acc}-header`);
      if (acc === targetId) {
        content.classList.remove('hidden');
        btn.setAttribute('aria-expanded', 'true');
      } else {
        content.classList.add('hidden');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  accordions.forEach(acc => {
    const btn = document.getElementById(`${acc}-header`);
    if (btn) {
      btn.addEventListener('click', () => {
        const isExpanded = btn.getAttribute('aria-expanded') === 'true';
        if (!isExpanded) {
          openAccordion(acc);
        }
      });
    }
    
    // Continue buttons
    const continueBtn = document.getElementById(`${acc}-continue`);
    if (continueBtn) {
      continueBtn.addEventListener('click', () => {
        const nextId = continueBtn.getAttribute('data-next');
        if (nextId) {
          openAccordion(nextId);
          const nextSection = document.querySelector(`[data-hook="${nextId}-section"]`);
          if (nextSection) {
            const firstInput = nextSection.querySelector('input');
            if (firstInput) firstInput.focus();
            else nextSection.focus();
          }
        }
      });
    }
  });

  // Initial state: open Contact
  openAccordion('contact');

  loadProgress();
});
