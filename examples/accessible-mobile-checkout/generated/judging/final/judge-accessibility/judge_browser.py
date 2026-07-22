import json
import sys
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[4]
BLIND = ROOT / "generated" / "judging" / "final" / "blind"
OUT = Path(__file__).resolve().parent


def file_url(path: Path) -> str:
    return "file:///" + quote(str(path).replace("\\", "/"))


def control_snapshot(page):
    return page.locator("a, button, input, select, textarea, [role='button'], [role='link'], [role='checkbox'], [role='radio'], [role='tab']").evaluate_all(
        """els => els.map((el, index) => {
          const label = el.labels && el.labels.length ? [...el.labels].map(x => x.innerText.trim()).join(" ") : "";
          const rect = el.getBoundingClientRect();
          return {
            index, tag: el.tagName.toLowerCase(), type: el.getAttribute("type"),
            id: el.id || null, name: el.getAttribute("name"), role: el.getAttribute("role"),
            text: (el.innerText || el.value || "").trim().replace(/\\s+/g, " ").slice(0, 160),
            aria_label: el.getAttribute("aria-label"), aria_describedby: el.getAttribute("aria-describedby"),
            label, disabled: !!el.disabled, required: !!el.required,
            checked: "checked" in el ? !!el.checked : null,
            visible: !!(rect.width && rect.height), box: {x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height)}
          };
        })"""
    )


def main(label: str):
    candidate = BLIND / label
    shots = OUT / "screenshots" / label[-1]
    shots.mkdir(parents=True, exist_ok=True)
    transcript = {
        "candidate_label": label,
        "environment": {
            "viewport": {"width": 390, "height": 844},
            "browser": "local Chromium via Python Playwright",
            "reduced_motion": "reduce",
            "network": "offline file bundle",
        },
        "actions": [],
        "console": [],
        "requests": [],
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page = context.new_page()
        page.on("console", lambda msg: transcript["console"].append({"type": msg.type, "text": msg.text}))
        page.on("request", lambda req: transcript["requests"].append(req.url))
        page.goto(file_url(candidate / "index.html"), wait_until="load")
        page.wait_for_timeout(350)
        page.evaluate("localStorage.clear(); sessionStorage.clear()")
        page.reload(wait_until="load")
        page.wait_for_timeout(250)
        page.screenshot(path=str(shots / "01-initial-reduced-motion.png"), full_page=True)
        transcript["initial_controls"] = control_snapshot(page)
        transcript["initial_text"] = page.locator("body").inner_text()[:12000]
        transcript["actions"].append({"action": "load at 390x844 with reduced motion", "outcome": "loaded"})
        transcript["control_coverage"] = []

        def visible_text(selector):
            return page.locator(selector).all_inner_texts()

        def snapshot(name):
            page.screenshot(path=str(shots / name), full_page=True)

        def action(name, fn):
            try:
                result = fn()
                transcript["actions"].append({"action": name, "outcome": result or "completed"})
                return result
            except Exception as exc:
                transcript["actions"].append({"action": name, "outcome": "failed", "detail": str(exc)})
                return None

        # Keyboard entry and all persistent step links are exercised before values are entered.
        def skip_link():
            page.keyboard.press("Tab")
            before = page.evaluate("document.activeElement && document.activeElement.textContent.trim()")
            page.keyboard.press("Enter")
            after = page.evaluate("document.activeElement && (document.activeElement.id || document.activeElement.name)")
            snapshot("02-skip-link-focus.png")
            return {"focused_before_activate": before, "focused_after_activate": after}

        action("keyboard: Tab then activate Skip to checkout form", skip_link)
        for link in page.get_by_role("link").all():
            text = (link.inner_text() or "").strip()
            if text != "Skip to checkout form":
                action(f"activate step link: {text}", lambda link=link, text=text: (
                    {"scroll_y": page.evaluate("window.scrollY")} if (link.click(), page.wait_for_timeout(100)) else None
                ))
                transcript["control_coverage"].append({"control": text, "operation": "click", "result": "activated"})

        # Required field correction and error focus are observed as a real submission attempt.
        page.locator("#contact-email").fill("not-an-email")
        action("submit invalid checkout to observe error prevention", lambda: (
            page.get_by_role("button", name="Place order").click(),
            page.wait_for_timeout(150),
            {
                "focused_id": page.evaluate("document.activeElement && document.activeElement.id"),
                "invalid_ids": page.locator(":invalid").evaluate_all("els => els.map(el => el.id)"),
                "alert_text": visible_text("[role='alert']"),
            }
        )[2])
        snapshot("03-invalid-submission.png")
        page.locator("#contact-email").fill("alex.morgan@example.invalid")
        transcript["control_coverage"].append({"control": "Email", "operation": "invalid then corrected", "result": "corrected"})

        values = {
            "#contact-name": "Alex Morgan",
            "#contact-phone": "+61 400 000 000",
            "#address-line1": "42 Fiction Lane",
            "#address-city": "Sampleton",
            "#address-state": "NSW",
            "#address-postcode": "2000",
            "#address-country": "Australia",
            "#card-number": "4111 1111 1111 1111",
            "#card-expiry": "12/34",
            "#card-security": "123",
            "#card-name": "Alex Morgan",
        }
        for selector, value in values.items():
            action(f"fill {selector[1:]}", lambda selector=selector, value=value: page.locator(selector).fill(value))
            transcript["control_coverage"].append({"control": selector[1:], "operation": "fill", "result": "filled"})

        for shipping_id in ("#shipping-express", "#shipping-standard"):
            action(f"select {shipping_id[1:]}", lambda shipping_id=shipping_id: page.locator(shipping_id).check())
            transcript["control_coverage"].append({"control": shipping_id[1:], "operation": "select", "result": "selected"})
        snapshot("04-filled-shipping.png")

        # Persist only non-payment work, reload, and inspect that payment secrets did not return.
        if page.get_by_role("button", name="Save progress").count():
            action("save safe progress", lambda: (
                page.get_by_role("button", name="Save progress").click(),
                page.wait_for_timeout(150),
                {"status": visible_text("[role='status']"), "alerts": visible_text("[role='alert']")}
            )[2])
        else:
            transcript["actions"].append({"action": "save safe progress", "outcome": "not provided; candidate uses observed automatic safe restoration"})
        action("reload after save", lambda: (
            page.reload(wait_until="load"),
            page.wait_for_timeout(150),
            {
                "contact_restored": page.locator("#contact-name").input_value(),
                "address_restored": page.locator("#address-line1").input_value(),
                "payment_number_after_reload": page.locator("#card-number").input_value(),
                "payment_cvv_after_reload": page.locator("#card-security").input_value(),
            }
        )[2])
        snapshot("05-reload-safe-resume.png")

        # Exercise destructive-action confirmation, Escape, Cancel, and affirmative clear.
        clear_control_available = page.get_by_role("button", name="Clear saved progress").count() > 0
        if clear_control_available:
            action("open clear-progress confirmation then Escape", lambda: (
                page.get_by_role("button", name="Clear saved progress").click(),
                page.wait_for_timeout(80),
                page.keyboard.press("Escape"),
                {"dialog_visible": page.locator("[role='dialog']").count() and page.locator("[role='dialog']").is_visible()}
            )[2])
            action("open clear-progress confirmation then Cancel", lambda: (
                page.get_by_role("button", name="Clear saved progress").click(),
                page.wait_for_timeout(80),
                page.get_by_role("button", name="Cancel").click(),
                {"contact_preserved": page.locator("#contact-name").input_value()}
            )[2])
            action("confirm clear saved progress", lambda: (
                page.get_by_role("button", name="Clear saved progress").click(),
                page.wait_for_timeout(80),
                page.get_by_role("button", name="Yes, clear saved progress").click(),
                page.wait_for_timeout(100),
                {"contact_after_clear": page.locator("#contact-name").input_value()}
            )[2])
        else:
            transcript["actions"].append({"action": "clear/cancel/Escape", "outcome": "not discoverable; no clear-progress control or confirmation was provided"})
        snapshot("06-clear-confirmation.png")
        if clear_control_available:
            transcript["control_coverage"].append({"control": "Clear saved progress", "operation": "Escape, Cancel, confirm", "result": "all paths exercised"})
        else:
            transcript["control_coverage"].append({"control": "Clear saved progress", "operation": "discoverability check", "result": "not provided"})

        # Re-enter data for a full canonical completion and visible compact/edit flow.
        for selector, value in {"#contact-name": "Alex Morgan", "#contact-email": "alex.morgan@example.invalid", **values}.items():
            if selector != "#contact-email" or page.locator(selector).input_value() != value:
                page.locator(selector).fill(value)
        page.locator("#shipping-standard").check()
        action("enable Compact completed sections", lambda: (
            page.locator("#compact-completed").check(),
            page.wait_for_timeout(100),
            {"checked": page.locator("#compact-completed").is_checked()}
        )[2])
        snapshot("07-compact-completed.png")
        for edit_name in ("Edit contact", "Edit delivery", "Edit shipping", "Edit payment"):
            edit = page.get_by_role("button", name=edit_name)
            if edit.count() and edit.first.is_visible():
                action(f"activate {edit_name}", lambda edit=edit, edit_name=edit_name: (
                    edit.first.click(), page.wait_for_timeout(80), {"focused_id": page.evaluate("document.activeElement && document.activeElement.id")}
                )[2])
                transcript["control_coverage"].append({"control": edit_name, "operation": "click", "result": "activated"})
        page.locator("#review-confirmation").check()
        transcript["control_coverage"].append({"control": "review-confirmation", "operation": "check", "result": "checked"})

        # Return focus through a keyboard run immediately before confirming.
        page.locator("#review-confirmation").focus()
        keyboard_ids = []
        for _ in range(12):
            page.keyboard.press("Tab")
            keyboard_ids.append(page.evaluate("document.activeElement && (document.activeElement.id || document.activeElement.name || document.activeElement.textContent.trim().slice(0,60))"))
        transcript["keyboard_traversal"] = keyboard_ids
        action("place canonical synthetic order", lambda: (
            page.get_by_role("button", name="Place order").click(),
            page.wait_for_timeout(250),
            {
                "syn_2048_visible": "SYN-2048" in page.locator("body").inner_text(),
                "status": visible_text("[role='status']"),
                "alerts": visible_text("[role='alert']"),
            }
        )[2])
        snapshot("08-confirmation-syn-2048.png")
        action("attempt duplicate Place order activation", lambda: {
            "place_order_button_count": page.get_by_role("button", name="Place order").count(),
            "confirmation_count": page.locator("text=SYN-2048").count(),
        })
        action("reload after confirmation", lambda: (
            page.reload(wait_until="load"),
            page.wait_for_timeout(150),
            {
                "syn_2048_present": "SYN-2048" in page.locator("body").inner_text(),
                "payment_number_after_confirmation_reload": page.locator("#card-number").input_value() if page.locator("#card-number").count() else None,
                "payment_cvv_after_confirmation_reload": page.locator("#card-security").input_value() if page.locator("#card-security").count() else None,
            }
        )[2])
        snapshot("09-post-confirmation-reload.png")
        transcript["final_controls"] = control_snapshot(page)
        transcript["external_requests"] = [url for url in transcript["requests"] if not url.startswith("file:")]
        context.close()
        browser.close()
    (OUT / f"navigation-transcript-{label[-1]}.json").write_text(json.dumps(transcript, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
