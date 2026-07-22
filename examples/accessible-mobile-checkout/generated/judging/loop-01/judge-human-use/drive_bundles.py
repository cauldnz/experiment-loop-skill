"""
Blind human-use judge driver for accessible-mobile-checkout blind bundles.

Serves each candidate over a local file:// URL (they are static HTML) and
exercises the required qualitative-lens scenarios. Emits one navigation
transcript JSON per candidate plus screenshots.

This script does NOT alter any bundle. It only reads and drives them.
"""

import json
import os
import pathlib
import re
import time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = pathlib.Path(__file__).resolve().parents[0]
JUDGE = pathlib.Path(
    r"<experiment-workspace>\generated\judging\loop-01\judge-human-use"
)
BLIND = pathlib.Path(
    r"<experiment-workspace>\generated\judging\blind-loop-01"
)
SHOTS = JUDGE / "screenshots"

CANDIDATE_ORDER = ["candidate-c", "candidate-b", "candidate-a"]

FIXTURE = {
    "contact-name": "Alex Morgan",
    "contact-email": "alex.morgan@example.invalid",
    "contact-phone": "+61 400 000 000",
    "address-line1": "42 Fiction Lane",
    "address-city": "Sampleton",
    "address-state": "NSW",
    "address-postcode": "2000",
    "address-country": "Australia",
    "card-number": "4111 1111 1111 1111",
    "card-expiry": "12/34",
    "card-security": "123",
    "card-name": "Alex Morgan",
}

# Mobile viewports
VIEWPORT_DEFAULT = {"width": 390, "height": 844}
VIEWPORT_SMALL = {"width": 320, "height": 568}


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def snap(page, cdir, name):
    p = SHOTS / cdir / f"{name}.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=str(p), full_page=True)
    except Exception as e:
        print(f"screenshot failed {name}: {e}")
    return str(p.relative_to(JUDGE.parent.parent.parent.parent.parent.parent.parent.parent)) if False else f"generated/judging/loop-01/judge-human-use/screenshots/{cdir}/{name}.png"


def try_fill(page, selector, value):
    try:
        page.fill(selector, value)
        return True
    except Exception as e:
        return str(e)


def get_visible_step(page):
    # candidate-c only shows one step at a time via .step-pending
    try:
        r = page.evaluate("""
          () => Array.from(document.querySelectorAll('.step')).map(s => ({step: s.dataset.step, hidden: s.classList.contains('step-pending'), ariaHidden: s.getAttribute('aria-hidden')}))
        """)
        return r
    except Exception:
        return None


def run_candidate(playwright, candidate_dir_name):
    """Return a transcript dict for one candidate."""
    entries = []
    console_msgs = []
    page_errors = []

    def add(action, outcome, screenshot=None, extra=None):
        item = {"t": now_iso(), "action": action, "outcome": outcome}
        if screenshot:
            item["screenshot"] = screenshot
        if extra:
            item["extra"] = extra
        entries.append(item)

    browser = playwright.chromium.launch()
    ctx = browser.new_context(viewport=VIEWPORT_DEFAULT, device_scale_factor=2, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    page.on("console", lambda m: console_msgs.append({"type": m.type, "text": m.text}))
    page.on("pageerror", lambda e: page_errors.append(str(e)))

    file_url = (BLIND / candidate_dir_name / "index.html").as_uri()

    # ---------- SCENARIO 1: Initial load, 390x844, exploration ----------
    page.goto(file_url, wait_until="load")
    add("goto initial page 390x844", "loaded")
    time.sleep(0.2)
    add("initial screenshot", "captured", screenshot=snap(page, candidate_dir_name, "01-initial-390x844"))

    # Landmarks / headings audit
    landmark_report = page.evaluate("""
      () => {
        const q = s => Array.from(document.querySelectorAll(s));
        const focusables = q('a,button,input,select,textarea,[tabindex]:not([tabindex="-1"])').length;
        return {
          main: q('main').length,
          nav: q('nav').length,
          aside: q('aside').length,
          headings: q('h1,h2,h3,h4').map(h => ({tag: h.tagName, text: (h.textContent||'').trim().slice(0,80)})),
          skipLinks: q('a.skip-link,[class*="skip"]').map(a => (a.textContent||'').trim()),
          landmarks: q('[role]').map(el => ({tag: el.tagName, role: el.getAttribute('role')})).slice(0,20),
          liveRegions: q('[aria-live]').map(el => ({live: el.getAttribute('aria-live'), atomic: el.getAttribute('aria-atomic'), role: el.getAttribute('role')})),
          synthBannerText: (document.querySelector('[data-hook="synthetic-banner"]')||{}).textContent?.trim()?.slice(0,200) || null,
          buttonCount: q('button').length,
          focusableCount: focusables,
        };
      }
    """)
    add("audit landmarks/headings", "captured", extra=landmark_report)

    # ---------- SCENARIO 2: Invalid submit / error prevention & recovery ----------
    # Try to trigger error state by attempting to place order without filling
    # For candidate-c, we need to navigate to review step. For A and B, submit button is on page.
    try:
        po = page.query_selector('[data-hook="place-order"]')
        if po and po.is_visible():
            po.click()
            time.sleep(0.3)
            add("click place-order with empty form", "invalid submit attempted")
            snap_ref = snap(page, candidate_dir_name, "02-error-summary")
            add("error summary state", "captured", screenshot=snap_ref)
        else:
            # candidate-c: try to navigate to step 4 by clicking Continue with empty fields
            for _ in range(4):
                cont = page.query_selector('[data-hook="continue"]:visible')
                if not cont:
                    break
                cont.click()
                time.sleep(0.15)
            add("wizard continue with empty fields", "wizard advanced through steps")
            po = page.query_selector('[data-hook="place-order"]')
            if po and po.is_visible():
                po.click()
                time.sleep(0.3)
                add("click place-order at review with empties", "invalid submit attempted")
                snap_ref = snap(page, candidate_dir_name, "02-error-summary")
                add("error summary state", "captured", screenshot=snap_ref)
    except Exception as e:
        add("invalid submit attempt failed", f"error: {e}")

    # Capture error summary text & aria-invalid count
    err_report = page.evaluate("""
      () => {
        const es = document.querySelector('[data-hook="error-summary"]');
        const invalids = Array.from(document.querySelectorAll('[aria-invalid="true"]')).map(i => i.id||i.name);
        const fieldErrs = Array.from(document.querySelectorAll('[data-hook="field-error"], .field-error')).filter(e => !e.hidden && (e.textContent||'').trim()).map(e => (e.textContent||'').trim().slice(0,120));
        const status = document.querySelector('[data-hook="status"]');
        return {
          errorSummaryVisible: es ? !es.hidden : null,
          errorSummaryText: es ? (es.textContent||'').trim().slice(0,500) : null,
          errorSummaryFocused: es && document.activeElement === es,
          invalidsCount: invalids.length,
          invalids: invalids.slice(0,20),
          visibleFieldErrors: fieldErrs.slice(0,20),
          statusText: status ? (status.textContent||'').trim().slice(0,400) : null,
          activeElement: document.activeElement ? document.activeElement.tagName + (document.activeElement.id?'#'+document.activeElement.id:'') : null
        };
      }
    """)
    add("post-invalid-submit report", "captured", extra=err_report)

    # ---------- SCENARIO 3: Reload/interruption & payment non-persistence ----------
    # First, fill only safe fields (contact) then reload
    def fill_selector(sel_or_id, val):
        # try both id and data-hook selectors
        for s in [f"#{sel_or_id}", f"[data-hook=\"{sel_or_id}\"]"]:
            el = page.query_selector(s)
            if el:
                try:
                    el.fill(val)
                    return True
                except Exception:
                    pass
        return False

    # For candidate-c, we may need to reveal step 1 first (init state should have step 1 visible).
    # Fill contact + address; then reload
    for k in ["contact-name", "contact-email", "contact-phone",
              "address-line1", "address-city", "address-state", "address-postcode", "address-country"]:
        ok = fill_selector(k, FIXTURE[k])
        if not ok:
            add(f"fill {k} for save/resume test", "field not immediately fillable (may be gated by wizard)")

    # Try to fill payment fields too so we can prove they DO NOT persist
    for k in ["card-number", "card-expiry", "card-security", "card-name"]:
        fill_selector(k, FIXTURE[k])

    add("filled safe + payment before reload", "attempted")
    time.sleep(0.15)
    snap_ref = snap(page, candidate_dir_name, "03-pre-reload")
    add("pre-reload state", "captured", screenshot=snap_ref)

    page.reload(wait_until="load")
    time.sleep(0.3)
    persistence = page.evaluate("""
      () => {
        const val = id => { const e = document.getElementById(id); return e ? e.value : null; };
        return {
          safe: {
            'contact-name': val('contact-name'),
            'contact-email': val('contact-email'),
            'address-line1': val('address-line1'),
            'address-postcode': val('address-postcode'),
          },
          payment: {
            'card-number': val('card-number'),
            'card-expiry': val('card-expiry'),
            'card-security': val('card-security'),
            'card-name': val('card-name'),
          }
        };
      }
    """)
    add("reload persistence check", "captured", extra=persistence, screenshot=snap(page, candidate_dir_name, "04-post-reload"))

    # ---------- SCENARIO 4: Complete valid canonical path (mouse+touch) ----------
    # Restart context fresh so localStorage doesn't preload
    try:
        page.evaluate("() => localStorage.clear()")
    except Exception:
        pass
    page.reload(wait_until="load")
    time.sleep(0.2)

    def full_fill_and_navigate():
        # Handle wizard vs single-page: for wizard, click Continue between steps.
        step_field_groups = [
            ["contact-name", "contact-email", "contact-phone"],
            ["address-line1", "address-city", "address-state", "address-postcode", "address-country"],
            ["card-number", "card-expiry", "card-security", "card-name"],
        ]
        # For single-page just fill everything then check confirmation checkbox
        # Try wizard-style first: fill group then click Continue if present
        wizard_like = page.evaluate("() => !!document.querySelector('[data-hook=\"continue\"]')")
        if wizard_like:
            for grp in step_field_groups:
                for k in grp:
                    fill_selector(k, FIXTURE[k])
                cont = page.query_selector('[data-hook="continue"]:visible')
                if cont:
                    cont.click()
                    time.sleep(0.15)
        else:
            for grp in step_field_groups:
                for k in grp:
                    fill_selector(k, FIXTURE[k])
        # Standard shipping is the default; ensure a radio is selected
        # confirm checkbox
        rc = page.query_selector('#review-confirmation')
        if rc:
            try:
                rc.check()
            except Exception:
                rc.click()

    full_fill_and_navigate()
    time.sleep(0.2)
    snap_ref = snap(page, candidate_dir_name, "05-review-filled")
    add("filled complete form (mouse fill)", "captured", screenshot=snap_ref)

    # Verify review data present
    review_report = page.evaluate("""
      () => {
        const rf = Array.from(document.querySelectorAll('[data-review-field]')).map(el => ({key: el.dataset.reviewField, text: (el.textContent||'').trim().slice(0,200)}));
        const totalEl = document.querySelector('[data-hook="total"]');
        return { reviewFields: rf, totalText: totalEl ? (totalEl.textContent||'').trim() : null };
      }
    """)
    add("review content", "captured", extra=review_report)

    # Click Place order
    try:
        po = page.query_selector('[data-hook="place-order"]')
        if po:
            po.click()
            time.sleep(0.5)
            add("click Place order", "clicked")
    except Exception as e:
        add("place order click failed", f"error: {e}")

    conf_report = page.evaluate("""
      () => {
        const conf = document.querySelector('[data-hook="confirmation"]');
        const cid = document.querySelector('[data-hook="confirmation-id"]');
        return {
          confirmationVisible: conf ? !conf.hidden && !conf.classList.contains('hidden') : null,
          confirmationText: conf ? (conf.textContent||'').trim().slice(0,400) : null,
          confirmationId: cid ? (cid.textContent||'').trim() : null,
          activeElement: document.activeElement ? document.activeElement.tagName + (document.activeElement.id?'#'+document.activeElement.id:'') : null,
        };
      }
    """)
    add("confirmation state", "captured", extra=conf_report, screenshot=snap(page, candidate_dir_name, "06-confirmation"))

    # ---------- SCENARIO 5: Repeated Place order (duplicate-safe) ----------
    try:
        po = page.query_selector('[data-hook="place-order"]')
        if po and po.is_enabled():
            po.click()
            time.sleep(0.2)
            add("second click Place order", "clicked (duplicate-safety test)")
        else:
            add("second Place order attempt", "button disabled or missing (good)")
    except Exception as e:
        add("second place order click", f"error: {e}")
    dup_report = page.evaluate("""
      () => ({
        confIds: Array.from(document.querySelectorAll('[data-hook="confirmation-id"]')).map(e => (e.textContent||'').trim()),
        placeOrderDisabled: (document.querySelector('[data-hook=\"place-order\"]')||{}).disabled,
        placeOrderAriaDisabled: document.querySelector('[data-hook=\"place-order\"]') ? document.querySelector('[data-hook=\"place-order\"]').getAttribute('aria-disabled') : null,
      })
    """)
    add("duplicate-safety report", "captured", extra=dup_report, screenshot=snap(page, candidate_dir_name, "07-after-duplicate"))

    ctx.close()

    # ---------- SCENARIO 6: Keyboard-only completion in fresh context ----------
    ctx2 = browser.new_context(viewport=VIEWPORT_DEFAULT, device_scale_factor=2, is_mobile=False, has_touch=False)
    page2 = ctx2.new_page()
    ctx2.on = None  # not needed
    page2.on("console", lambda m: console_msgs.append({"type": m.type, "text": "kb:"+m.text}))
    page2.on("pageerror", lambda e: page_errors.append("kb:"+str(e)))
    page2.goto(file_url, wait_until="load")
    time.sleep(0.2)
    add("keyboard: fresh navigation start", "loaded")

    # Tab through and observe first focus and skip-link
    page2.keyboard.press("Tab")
    time.sleep(0.05)
    first_focus = page2.evaluate("() => { const a=document.activeElement; return a ? (a.tagName + (a.id?'#'+a.id:'') + ' text=' + ((a.textContent||'').trim().slice(0,60))) : null }")
    add("keyboard: first Tab focus", first_focus)

    # Try activating skip-link if visible
    if "skip" in (first_focus or "").lower():
        page2.keyboard.press("Enter")
        time.sleep(0.05)
        after_skip = page2.evaluate("() => { const a=document.activeElement; return a ? a.tagName + (a.id?'#'+a.id:'') : null }")
        add("keyboard: activated skip-link", after_skip)

    # Type into inputs using page.locator("id").fill via keyboard-safe route.
    # Use JS-driven focus + type to simulate keyboard entry once we reach the field.
    def kb_fill(sel_or_id, val):
        for s in [f"#{sel_or_id}", f"[data-hook=\"{sel_or_id}\"]"]:
            el = page2.query_selector(s)
            if el:
                try:
                    el.focus()
                    # Clear existing
                    el.evaluate("el => { el.value = ''; el.dispatchEvent(new Event('input', {bubbles:true})); }")
                    page2.keyboard.type(val, delay=1)
                    el.evaluate("el => el.dispatchEvent(new Event('change', {bubbles:true}))")
                    return True
                except Exception:
                    return False
        return False

    step_field_groups = [
        ["contact-name", "contact-email", "contact-phone"],
        ["address-line1", "address-city", "address-state", "address-postcode", "address-country"],
        ["card-number", "card-expiry", "card-security", "card-name"],
    ]
    wizard_like = page2.evaluate("() => !!document.querySelector('[data-hook=\"continue\"]')")
    for grp in step_field_groups:
        for k in grp:
            kb_fill(k, FIXTURE[k])
        if wizard_like:
            # find visible continue button and press Enter on it
            cont = page2.query_selector('[data-hook="continue"]:visible')
            if cont:
                cont.focus()
                page2.keyboard.press("Enter")
                time.sleep(0.1)
    # confirm checkbox
    rc = page2.query_selector('#review-confirmation')
    if rc:
        rc.focus()
        page2.keyboard.press("Space")
        time.sleep(0.05)
    add("keyboard: form completed by keyboard entry", "attempted")
    snap_ref = snap(page2, candidate_dir_name, "08-keyboard-review")
    add("keyboard: review screenshot", "captured", screenshot=snap_ref)

    # Place order via keyboard
    po = page2.query_selector('[data-hook="place-order"]')
    if po:
        po.focus()
        page2.keyboard.press("Enter")
        time.sleep(0.4)
    kb_conf = page2.evaluate("""
      () => {
        const conf = document.querySelector('[data-hook="confirmation"]');
        const cid = document.querySelector('[data-hook="confirmation-id"]');
        return {
          confirmationVisible: conf ? !conf.hidden && !conf.classList.contains('hidden') : null,
          confirmationId: cid ? (cid.textContent||'').trim() : null,
          activeElement: document.activeElement ? document.activeElement.tagName + (document.activeElement.id?'#'+document.activeElement.id:'') : null,
        };
      }
    """)
    add("keyboard: confirmation state", "captured", extra=kb_conf, screenshot=snap(page2, candidate_dir_name, "09-keyboard-confirmation"))
    ctx2.close()

    # ---------- SCENARIO 7: Reduced motion ----------
    ctx3 = browser.new_context(viewport=VIEWPORT_DEFAULT, device_scale_factor=2, is_mobile=True, has_touch=True, reduced_motion="reduce")
    page3 = ctx3.new_page()
    page3.on("pageerror", lambda e: page_errors.append("rm:"+str(e)))
    page3.goto(file_url, wait_until="load")
    time.sleep(0.2)
    add("reduced-motion: loaded", "captured", screenshot=snap(page3, candidate_dir_name, "10-reduced-motion-initial"))
    # Just complete flow quickly
    wizard_like3 = page3.evaluate("() => !!document.querySelector('[data-hook=\"continue\"]')")
    for grp in step_field_groups:
        for k in grp:
            for s in [f"#{k}", f"[data-hook=\"{k}\"]"]:
                el = page3.query_selector(s)
                if el:
                    try:
                        el.fill(FIXTURE[k])
                        break
                    except Exception:
                        pass
        if wizard_like3:
            cont = page3.query_selector('[data-hook="continue"]:visible')
            if cont:
                cont.click()
                time.sleep(0.05)
    rc3 = page3.query_selector('#review-confirmation')
    if rc3:
        try: rc3.check()
        except: rc3.click()
    po3 = page3.query_selector('[data-hook="place-order"]')
    if po3:
        po3.click()
        time.sleep(0.3)
    rm_report = page3.evaluate("""
      () => {
        const cid = document.querySelector('[data-hook="confirmation-id"]');
        return {confirmationId: cid ? (cid.textContent||'').trim() : null};
      }
    """)
    add("reduced-motion: completed flow", "captured", extra=rm_report, screenshot=snap(page3, candidate_dir_name, "11-reduced-motion-confirmation"))
    ctx3.close()

    # ---------- SCENARIO 8: Small viewport 320x568 ----------
    ctx4 = browser.new_context(viewport=VIEWPORT_SMALL, device_scale_factor=2, is_mobile=True, has_touch=True)
    page4 = ctx4.new_page()
    page4.on("pageerror", lambda e: page_errors.append("sm:"+str(e)))
    page4.goto(file_url, wait_until="load")
    time.sleep(0.2)
    small_report = page4.evaluate("""
      () => {
        const doc = document.documentElement;
        return {
          scrollWidth: doc.scrollWidth,
          clientWidth: doc.clientWidth,
          hasHorizontalScroll: doc.scrollWidth > doc.clientWidth + 1
        };
      }
    """)
    add("320x568: viewport initial", "captured", extra=small_report, screenshot=snap(page4, candidate_dir_name, "12-viewport-320-initial"))
    ctx4.close()

    browser.close()

    return {
        "candidate": candidate_dir_name,
        "started_at": now_iso(),
        "entries": entries,
        "console_messages": console_msgs,
        "page_errors": page_errors,
    }


def main():
    JUDGE.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        for cand in CANDIDATE_ORDER:
            print(f"=== Driving {cand} ===")
            transcript = run_candidate(pw, cand)
            letter = cand.split("-")[-1]
            out = JUDGE / f"navigation-transcript-{letter}.json"
            out.write_text(json.dumps(transcript, indent=2))
            print(f"  wrote {out}")
            print(f"  page_errors: {len(transcript['page_errors'])} console_messages: {len(transcript['console_messages'])}")

if __name__ == "__main__":
    main()
