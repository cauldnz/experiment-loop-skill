"""Judge-local blind Playwright driver for final panel.

Operates each blind bundle (candidate-c, candidate-b, candidate-a in this
fixed order) at 390x844 CSS px with reduced motion and touch enabled.
Discovers controls generically, tolerates missing/renamed features, and
captures screenshots, transcripts, console messages, and network
requests. Does not rerun the objective harness.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

JUDGE_DIR = Path(__file__).resolve().parent.parent
BLIND_ROOT = JUDGE_DIR.parent / "blind"
VIEWPORT = {"width": 390, "height": 844}

CANDIDATES = [
    ("candidate-c", "c"),
    ("candidate-b", "b"),
    ("candidate-a", "a"),
]


def record(steps, name, action, target, outcome, extra=None):
    entry = {
        "step": len(steps) + 1,
        "name": name,
        "action": action,
        "target": target,
        "outcome": outcome,
    }
    if extra is not None:
        entry["details"] = extra
    steps.append(entry)


def query_state(page):
    return page.evaluate(
        """() => {
        const q = (sel) => document.querySelector(sel);
        const badges = Array.from(document.querySelectorAll('[data-section-state], [data-section-status]')).map(el => ({
            section: el.closest('[data-section], .task-section, section')?.id || null,
            text: (el.textContent || '').trim(),
            classes: el.className,
        }));
        const progress = q('[role="progressbar"]');
        const summary = q('[data-hook="error-summary"], #error-summary');
        const status = q('[data-hook="status"], #checkout-status');
        const confirmation = q('[data-hook="confirmation"], #confirmation, #confirmation-content');
        const confirmationHidden = confirmation ? (confirmation.hidden || getComputedStyle(confirmation).display === 'none' || confirmation.getAttribute('aria-hidden') === 'true') : true;
        const placeOrder = q('[data-hook="place-order"], button[type="submit"]');
        const clearConfirm = q('#clear-confirm, [data-hook="clear-confirm"]');
        const clearVisible = clearConfirm ? !(clearConfirm.hidden || getComputedStyle(clearConfirm).display === 'none') : false;
        const totalEl = q('[data-hook="total"], [data-review-total], [data-total]');
        return {
            progress_valuenow: progress?.getAttribute('aria-valuenow') || null,
            progress_valuetext: progress?.getAttribute('aria-valuetext') || null,
            error_summary_hidden: summary ? !!summary.hidden : null,
            error_summary_text: summary ? (summary.textContent || '').trim().slice(0, 240) : '',
            status_text: status ? (status.textContent || '').trim().slice(0, 240) : '',
            confirmation_visible: !confirmationHidden,
            place_order_disabled: !!placeOrder?.disabled,
            place_order_present: !!placeOrder,
            place_order_aria_busy: placeOrder?.getAttribute('aria-busy') || null,
            clear_confirm_visible: clearVisible,
            compact_completed: !!q('#compact-completed')?.checked,
            active_element: document.activeElement ? {
                tag: document.activeElement.tagName,
                id: document.activeElement.id || null,
                name: document.activeElement.getAttribute('name'),
                text: (document.activeElement.textContent || '').trim().slice(0, 80),
            } : null,
            section_states: badges,
            totals: {
                shipping: q('[data-shipping-total]')?.textContent,
                grand: totalEl ? totalEl.textContent : null,
                subtotal: q('[data-hook="subtotal"]')?.textContent,
                tax: q('[data-hook="tax"]')?.textContent,
            },
            confirmation_text: confirmation ? (confirmation.textContent || '').trim().slice(0, 240) : '',
        };
    }"""
    )


def touch_target_sizes(page):
    return page.evaluate(
        """() => {
        const selectors = [
            'a', 'button', 'input:not([type="hidden"])', 'select', 'label.choice-card',
            '[role="checkbox"]', '[data-hook]'
        ];
        const set = new Set();
        const rows = [];
        document.querySelectorAll(selectors.join(',')).forEach(el => {
            if (el.offsetParent === null && el.tagName !== 'A') return;
            const rect = el.getBoundingClientRect();
            if (rect.width === 0 && rect.height === 0) return;
            const key = (el.id || '') + '|' + (el.getAttribute('data-hook') || '') + '|' + el.tagName + '|' + (el.textContent || '').trim().slice(0, 30);
            if (set.has(key)) return;
            set.add(key);
            rows.push({
                tag: el.tagName,
                id: el.id || null,
                data_hook: el.getAttribute('data-hook') || null,
                text: (el.textContent || '').trim().slice(0, 60),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                below_24: (rect.width < 24 || rect.height < 24),
            });
        });
        return rows;
    }"""
    )


def keyboard_tab_traverse(page, max_steps=50):
    order = []
    page.evaluate("() => { document.body.focus(); if (document.activeElement !== document.body) document.body.focus(); }")
    for _ in range(max_steps):
        page.keyboard.press("Tab")
        info = page.evaluate(
            """() => {
            const el = document.activeElement;
            if (!el || el === document.body) return null;
            return {
                tag: el.tagName,
                id: el.id || null,
                type: el.getAttribute('type'),
                name: el.getAttribute('name'),
                aria_label: el.getAttribute('aria-label'),
                data_hook: el.getAttribute('data-hook'),
                text: (el.textContent || '').trim().slice(0, 60),
                hidden_ancestor: (() => {
                    let cur = el;
                    while (cur) {
                        if (cur.hidden) return true;
                        cur = cur.parentElement;
                    }
                    return false;
                })(),
            };
        }"""
        )
        order.append(info)
    return order


def try_click(page, selector, force=False, wait_ms=100):
    loc = page.locator(selector).first
    if loc.count() == 0:
        return False
    try:
        loc.click(force=force, timeout=1500)
        page.wait_for_timeout(wait_ms)
        return True
    except PWTimeout:
        return False
    except Exception:
        return False


def has_selector(page, selector):
    return page.locator(selector).first.count() > 0


def run_candidate(pw, bundle_name, code):
    shots_dir = JUDGE_DIR / "screenshots" / code
    logs_dir = JUDGE_DIR / "logs" / code
    shots_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    console_msgs = []
    external_requests = []
    net_requests = []
    steps = []

    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(
        viewport=VIEWPORT,
        reduced_motion="reduce",
        device_scale_factor=2,
        has_touch=True,
        is_mobile=True,
    )

    def on_console(msg):
        console_msgs.append({
            "type": msg.type,
            "text": msg.text[:400],
            "location": msg.location,
        })

    def on_request(req):
        u = req.url
        net_requests.append({"url": u[:200], "resource_type": req.resource_type, "method": req.method})
        parsed = urlparse(u)
        if parsed.scheme not in ("file", "data", "about", "blob", "chrome-error"):
            external_requests.append({"url": u[:200], "resource_type": req.resource_type})

    context.on("console", on_console)
    context.on("request", on_request)

    page = context.new_page()
    page.on("console", on_console)
    page.on("request", on_request)

    candidate_html = BLIND_ROOT / bundle_name / "index.html"
    candidate_url = candidate_html.resolve().as_uri()
    page.goto(candidate_url, wait_until="load")
    page.wait_for_timeout(200)

    # 1. Discovery — landmarks, section nav, progress, initial state
    landmarks = page.evaluate(
        """() => {
        const pick = (sel) => Array.from(document.querySelectorAll(sel)).map(el => ({
            tag: el.tagName,
            role: el.getAttribute('role'),
            aria_label: el.getAttribute('aria-label') || el.getAttribute('aria-labelledby'),
            id: el.id || null,
            text: (el.textContent || '').trim().slice(0, 80),
        }));
        return {
            header: pick('header'),
            main: pick('main'),
            nav: pick('nav'),
            footer: pick('footer'),
            aside: pick('aside'),
            landmark_role_notes: pick('[role="note"]'),
            progressbar: pick('[role="progressbar"]'),
            skip_links: pick('a.skip-link, a[href="#main-content"], a[href^="#main"]'),
            headings: Array.from(document.querySelectorAll('h1,h2,h3')).map(h => ({
                level: h.tagName,
                id: h.id || null,
                text: (h.textContent || '').trim().slice(0, 80),
            })),
        };
    }"""
    )
    (logs_dir / "landmarks.json").write_text(json.dumps(landmarks, indent=2))

    page.screenshot(path=str(shots_dir / "01-initial-390x844.png"), full_page=True)
    record(steps, "initial_load", "goto file:", "candidate index.html", "loaded 390x844, reduced motion",
           {"state": query_state(page), "url": candidate_url,
            "skip_links": landmarks["skip_links"],
            "landmark_counts": {k: len(v) for k, v in landmarks.items() if isinstance(v, list)}})

    # Additional viewports as required by contract
    for w, h in [(320, 568), (360, 800)]:
        page.set_viewport_size({"width": w, "height": h})
        page.wait_for_timeout(60)
        page.screenshot(path=str(shots_dir / f"01a-viewport-{w}x{h}.png"), full_page=True)
    page.set_viewport_size(VIEWPORT)
    page.wait_for_timeout(60)

    # 2. Keyboard traversal from top
    tab_order = keyboard_tab_traverse(page, max_steps=60)
    (logs_dir / "tab-order.json").write_text(json.dumps(tab_order, indent=2))
    hidden_leaks = [i for i, x in enumerate(tab_order) if x and x.get("hidden_ancestor")]
    record(steps, "keyboard_tab_traverse", "Tab*60", "document", "captured focus order",
           {"visible_focus_check": "tab_order in logs/tab-order.json",
            "hidden_ancestor_leaks": hidden_leaks,
            "count_focused": sum(1 for x in tab_order if x is not None)})

    # 3. Section nav links or in-page anchors
    anchor_targets = ["#contact", "#delivery", "#shipping", "#payment", "#review"]
    for anchor in anchor_targets:
        clicked = False
        for sel in [f'nav a[href="{anchor}"]', f'.section-nav a[href="{anchor}"]', f'a[href="{anchor}"]']:
            if has_selector(page, sel):
                try:
                    page.locator(sel).first.click(timeout=1200)
                    page.wait_for_timeout(70)
                    clicked = True
                    break
                except Exception:
                    continue
        record(steps, f"nav_click_{anchor}", "click section nav link", anchor,
               "scrolled/anchor navigated" if clicked else "no such nav link (section directly present)",
               {"y": page.evaluate("window.scrollY"), "hash": page.evaluate("location.hash"),
                "clicked": clicked})

    # 4. Touch target audit
    touch = touch_target_sizes(page)
    (logs_dir / "touch-targets.json").write_text(json.dumps(touch, indent=2))
    below = [t for t in touch if t["below_24"]]
    record(steps, "touch_target_audit", "measure interactive rects", "all controls",
           f"{len(touch)} controls measured, {len(below)} below 24x24 CSS px",
           {"below_24": below[:15], "measured_count": len(touch)})

    # 5. Empty invalid submission
    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(50)
    place_selector = None
    for sel in ['[data-hook="place-order"]', 'button[type="submit"]', '#place-order']:
        if has_selector(page, sel):
            place_selector = sel
            break
    if place_selector:
        page.locator(place_selector).first.click()
        page.wait_for_timeout(180)
    empty_state = query_state(page)
    page.screenshot(path=str(shots_dir / "02-empty-submit-error-summary.png"), full_page=True)
    record(steps, "empty_submit", "click Place order with all fields blank", place_selector or "n/a",
           "error summary appears, focus moved to summary, no confirmation",
           {"state": empty_state})

    # Follow an error summary link if present
    summary_link_sel = '[data-hook="error-summary"] li a, #error-summary li a, [data-hook="error-summary"] a[href^="#"]'
    if has_selector(page, summary_link_sel):
        first_link = page.locator(summary_link_sel).first
        try:
            first_link_text = first_link.text_content()
        except Exception:
            first_link_text = None
        try:
            first_link.click(timeout=1200)
            page.wait_for_timeout(90)
            record(steps, "error_summary_link_click", "click first grouped link",
                   first_link_text or "?", "focus/scroll should move to field",
                   {"active": query_state(page)["active_element"]})
        except Exception as e:
            record(steps, "error_summary_link_click", "click first grouped link",
                   first_link_text or "?", f"click failed: {e}", {})
    else:
        record(steps, "error_summary_link_click", "no summary links found",
               "n/a", "candidate has no grouped-link summary", {})

    # 6. Fill contact
    def fill_if(selector, value):
        if has_selector(page, selector):
            try:
                page.locator(selector).first.fill(value)
                return True
            except Exception:
                return False
        return False

    fill_if("#contact-name", "Alex Morgan")
    fill_if("#contact-email", "alex.morgan@example.invalid")
    fill_if("#contact-phone", "+61 400 000 000")
    record(steps, "fill_contact", "fill contact fields", "contact section",
           "values entered", {"state_after": query_state(page)})

    # 7. Fill delivery
    fill_if("#address-line1", "42 Fiction Lane")
    fill_if("#address-city", "Sampleton")
    fill_if("#address-state", "NSW")
    fill_if("#address-postcode", "2000")
    fill_if("#address-country", "Australia")
    record(steps, "fill_delivery", "fill delivery fields", "delivery section",
           "values entered", {"state_after": query_state(page)})

    # 8. Invalid then valid postcode correction
    fill_if("#address-postcode", "abcd")
    try:
        page.locator("#address-postcode").blur()
    except Exception:
        pass
    page.wait_for_timeout(90)
    bad_state = query_state(page)
    page.screenshot(path=str(shots_dir / "03-error-recovery-invalid-postcode.png"), full_page=True)
    record(steps, "invalid_postcode_blur", "type invalid postcode then blur",
           "#address-postcode", "field-level error should appear inline", {"state": bad_state})

    fill_if("#address-postcode", "2000")
    try:
        page.locator("#address-postcode").blur()
    except Exception:
        pass
    page.wait_for_timeout(90)
    record(steps, "correct_postcode", "restore valid postcode", "#address-postcode",
           "inline error should clear", {"state": query_state(page)})

    # 9. Shipping change (express) then back
    if has_selector(page, "#shipping-express"):
        try:
            page.locator("#shipping-express").check()
            page.wait_for_timeout(90)
        except Exception:
            pass
        record(steps, "shipping_change_express", "select Express radio", "#shipping-express",
               "totals should update", {"state": query_state(page)})
    if has_selector(page, "#shipping-standard"):
        try:
            page.locator("#shipping-standard").check()
            page.wait_for_timeout(80)
        except Exception:
            pass

    # 10. Save progress explicit (if action exists)
    save_now_sel = '[data-action="save-now"]'
    if has_selector(page, save_now_sel):
        try:
            page.locator(save_now_sel).first.click(timeout=1200)
            page.wait_for_timeout(90)
            record(steps, "save_progress", "click Save progress", save_now_sel,
                   "explicit save; status announces",
                   {"state": query_state(page)})
        except Exception as e:
            record(steps, "save_progress", "click Save progress", save_now_sel,
                   f"click failed: {e}", {})
    else:
        record(steps, "save_progress", "no explicit save-now action", "n/a",
               "candidate autosaves silently or lacks explicit save control", {})

    # 11. Payment fill and secret non-persistence check
    fill_if("#card-number", "4111111111111111")
    fill_if("#card-expiry", "12/34")
    fill_if("#card-security", "123")
    fill_if("#card-name", "Alex Morgan")
    page.wait_for_timeout(120)
    secret_check = page.evaluate(
        """() => {
        try {
            const keys = [];
            for (let i = 0; i < localStorage.length; i++) keys.push(localStorage.key(i));
            const results = keys.map(k => {
                const raw = localStorage.getItem(k);
                return {
                    key: k,
                    length: raw ? raw.length : 0,
                    has_card_number: raw ? /(card[-_ ]?number|4111111111111111)/i.test(raw) : false,
                    has_card_security: raw ? /(card[-_ ]?security|\\bcvv\\b|\\bcvc\\b|\\bsecurity[-_ ]?code\\b)/i.test(raw) : false,
                    has_card_expiry: raw ? /(card[-_ ]?expiry|12\\/34)/i.test(raw) : false,
                };
            });
            return { keys, results };
        } catch (e) { return { error: String(e) }; }
    }"""
    )
    record(steps, "payment_secret_check", "inspect localStorage after payment fill",
           "localStorage.*",
           "must not contain card-number/card-security/card-expiry",
           {"localstorage": secret_check})

    # 12. Compact-completed toggle
    if has_selector(page, "#compact-completed"):
        page.evaluate("() => { document.activeElement && document.activeElement.blur && document.activeElement.blur(); document.body.focus(); }")
        page.wait_for_timeout(80)
        try:
            page.locator("#compact-completed").check()
            page.wait_for_timeout(180)
        except Exception:
            pass
        compact_visibility = page.evaluate(
            """() => {
            const out = {};
            ['contact','delivery','shipping','payment','review'].forEach(id => {
                const s = document.querySelector('#' + id);
                if (!s) { out[id] = null; return; }
                const body = s.querySelector('[data-section-body]');
                const summary = s.querySelector('[data-completed-summary]');
                const edit = s.querySelector('[data-edit-section]');
                out[id] = {
                    compacted: s.dataset.compacted || null,
                    body_hidden: !!body?.hidden,
                    summary_hidden: !!summary?.hidden,
                    edit_visible: !!(edit && edit.offsetParent !== null),
                };
            });
            return out;
        }"""
        )
        record(steps, "compact_toggle_on", "toggle compact completed sections", "#compact-completed",
               "completed sections should compact; hidden fields removed from focus",
               {"state": query_state(page), "section_visibility": compact_visibility})
        page.screenshot(path=str(shots_dir / "04-compact-completed-on.png"), full_page=True)

        # Verify no focus lands in hidden fields via tab from top
        compact_tab_order = keyboard_tab_traverse(page, max_steps=40)
        (logs_dir / "tab-order-compact.json").write_text(json.dumps(compact_tab_order, indent=2))
        compact_hidden_leaks = [i for i, x in enumerate(compact_tab_order) if x and x.get("hidden_ancestor")]
        record(steps, "compact_focus_audit", "Tab*40 after compact on", "document",
               f"hidden-ancestor focus leaks: {len(compact_hidden_leaks)}",
               {"leaks": compact_hidden_leaks})

        # Edit a compacted section via Edit button
        page.evaluate("() => { document.activeElement && document.activeElement.blur && document.activeElement.blur(); document.body.focus(); }")
        page.wait_for_timeout(120)
        edit_sel = '#contact button[data-edit-section="contact"], button[data-edit-section="contact"]'
        edited = False
        if has_selector(page, edit_sel):
            try:
                # Re-check compact-toggle to ensure contact is currently compacted
                edit_visible = page.evaluate(
                    """() => {
                    const b = document.querySelector('button[data-edit-section="contact"]');
                    return b ? { offsetParent: !!b.offsetParent } : null;
                }"""
                )
                if edit_visible and not edit_visible["offsetParent"]:
                    page.locator("#compact-completed").uncheck()
                    page.wait_for_timeout(80)
                    page.evaluate("() => { document.body.focus(); }")
                    page.locator("#compact-completed").check()
                    page.wait_for_timeout(140)
                page.locator(edit_sel).first.click(force=True, timeout=1500)
                page.wait_for_timeout(90)
                edited = True
                record(steps, "edit_contact_from_compact", "click Edit contact", edit_sel,
                       "section re-expands and first field focused",
                       {"state": query_state(page)})
                page.screenshot(path=str(shots_dir / "05-edit-compact-section.png"), full_page=True)
            except Exception as e:
                record(steps, "edit_contact_from_compact", "click Edit contact", edit_sel,
                       f"click failed: {e}", {})
        else:
            record(steps, "edit_contact_from_compact", "no edit-section button for contact",
                   "n/a", "compact/edit flow not offered", {})

        # Turn compact off again for review clarity
        try:
            page.locator("#compact-completed").uncheck()
            page.wait_for_timeout(60)
        except Exception:
            pass
    else:
        record(steps, "compact_toggle_on", "no #compact-completed toggle present", "n/a",
               "candidate lacks compact-completed feature", {})

    # 13. Clear-progress confirm/cancel/Escape (if provided)
    clear_sel = '[data-action="clear-progress"]'
    if has_selector(page, clear_sel):
        try:
            page.locator(clear_sel).first.click(timeout=1500)
            page.wait_for_timeout(90)
            record(steps, "clear_progress_prompt", "click Clear saved progress", clear_sel,
                   "confirmation region appears, Cancel focused",
                   {"state": query_state(page)})
            page.screenshot(path=str(shots_dir / "06-clear-confirm-dialog.png"), full_page=True)

            cancel_sel = '[data-action="cancel-clear"]'
            if has_selector(page, cancel_sel):
                page.locator(cancel_sel).first.click(timeout=1200)
                page.wait_for_timeout(90)
                record(steps, "clear_progress_cancel", "click Cancel in clear dialog", cancel_sel,
                       "confirmation hidden, focus returns to Clear button, values preserved",
                       {"state": query_state(page)})

            page.locator(clear_sel).first.click(timeout=1500)
            page.wait_for_timeout(80)
            page.keyboard.press("Escape")
            page.wait_for_timeout(80)
            record(steps, "clear_progress_escape", "Escape from clear dialog", "keydown Escape",
                   "same as cancel: dialog dismisses without clearing",
                   {"state": query_state(page)})
        except Exception as e:
            record(steps, "clear_progress_flow", "clear-progress flow", clear_sel,
                   f"failed: {e}", {})
    else:
        record(steps, "clear_progress_flow", "no clear-progress action present", "n/a",
               "candidate lacks explicit destructive-clear affordance", {})

    # 14. Missing review checkbox → submit → grouped error including review
    if place_selector and has_selector(page, "#review-confirmation"):
        try:
            page.locator("#review-confirmation").uncheck()
        except Exception:
            pass
        page.locator(place_selector).first.click()
        page.wait_for_timeout(160)
        record(steps, "submit_without_review", "Place order without review checkbox",
               "form submit", "review error entry appears; other sections valid",
               {"state": query_state(page)})
        page.screenshot(path=str(shots_dir / "07-review-required-error.png"), full_page=True)

    # 15. Check review checkbox
    if has_selector(page, "#review-confirmation"):
        try:
            page.locator("#review-confirmation").check()
            page.wait_for_timeout(70)
        except Exception:
            pass

    # 16. Valid submission → SYN-2048 confirmation
    if place_selector:
        page.locator(place_selector).first.click()
        page.wait_for_timeout(700)
    conf_state = query_state(page)
    record(steps, "valid_submit", "Place order with valid fields + review checked", "form submit",
           "confirmation should appear; place-order disabled",
           {"state": conf_state})
    page.screenshot(path=str(shots_dir / "08-confirmation.png"), full_page=True)

    confirmation_text = page.evaluate(
        """() => {
        const roots = document.querySelectorAll('[data-hook="confirmation"], #confirmation, #confirmation-content, [data-hook="placed-banner"], #placed-banner');
        return Array.from(roots).map(r => (r.textContent || '').trim().slice(0, 400));
    }"""
    )
    has_syn2048 = any("SYN-2048" in t for t in confirmation_text)
    record(steps, "confirmation_id_check", "look for SYN-2048 in confirmation region",
           "confirmation region", f"SYN-2048 present: {has_syn2048}",
           {"confirmation_text_snippets": confirmation_text, "has_syn2048": has_syn2048})

    # 17. Duplicate placement attempt (click again + dispatchEvent)
    if place_selector:
        try:
            page.locator(place_selector).first.click(force=True, timeout=1500)
        except Exception:
            pass
        page.wait_for_timeout(220)
        record(steps, "duplicate_submit_attempted", "click Place order again after confirmation",
               "form submit", "no duplicate confirmation; status conveys already confirmed",
               {"state": query_state(page)})

    double_dispatch = page.evaluate(
        """() => {
        const before = document.querySelectorAll('[data-hook="confirmation-id"], #confirmation-content, [data-hook="confirmation"]').length;
        const form = document.querySelector('#checkout-form, form');
        if (form) form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        const after = document.querySelectorAll('[data-hook="confirmation-id"], #confirmation-content, [data-hook="confirmation"]').length;
        return { before, after };
    }"""
    )
    record(steps, "duplicate_dispatch_submit", "dispatchEvent(submit) after confirmation",
           "form", f"confirmation nodes before {double_dispatch['before']} after {double_dispatch['after']}",
           {"double_dispatch": double_dispatch, "state": query_state(page)})

    # 18. External-request log
    record(steps, "network_summary", "read collected network log", "context",
           f"{len(external_requests)} external requests captured",
           {"external_requests": external_requests, "total_requests_seen": len(net_requests)})

    # 19. Reload safe-restore + payment-secret non-persistence
    page.reload(wait_until="load")
    page.wait_for_timeout(250)
    reload_state = page.evaluate(
        """() => {
        const q = (s) => document.querySelector(s);
        return {
            contact_name: q('#contact-name')?.value,
            contact_email: q('#contact-email')?.value,
            contact_phone: q('#contact-phone')?.value,
            address_line1: q('#address-line1')?.value,
            address_city: q('#address-city')?.value,
            address_state: q('#address-state')?.value,
            address_postcode: q('#address-postcode')?.value,
            address_country: q('#address-country')?.value,
            card_number: q('#card-number')?.value,
            card_expiry: q('#card-expiry')?.value,
            card_security: q('#card-security')?.value,
            card_name: q('#card-name')?.value,
            shipping_value: q('input[name="shipping"]:checked')?.value,
            status: (q('[data-hook="status"], #checkout-status')?.textContent || '').trim().slice(0, 200),
            confirmation_visible: (() => {
                const c = q('[data-hook="confirmation"], #confirmation, #confirmation-content');
                if (!c) return false;
                return !(c.hidden || getComputedStyle(c).display === 'none');
            })(),
            place_order_disabled: !!q('[data-hook="place-order"], button[type="submit"]')?.disabled,
        };
    }"""
    )
    record(steps, "reload_restore", "page.reload() after successful submit",
           "browser reload",
           "safe fields restore, payment fields empty, confirmation hidden, place-order re-enabled",
           {"reload_state": reload_state})
    page.screenshot(path=str(shots_dir / "09-post-reload-restored.png"), full_page=True)

    # 20. Confirm clear-progress actually clears (only if supported)
    if has_selector(page, clear_sel):
        try:
            page.locator(clear_sel).first.click(timeout=1500)
            page.wait_for_timeout(90)
            confirm_clear_sel = '[data-action="confirm-clear"]'
            if has_selector(page, confirm_clear_sel):
                page.locator(confirm_clear_sel).first.click(timeout=1500)
                page.wait_for_load_state("load")
                page.wait_for_timeout(250)
                cleared_state = page.evaluate(
                    """() => {
                    const q = (s) => document.querySelector(s);
                    const keys = [];
                    for (let i = 0; i < localStorage.length; i++) keys.push(localStorage.key(i));
                    return {
                        contact_name: q('#contact-name')?.value,
                        address_postcode: q('#address-postcode')?.value,
                        localstorage_keys: keys,
                        status: (q('[data-hook="status"], #checkout-status')?.textContent || '').trim().slice(0, 200),
                    };
                }"""
                )
                record(steps, "clear_confirm_action", "confirm Clear saved progress", confirm_clear_sel,
                       "reloads, safe fields empty, localstorage cleared",
                       {"state": cleared_state})
                page.screenshot(path=str(shots_dir / "10-after-clear-confirmed.png"), full_page=True)
        except Exception as e:
            record(steps, "clear_confirm_action", "confirm Clear saved progress", clear_sel,
                   f"failed: {e}", {})
    else:
        # Verify that reload alone leaves payment empty (already recorded) and confirm no extra destructive-safety
        record(steps, "clear_confirm_action", "no clear-progress affordance", "n/a",
               "candidate does not provide user-initiated clear-all", {})

    # Save outputs
    (logs_dir / "console.json").write_text(json.dumps(console_msgs, indent=2))
    (logs_dir / "network.json").write_text(json.dumps({
        "total_requests": len(net_requests),
        "external_requests": external_requests,
        "sample_requests": net_requests[:20],
    }, indent=2))

    transcript = {
        "candidate_label": code,
        "bundle_name": bundle_name,
        "iteration_id": "final",
        "viewport": VIEWPORT,
        "reduced_motion": "reduce",
        "candidate_url": candidate_url,
        "steps": steps,
        "console": console_msgs,
        "external_requests": external_requests,
        "total_network_requests_including_local_asset_loads": len(net_requests),
    }
    (JUDGE_DIR / f"navigation-transcript-{code}.json").write_text(json.dumps(transcript, indent=2))

    browser.close()

    return {
        "candidate": code,
        "bundle": bundle_name,
        "steps": len(steps),
        "console_msgs": len(console_msgs),
        "external_requests": len(external_requests),
        "focus_leaks": hidden_leaks,
        "touch_targets_below_24": [t for t in touch if t["below_24"]],
        "has_syn2048": has_syn2048,
        "confirmation_text_snippets": confirmation_text,
    }


def main():
    summary = {}
    with sync_playwright() as pw:
        for bundle_name, code in CANDIDATES:
            print(f"=== operating {bundle_name} (label {code}) ===", flush=True)
            summary[code] = run_candidate(pw, bundle_name, code)
            print(f"    done: {summary[code]}", flush=True)
    (JUDGE_DIR / "logs" / "run-summary.json").write_text(json.dumps(summary, indent=2))
    print("ALL DONE")


if __name__ == "__main__":
    main()
