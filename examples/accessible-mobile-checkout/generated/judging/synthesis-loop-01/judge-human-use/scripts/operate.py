"""
Judge-local Playwright driver for candidate-a (synthesis-loop-01).

Exercises the candidate at 390x844 with keyboard, captures screenshots and
a full navigation transcript, and records every console message and every
network request the page attempts. All outputs are judge-local.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

JUDGE_DIR = Path(__file__).resolve().parent.parent
CANDIDATE_HTML = (
    JUDGE_DIR.parent.parent.parent
    / "synthesis"
    / "loop-01"
    / "index.html"
)
SHOTS = JUDGE_DIR / "screenshots"
LOGS = JUDGE_DIR / "logs"
SHOTS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

VIEWPORT = {"width": 390, "height": 844}


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
        const badges = Array.from(document.querySelectorAll('[data-section-state]')).map(el => ({
            section: el.closest('.task-section')?.id || null,
            text: el.textContent.trim(),
            classes: el.className,
        }));
        const progress = q('[data-hook="progress"]');
        const summary = q('[data-hook="error-summary"]');
        const status = q('[data-hook="status"]');
        const confirmationVisible = !q('[data-hook="confirmation"]').hidden;
        const placeOrder = q('[data-hook="place-order"]');
        const clearConfirmVisible = !q('#clear-confirm').hidden;
        return {
            progress_valuenow: progress?.getAttribute('aria-valuenow'),
            progress_valuetext: progress?.getAttribute('aria-valuetext'),
            error_summary_hidden: !!summary?.hidden,
            error_summary_text: summary?.textContent?.trim().slice(0, 240) || '',
            status_text: status?.textContent?.trim().slice(0, 240) || '',
            confirmation_visible: confirmationVisible,
            confirmation_id_text: q('[data-hook="confirmation-id"]')?.textContent || null,
            place_order_disabled: !!placeOrder?.disabled,
            place_order_present: !!placeOrder,
            place_order_aria_busy: placeOrder?.getAttribute('aria-busy') || null,
            clear_confirm_visible: clearConfirmVisible,
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
                grand: q('[data-hook="total"]')?.textContent,
                due: q('[data-review-total]')?.textContent,
            },
            saved_localstorage_present: (() => {
                try { return !!localStorage.getItem('northstar-synthesis-checkout'); } catch { return null; }
            })(),
            saved_localstorage_has_card: (() => {
                try {
                    const raw = localStorage.getItem('northstar-synthesis-checkout');
                    if (!raw) return false;
                    return /card-number|card-security|card-expiry/i.test(raw);
                } catch { return null; }
            })(),
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
            const key = el.id || (el.getAttribute('data-hook') || '') + '|' + el.tagName + '|' + (el.textContent || '').trim().slice(0, 30);
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


def keyboard_tab_traverse(page, max_steps=40):
    order = []
    page.evaluate("() => { document.body.focus(); }")
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


def main():
    console_msgs = []
    external_requests = []
    net_requests = []
    steps = []

    with sync_playwright() as pw:
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

        candidate_url = CANDIDATE_HTML.resolve().as_uri()
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
                skip_links: pick('a.skip-link'),
                headings: Array.from(document.querySelectorAll('h1,h2,h3')).map(h => ({
                    level: h.tagName,
                    id: h.id || null,
                    text: (h.textContent || '').trim().slice(0, 80),
                })),
            };
        }"""
        )
        (LOGS / "landmarks.json").write_text(json.dumps(landmarks, indent=2))

        page.screenshot(path=str(SHOTS / "01-initial-390x844.png"), full_page=True)
        record(steps, "initial_load", "goto file:", "candidate index.html", "loaded 390x844, reduced motion",
               {"state": query_state(page), "url": candidate_url})

        # 2. Keyboard traversal from top
        tab_order = keyboard_tab_traverse(page, max_steps=50)
        (LOGS / "tab-order.json").write_text(json.dumps(tab_order, indent=2))
        record(steps, "keyboard_tab_traverse", "Tab*50", "document", "captured focus order",
               {"visible_focus_check": "tab_order in logs/tab-order.json",
                "hidden_ancestor_leaks": [i for i, x in enumerate(tab_order) if x and x.get("hidden_ancestor")]})

        # 3. Section nav links (anchor jump)
        for anchor in ["#contact", "#delivery", "#shipping", "#payment", "#review"]:
            page.locator(f'nav.section-nav a[href="{anchor}"]').click()
            page.wait_for_timeout(80)
            record(steps, f"nav_click_{anchor}", "click section-nav link", anchor, "scrolled/anchor navigated",
                   {"y": page.evaluate("window.scrollY"), "hash": page.evaluate("location.hash")})

        # 4. Touch target audit
        touch = touch_target_sizes(page)
        (LOGS / "touch-targets.json").write_text(json.dumps(touch, indent=2))
        below = [t for t in touch if t["below_24"]]
        record(steps, "touch_target_audit", "measure interactive rects", "all controls",
               f"{len(touch)} controls measured, {len(below)} below 24x24 CSS px",
               {"below_24": below[:10]})

        # 5. Empty invalid submission
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(50)
        page.locator('[data-hook="place-order"]').click()
        page.wait_for_timeout(150)
        empty_state = query_state(page)
        page.screenshot(path=str(SHOTS / "02-empty-submit-error-summary.png"), full_page=True)
        record(steps, "empty_submit", "click Place order with all fields blank", "form",
               "error summary appears, focus moved to summary, no confirmation",
               {"state": empty_state})

        # Follow an error summary link
        first_link = page.locator('[data-hook="error-summary"] li a').first
        first_link_text = first_link.text_content()
        first_link.click()
        page.wait_for_timeout(80)
        record(steps, "error_summary_link_click", "click first grouped link",
               first_link_text, "focus/scroll should move to first field of that section",
               {"active": query_state(page)["active_element"]})

        # 6. Fill contact
        page.locator("#contact-name").fill("Alex Morgan")
        page.locator("#contact-email").fill("alex.morgan@example.invalid")
        page.locator("#contact-phone").fill("+61 400 000 000")
        record(steps, "fill_contact", "fill contact fields", "contact section",
               "values entered; per-field blur validation exercised", {"state_after": query_state(page)})

        # 7. Fill delivery
        page.locator("#address-line1").fill("42 Fiction Lane")
        page.locator("#address-city").fill("Sampleton")
        page.locator("#address-state").fill("NSW")
        page.locator("#address-postcode").fill("2000")
        page.locator("#address-country").fill("Australia")
        record(steps, "fill_delivery", "fill delivery fields", "delivery section",
               "values entered", {"state_after": query_state(page)})

        # 8. Invalid then valid postcode correction
        page.locator("#address-postcode").fill("abcd")
        page.locator("#address-postcode").blur()
        page.wait_for_timeout(80)
        bad_state = query_state(page)
        page.screenshot(path=str(SHOTS / "03-error-recovery-invalid-postcode.png"), full_page=True)
        record(steps, "invalid_postcode_blur", "type invalid postcode then blur",
               "#address-postcode", "field-level error should appear inline", {"state": bad_state})

        page.locator("#address-postcode").fill("2000")
        page.locator("#address-postcode").blur()
        page.wait_for_timeout(80)
        record(steps, "correct_postcode", "restore valid postcode", "#address-postcode",
               "inline error should clear", {"state": query_state(page)})

        # 9. Shipping change (express) — updates totals
        page.locator("#shipping-express").check()
        page.wait_for_timeout(80)
        record(steps, "shipping_change_express", "select Express radio", "shipping",
               "totals should update to AUD 100.50",
               {"state": query_state(page)})
        page.locator("#shipping-standard").check()
        page.wait_for_timeout(80)

        # 10. Save progress explicit
        page.locator('[data-action="save-now"]').click()
        page.wait_for_timeout(80)
        record(steps, "save_progress", "click Save progress", '[data-action="save-now"]',
               "explicit save; status announces",
               {"state": query_state(page)})

        # 11. Verify payment secrets not in localStorage after fill
        page.locator("#card-number").fill("4111111111111111")
        page.locator("#card-expiry").fill("12/34")
        page.locator("#card-security").fill("123")
        page.locator("#card-name").fill("Alex Morgan")
        page.wait_for_timeout(80)
        secret_check = page.evaluate(
            """() => {
            try {
                const raw = localStorage.getItem('northstar-synthesis-checkout');
                return {
                    present: !!raw,
                    has_card_key: raw ? /card-number|card-security|card-expiry/i.test(raw) : false,
                    length: raw ? raw.length : 0,
                    keys: raw ? Object.keys(JSON.parse(raw).fields || {}) : [],
                };
            } catch (e) { return { error: String(e) }; }
        }"""
        )
        record(steps, "payment_secret_check", "inspect localStorage after payment fill",
               "localStorage.northstar-synthesis-checkout",
               "must not contain card-number/card-security/card-expiry",
               {"localstorage": secret_check})

        # 12. Compact-completed toggle — check hidden fields leave focus order
        # Move focus fully out of any task section first, so refreshCompactSections
        # can compact every already-complete section including payment.
        page.evaluate("() => { document.activeElement && document.activeElement.blur && document.activeElement.blur(); document.body.focus(); }")
        page.wait_for_timeout(60)
        page.locator("#compact-completed").check()
        page.wait_for_timeout(160)
        compact_visibility = page.evaluate(
            """() => {
            const out = {};
            ['contact','delivery','shipping','payment'].forEach(id => {
                const s = document.querySelector('#' + id);
                const body = s.querySelector('[data-section-body]');
                const summary = s.querySelector('[data-completed-summary]');
                const edit = s.querySelector('[data-edit-section]');
                out[id] = {
                    compacted: s.dataset.compacted,
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
        page.screenshot(path=str(SHOTS / "04-compact-completed-on.png"), full_page=True)

        # Verify no focus lands in hidden fields via tab from top
        compact_tab_order = keyboard_tab_traverse(page, max_steps=40)
        (LOGS / "tab-order-compact.json").write_text(json.dumps(compact_tab_order, indent=2))
        compact_hidden_leaks = [i for i, x in enumerate(compact_tab_order) if x and x.get("hidden_ancestor")]
        record(steps, "compact_focus_audit", "Tab*40 after compact on", "document",
               f"hidden-ancestor focus leaks: {len(compact_hidden_leaks)}",
               {"leaks": compact_hidden_leaks})

        # Edit a compacted section via Edit button — make sure focus is outside sections first
        page.evaluate("() => { document.activeElement && document.activeElement.blur && document.activeElement.blur(); document.body.focus(); }")
        page.wait_for_timeout(120)
        # Re-check compact so any newly non-focused sections compact
        edit_btn = page.locator('#contact button[data-edit-section="contact"]')
        edit_visible = page.evaluate(
            """() => {
            const b = document.querySelector('#contact button[data-edit-section="contact"]');
            return b ? { offsetParent: !!b.offsetParent, hidden_ancestor: (function(){ let c=b; while(c){ if(c.hidden) return true; c=c.parentElement; } return false; })() } : null;
        }"""
        )
        if edit_visible and not edit_visible["offsetParent"]:
            # Force-compact contact via keyboard: click compact-toggle off then on to retrigger
            page.locator("#compact-completed").uncheck()
            page.wait_for_timeout(80)
            page.evaluate("() => { document.body.focus(); }")
            page.locator("#compact-completed").check()
            page.wait_for_timeout(120)
        edit_btn.click(force=True)
        page.wait_for_timeout(80)
        record(steps, "edit_contact_from_compact", "click Edit contact", "[data-edit-section=contact]",
               "section re-expands and first field focused",
               {"state": query_state(page)})
        page.screenshot(path=str(SHOTS / "05-edit-compact-section.png"), full_page=True)

        # Turn compact off again for review clarity
        page.locator("#compact-completed").uncheck()
        page.wait_for_timeout(60)

        # 13. Clear-progress confirm/cancel/Escape
        page.locator('[data-action="clear-progress"]').click()
        page.wait_for_timeout(80)
        record(steps, "clear_progress_prompt", "click Clear saved progress", "[data-action=clear-progress]",
               "confirmation region appears, Cancel focused",
               {"state": query_state(page)})
        page.screenshot(path=str(SHOTS / "06-clear-confirm-dialog.png"), full_page=True)

        page.locator('[data-action="cancel-clear"]').click()
        page.wait_for_timeout(80)
        record(steps, "clear_progress_cancel", "click Cancel in clear dialog", "[data-action=cancel-clear]",
               "confirmation hidden, focus returns to Clear button, values preserved",
               {"state": query_state(page)})

        # Escape dismiss
        page.locator('[data-action="clear-progress"]').click()
        page.wait_for_timeout(60)
        page.keyboard.press("Escape")
        page.wait_for_timeout(60)
        record(steps, "clear_progress_escape", "Escape from clear dialog", "keydown Escape",
               "same as cancel: dialog dismisses without clearing",
               {"state": query_state(page)})

        # 14. Missing review checkbox → submit → grouped error including review
        page.locator('[data-hook="place-order"]').click()
        page.wait_for_timeout(120)
        record(steps, "submit_without_review", "Place order without review checkbox",
               "form submit", "review error entry appears; other sections valid",
               {"state": query_state(page)})
        page.screenshot(path=str(SHOTS / "07-review-required-error.png"), full_page=True)

        # 15. Check review checkbox
        page.locator("#review-confirmation").check()
        page.wait_for_timeout(60)

        # 16. Valid submission → SYN-2048 confirmation
        page.locator('[data-hook="place-order"]').click()
        page.wait_for_timeout(600)
        conf_state = query_state(page)
        record(steps, "valid_submit", "Place order with valid fields + review checked", "form submit",
               "confirmation SYN-2048 appears; place-order disabled",
               {"state": conf_state})
        page.screenshot(path=str(SHOTS / "08-confirmation-SYN-2048.png"), full_page=True)

        # 17. Duplicate placement attempt
        page.locator('[data-hook="place-order"]').click(force=True)
        page.wait_for_timeout(200)
        record(steps, "duplicate_submit_attempted", "click Place order again after confirmation",
               "form submit", "no duplicate confirmation; status conveys already confirmed",
               {"state": query_state(page)})

        # Also try form.dispatchEvent submit
        double_dispatch = page.evaluate(
            """() => {
            const before = document.querySelectorAll('[data-hook="confirmation-id"]').length;
            const form = document.querySelector('#checkout-form');
            form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            const after = document.querySelectorAll('[data-hook="confirmation-id"]').length;
            return { before, after };
        }"""
        )
        record(steps, "duplicate_dispatch_submit", "dispatchEvent(submit) after confirmation",
               "form", f"confirmation nodes before {double_dispatch['before']} after {double_dispatch['after']}",
               {"double_dispatch": double_dispatch, "state": query_state(page)})

        # 18. External-request log for SYN-2048 pass (no network)
        record(steps, "network_summary", "read collected network log", "context",
               f"{len(external_requests)} external requests captured",
               {"external_requests": external_requests, "total_requests_seen": len(net_requests)})

        # 19. Reload safe-restore + payment-secret non-persistence
        page.reload(wait_until="load")
        page.wait_for_timeout(200)
        reload_state = page.evaluate(
            """() => {
            const q = (s) => document.querySelector(s);
            return {
                contact_name: q('#contact-name').value,
                contact_email: q('#contact-email').value,
                contact_phone: q('#contact-phone').value,
                address_line1: q('#address-line1').value,
                address_city: q('#address-city').value,
                address_state: q('#address-state').value,
                address_postcode: q('#address-postcode').value,
                address_country: q('#address-country').value,
                card_number: q('#card-number').value,
                card_expiry: q('#card-expiry').value,
                card_security: q('#card-security').value,
                card_name: q('#card-name').value,
                shipping_value: q('input[name="shipping"]:checked')?.value,
                status: q('[data-hook="status"]').textContent.trim().slice(0, 200),
                confirmation_visible: !q('[data-hook="confirmation"]').hidden,
                place_order_disabled: q('[data-hook="place-order"]').disabled,
            };
        }"""
        )
        record(steps, "reload_restore", "page.reload() after successful submit",
               "browser reload",
               "safe fields restore, payment fields empty, confirmation hidden, place-order re-enabled",
               {"reload_state": reload_state})
        page.screenshot(path=str(SHOTS / "09-post-reload-restored.png"), full_page=True)

        # Sanity: Confirmation state must be gone; place order must be reset
        # But watch for duplicate-safe design: after reload placement flag reset is expected.

        # 20. Confirm clear-progress actually clears
        page.locator('[data-action="clear-progress"]').click()
        page.wait_for_timeout(80)
        page.locator('[data-action="confirm-clear"]').click()
        # Reload will happen; wait then check
        page.wait_for_load_state("load")
        page.wait_for_timeout(200)
        cleared_state = page.evaluate(
            """() => {
            const q = (s) => document.querySelector(s);
            return {
                contact_name: q('#contact-name').value,
                address_postcode: q('#address-postcode').value,
                localstorage_present: (() => { try { return !!localStorage.getItem('northstar-synthesis-checkout'); } catch { return null; }})(),
                status: q('[data-hook="status"]').textContent.trim().slice(0, 200),
            };
        }"""
        )
        record(steps, "clear_confirm_action", "confirm Clear saved progress", "[data-action=confirm-clear]",
               "reloads, safe fields empty, localstorage cleared",
               {"state": cleared_state})
        page.screenshot(path=str(SHOTS / "10-after-clear-confirmed.png"), full_page=True)

        # Save outputs
        (LOGS / "console.json").write_text(json.dumps(console_msgs, indent=2))
        (LOGS / "network.json").write_text(json.dumps({
            "total_requests": len(net_requests),
            "external_requests": external_requests,
            "sample_requests": net_requests[:20],
        }, indent=2))

        transcript = {
            "candidate_id": "candidate-a",
            "iteration_id": "synthesis-loop-01",
            "viewport": VIEWPORT,
            "reduced_motion": "reduce",
            "candidate_url": candidate_url,
            "steps": steps,
            "console": console_msgs,
            "external_requests": external_requests,
            "total_network_requests_including_local_asset_loads": len(net_requests),
        }
        (JUDGE_DIR / "navigation-transcript-a.json").write_text(json.dumps(transcript, indent=2))

        browser.close()

    print("DONE")
    print("external_requests:", len(external_requests))
    print("console_msgs:", len(console_msgs))


if __name__ == "__main__":
    main()
