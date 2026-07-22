#!/usr/bin/env python3
"""Frozen, track-neutral objective harness for the synthetic mobile checkout.

The harness deliberately depends only on the Python Playwright API and the
candidate hook contract in this directory.  It never starts a server and never
changes a candidate or a Manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from playwright.sync_api import (
        Error as PlaywrightError,
        Page,
        TimeoutError as PlaywrightTimeoutError,
        sync_playwright,
    )
except ImportError as exc:  # pragma: no cover - a clear CLI diagnostic
    print("Python Playwright is required by the frozen preflight.", file=sys.stderr)
    raise SystemExit(2) from exc


HUMAN_USE = {
    "applicability": "applicable",
    "rationale": "The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.",
}
HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE / "canonical-fixture.json"
CONTRACT_PATH = HERE / "candidate-contract.json"
REPORT_SCHEMA = "1.0"
VIEWPORTS = ((320, 568), (360, 800), (390, 844))
FORBIDDEN_SCOPE = (
    "account",
    "sign in",
    "sign-in",
    "coupon",
    "recommendation",
    "upsell",
    "stock",
)
FIELDS = {
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
SAFE_FIELDS = (
    "contact-name",
    "contact-email",
    "contact-phone",
    "address-line1",
    "address-city",
    "address-state",
    "address-postcode",
    "address-country",
)
PAYMENT_FIELDS = ("card-number", "card-expiry", "card-security")
GATE_IDS = (
    "content-fidelity",
    "semantic-accessibility-gate",
    "keyboard-completion-gate",
    "error-recovery-gate",
    "mobile-touch-gate",
    "resilience-gate",
    "offline-safety-gate",
)


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def atomic_json(path: Path, value: Any) -> None:
    atomic_write(path, json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compact(value: Any, limit: int = 280) -> str:
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def hook_selector(hook: str) -> str:
    return f'[data-hook="{hook}"]'


def rgb(value: str | None) -> tuple[float, float, float, float] | None:
    if not value or value in ("transparent", "none"):
        return None
    match = re.fullmatch(
        r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s/]+([\d.]+))?\s*\)",
        value.strip(),
        re.I,
    )
    if match:
        channels = tuple(float(match.group(i)) / 255 for i in range(1, 4))
        alpha = float(match.group(4)) if match.group(4) else 1.0
        if alpha > 1:
            alpha /= 255
        return (*channels, alpha)
    if value.startswith("#"):
        raw = value[1:]
        if len(raw) in (3, 4):
            raw = "".join(char * 2 for char in raw)
        if len(raw) in (6, 8):
            channels = tuple(int(raw[i : i + 2], 16) / 255 for i in (0, 2, 4))
            alpha = int(raw[6:8], 16) / 255 if len(raw) == 8 else 1.0
            return (*channels, alpha)
    return None


def composite(foreground: tuple[float, float, float, float], background: tuple[float, float, float, float]) -> tuple[float, float, float]:
    fa, ba = foreground[3], background[3]
    out_alpha = fa + ba * (1 - fa)
    if out_alpha == 0:
        return (1.0, 1.0, 1.0)
    return tuple(
        (foreground[i] * fa + background[i] * ba * (1 - fa)) / out_alpha
        for i in range(3)
    )


def luminance(color: tuple[float, float, float]) -> float:
    linear = []
    for channel in color:
        linear.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(foreground: tuple[float, float, float], background: tuple[float, float, float]) -> float:
    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


class GateBook:
    def __init__(self) -> None:
        self._gates: dict[str, dict[str, Any]] = {
            gate_id: {"id": gate_id, "status": "pass", "assertions": []}
            for gate_id in GATE_IDS
        }

    def check(self, gate_id: str, condition: bool, assertion: str, detail: Any = "") -> bool:
        entry = self._gates[gate_id]
        result = {
            "assertion": assertion,
            "status": "pass" if condition else "fail",
            "detail": compact(detail),
        }
        entry["assertions"].append(result)
        if not condition:
            entry["status"] = "fail"
        return condition

    def fail(self, gate_id: str, assertion: str, detail: Any = "") -> None:
        self.check(gate_id, False, assertion, detail)

    def records(self) -> list[dict[str, Any]]:
        return [self._gates[gate_id] for gate_id in GATE_IDS]

    def failed_ids(self) -> list[str]:
        return [entry["id"] for entry in self.records() if entry["status"] != "pass"]


class CheckoutHarness:
    def __init__(self, candidate: Path, out: Path, fixture: dict[str, Any]) -> None:
        self.candidate = candidate.resolve()
        self.out = out.resolve()
        self.fixture = fixture
        self.book = GateBook()
        self.metrics = {
            "focusable_controls_traversed": 0,
            "activations": 0,
            "corrections": 0,
            "completion_interactions": 0,
        }
        self.external_requests: list[str] = []
        self.screenshots: list[str] = []
        self.page: Page | None = None
        self.browser: Any = None
        self.context: Any = None
        self._last_storage: dict[str, Any] = {}

    def locator(self, hook: str) -> Any:
        assert self.page is not None
        return self.page.locator(hook_selector(hook)).first

    def count(self, hook: str) -> int:
        return self.page.locator(hook_selector(hook)).count() if self.page else 0

    def visible(self, hook: str) -> bool:
        try:
            return bool(self.count(hook) and self.locator(hook).is_visible())
        except PlaywrightError:
            return False

    def text(self, hook: str) -> str:
        try:
            return compact(self.locator(hook).inner_text())
        except PlaywrightError:
            return ""

    def field(self, hook: str) -> Any:
        return self.locator(hook)

    def value(self, hook: str) -> str:
        if not self.count(hook):
            return ""
        try:
            return self.field(hook).input_value(timeout=500)
        except PlaywrightError:
            return ""

    def _focus_style(self, locator: Any) -> dict[str, Any]:
        return locator.evaluate(
            """el => {
              el.focus();
              const s = getComputedStyle(el);
              return {
                active: document.activeElement === el,
                outlineColor: s.outlineColor,
                outlineWidth: s.outlineWidth,
                outlineStyle: s.outlineStyle,
                boxShadow: s.boxShadow,
                borderColor: s.borderColor
              };
            }""",
            locator,
        )

    def _visible_continue(self) -> Any | None:
        assert self.page is not None
        controls = self.page.locator(hook_selector("continue"))
        for index in range(controls.count()):
            control = controls.nth(index)
            if control.is_visible() and control.is_enabled():
                return control
        return None

    def reveal(self, hook: str) -> bool:
        """Reveal wizard fields without prescribing a Track's visual paradigm."""
        for _ in range(12):
            if self.visible(hook):
                return True
            control = self._visible_continue()
            if control is None:
                return False
            control.focus()
            self.page.keyboard.press("Enter")
            self.metrics["activations"] += 1
            self.page.wait_for_timeout(15)
        return self.visible(hook)

    def keyboard_fill(self, hook: str, value: str) -> bool:
        if not self.reveal(hook):
            return False
        control = self.field(hook)
        try:
            control.focus()
            self.page.keyboard.press("Control+A")
            self.page.keyboard.type(value)
            control.evaluate("el => el.blur()")
            return True
        except PlaywrightError:
            return False

    def fill(self, hook: str, value: str) -> bool:
        if not self.reveal(hook):
            return False
        try:
            self.field(hook).fill(value)
            self.field(hook).evaluate("el => el.blur()")
            return True
        except PlaywrightError:
            return False

    def advance(self) -> bool:
        control = self._visible_continue()
        if control is None:
            return True
        try:
            control.focus()
            self.page.keyboard.press("Enter")
            self.metrics["activations"] += 1
            self.page.wait_for_timeout(20)
            return True
        except PlaywrightError:
            return False

    def activate(self, hook: str, key: str = "Enter") -> bool:
        if not self.reveal(hook):
            return False
        try:
            control = self.locator(hook)
            control.focus()
            self.page.keyboard.press(key)
            self.metrics["activations"] += 1
            return True
        except PlaywrightError:
            return False

    def set_review(self, checked: bool) -> bool:
        if not self.reveal("review-confirmation"):
            return False
        control = self.locator("review-confirmation")
        try:
            if control.get_attribute("type") in ("checkbox", "radio"):
                current = bool(control.is_checked())
                if current != checked:
                    control.focus()
                    self.page.keyboard.press("Space")
                    self.metrics["activations"] += 1
            else:
                return False
            return bool(control.is_checked()) == checked
        except PlaywrightError:
            return False

    def clear_fields(self) -> None:
        for hook in FIELDS:
            if self.reveal(hook):
                try:
                    self.field(hook).fill("")
                except PlaywrightError:
                    pass

    def fill_all(self, keyboard: bool = False, include_review: bool = True) -> bool:
        success = True
        for hook, value in FIELDS.items():
            success = (self.keyboard_fill(hook, value) if keyboard else self.fill(hook, value)) and success
        success = self.set_shipping("standard") and success
        if include_review:
            success = self.set_review(True) and success
        self.advance()
        return success

    def set_shipping(self, method: str) -> bool:
        hook = "shipping-standard" if method == "standard" else "shipping-express"
        if not self.reveal(hook):
            return False
        control = self.locator(hook)
        try:
            kind = control.get_attribute("type")
            if kind in ("radio", "checkbox"):
                control.focus()
                if not control.is_checked():
                    self.page.keyboard.press("Space")
                    self.metrics["activations"] += 1
                return bool(control.is_checked())
            control.focus()
            self.page.keyboard.press("Space")
            self.metrics["activations"] += 1
            return True
        except PlaywrightError:
            return False

    def submit(self) -> bool:
        return self.activate("place-order", "Enter")

    def confirmation_count(self) -> int:
        if not self.page:
            return 0
        matches = self.page.locator(hook_selector("confirmation-id"))
        count = 0
        for index in range(matches.count()):
            try:
                if "SYN-2048" in matches.nth(index).inner_text():
                    count += 1
            except PlaywrightError:
                continue
        return count

    def storage(self) -> dict[str, Any]:
        return self.page.evaluate(
            """() => {
              const read = storage => Object.fromEntries(
                Array.from({length: storage.length}, (_, i) => {
                  const key = storage.key(i);
                  return [key, storage.getItem(key)];
                })
              );
              return {local: read(localStorage), session: read(sessionStorage)};
            }"""
        )

    def run(self) -> dict[str, Any]:
        self.out.mkdir(parents=True, exist_ok=True)
        if not (self.candidate / "index.html").is_file():
            for gate_id in GATE_IDS:
                self.book.fail(gate_id, "candidate-entrypoint", f"Missing {self.candidate / 'index.html'}")
            return self.report()
        with sync_playwright() as playwright:
            self.browser = playwright.chromium.launch(
                headless=True,
            )
            self.context = self.browser.new_context(
                viewport={"width": 390, "height": 844}, reduced_motion="reduce"
            )
            self.page = self.context.new_page()
            self.page.set_default_timeout(800)
            self.page.set_default_navigation_timeout(10000)
            self.page.on("request", self._request)
            self.page.on("requestfailed", self._request_failed)
            self.page.goto((self.candidate / "index.html").as_uri(), wait_until="load")
            self.page.wait_for_timeout(30)
            self._screenshot("initial")
            self.content_gate()
            self.semantic_gate()
            self.keyboard_gate()
            self.error_gate()
            self.mobile_gate()
            self.resilience_gate()
            self.offline_gate()
            self._screenshot("final")
            self.context.close()
            self.browser.close()
        return self.report()

    def _request(self, request: Any) -> None:
        url = request.url
        if not (url.startswith("file://") or url.startswith("data:") or url.startswith("blob:") or url.startswith("about:")):
            self.external_requests.append(url)
            try:
                request.abort()
            except PlaywrightError:
                pass

    def _request_failed(self, request: Any) -> None:
        if request.url.startswith(("http://", "https://", "ws://", "wss://")):
            self.external_requests.append(request.url)

    def _screenshot(self, name: str) -> None:
        try:
            path = self.out / f"{name}.png"
            self.page.screenshot(path=str(path), full_page=True)
            self.screenshots.append(path.name)
        except PlaywrightError as exc:
            self.book.fail("content-fidelity", "screenshot-captured", str(exc))

    def content_gate(self) -> None:
        gate = "content-fidelity"
        assert self.page is not None
        body = self.page.locator("body").inner_text()
        normalized = re.sub(r"\s+", " ", body)
        required_text = (
            "Northstar Goods",
            "Synthetic checkout demonstration",
            "Northstar Insulated Bottle",
            "Willow Cotton Throw",
            "AUD 80.00",
            "AUD 8.50",
            "Standard — 3 to 5 business days",
            "AUD 5.00",
            "Express — 1 to 2 business days",
            "AUD 12.00",
            "Guest",
        )
        for expected in required_text:
            self.book.check(gate, expected.lower() in normalized.lower(), "visible-canonical-text", expected)
        for hook in ("checkout-root", "synthetic-banner", "cart", "cart-line-bottle", "cart-line-throw", "subtotal", "tax", "shipping-standard", "shipping-express", "total"):
            self.book.check(gate, self.count(hook) == 1, "required-content-hook", hook)
        banner = self.text("synthetic-banner").lower()
        self.book.check(gate, "synthetic" in banner and ("fictional" in banner or "demonstration" in banner), "visible-synthetic-labelling", banner)
        lowered = normalized.lower()
        for forbidden in FORBIDDEN_SCOPE:
            self.book.check(gate, forbidden not in lowered, "forbidden-scope-absent", forbidden)
        self.book.check(
            gate,
            self.text("total") in ("", "AUD 93.50") or "AUD 93.50" in self.text("total") or "AUD 100.50" in self.text("total"),
            "shipping-total-is-frozen-choice",
            self.text("total"),
        )
        self.book.check(gate, self.count("confirmation-id") <= 1, "single-confirmation-hook", self.count("confirmation-id"))

    def semantic_gate(self) -> None:
        gate = "semantic-accessibility-gate"
        assert self.page is not None
        self.book.check(gate, self.page.locator("main").count() >= 1, "main-landmark")
        self.book.check(gate, self.page.locator("form").count() >= 1, "checkout-form")
        self.book.check(gate, self.page.locator("h1").count() >= 1, "primary-heading")
        self.book.check(gate, self.page.locator("h2,h3").count() >= 4, "task-headings", self.page.locator("h2,h3").count())
        self.book.check(gate, self.page.locator("fieldset").count() >= 4, "required-fieldsets", self.page.locator("fieldset").count())
        for hook in ("contact-section", "address-section", "shipping-section", "payment-section", "review-section"):
            self.book.check(gate, self.count(hook) == 1, "task-section-hook", hook)
        for hook in FIELDS:
            exists = self.count(hook) == 1
            self.book.check(gate, exists, "field-hook", hook)
            if not exists:
                continue
            control = self.locator(hook)
            label = control.evaluate(
                """el => {
                  const labelled = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby');
                  if (labelled) return labelled;
                  if (el.labels && el.labels.length) return Array.from(el.labels).map(x => x.innerText).join(' ');
                  const id = el.id;
                  return id ? Array.from(document.querySelectorAll(`label[for="${CSS.escape(id)}"]`)).map(x => x.innerText).join(' ') : '';
                }""",
                control,
            )
            described = control.get_attribute("aria-describedby") or ""
            required = control.get_attribute("required") is not None or control.get_attribute("aria-required") == "true"
            self.book.check(gate, bool(str(label).strip()), "accessible-name", f"{hook}: {label}")
            self.book.check(gate, bool(described.strip()), "field-description", hook)
            self.book.check(gate, required, "required-state", hook)
        status = self.locator("status")
        self.book.check(
            gate,
            self.count("status") == 1 and (
                status.get_attribute("role") in ("status", "alert", "log")
                or status.get_attribute("aria-live") in ("polite", "assertive")
            ),
            "status-live-semantics",
            self.text("status"),
        )
        summary = self.locator("error-summary")
        self.book.check(
            gate,
            self.count("error-summary") == 1 and (
                summary.get_attribute("role") in ("alert", "status")
                or summary.get_attribute("aria-live") in ("polite", "assertive")
            ),
            "error-live-semantics",
        )
        confirmation = self.locator("confirmation")
        self.book.check(
            gate,
            self.count("confirmation") == 1 and (
                confirmation.get_attribute("role") in ("status", "alert")
                or confirmation.get_attribute("aria-live") in ("polite", "assertive")
            ),
            "confirmation-semantics",
        )
        self.book.check(gate, self.count("place-order") == 1, "explicit-place-order-hook")
        if self.count("place-order"):
            control = self.locator("place-order")
            self.book.check(gate, "place order" in (control.inner_text() or "").lower(), "place-order-name", control.inner_text())
            self.book.check(gate, control.get_attribute("type") in ("submit", "button"), "place-order-control")
        if self.count("review-confirmation"):
            review = self.locator("review-confirmation")
            self.book.check(gate, review.get_attribute("type") in ("checkbox", "radio"), "explicit-review-control")
        else:
            self.book.fail(gate, "explicit-review-control", "Missing review-confirmation hook")
        edit_count = sum(self.count(hook) for hook in ("edit-contact", "edit-address", "edit-shipping", "edit-payment"))
        self.book.check(gate, edit_count >= 1, "edit-control-for-review-correction", edit_count)
        if self.count("place-order"):
            style = self._focus_style(self.locator("place-order"))
            visible_focus = (
                style.get("outlineStyle") not in ("none", "")
                and float(re.sub(r"[^0-9.]", "", style.get("outlineWidth", "0") or "0") or 0) > 0
            ) or style.get("boxShadow") not in ("none", "")
            self.book.check(gate, visible_focus, "visible-focus-indicator", style)

    def _element_paint(self, locator: Any) -> dict[str, Any]:
        return locator.evaluate(
            """el => {
              const transparent = c => !c || c === 'transparent' || c.endsWith(', 0)');
              let node = el;
              let background = 'rgb(255, 255, 255)';
              while (node && node.nodeType === 1) {
                const color = getComputedStyle(node).backgroundColor;
                if (!transparent(color)) { background = color; break; }
                node = node.parentElement;
              }
              const style = getComputedStyle(el);
              return {
                foreground: style.color,
                background,
                border: style.borderColor,
                outline: style.outlineColor,
                outlineWidth: style.outlineWidth,
                outlineStyle: style.outlineStyle,
                fontSize: style.fontSize,
                fontWeight: style.fontWeight,
                visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
              };
            }""",
            locator,
        )

    def _contrast_value(self, paint: dict[str, Any], fg_key: str = "foreground") -> float | None:
        foreground = rgb(paint.get(fg_key))
        background = rgb(paint.get("background"))
        if not foreground or not background:
            return None
        return contrast(composite(foreground, background), background[:3])

    def contrast_gate(self) -> None:
        gate = "semantic-accessibility-gate"
        contrast_gate = "content-fidelity"  # placeholder prevents accidental new gate IDs
        del contrast_gate
        samples = ("synthetic-banner", "cart", "subtotal", "tax", "total", "status", "error-summary")
        seen = 0
        for hook in samples:
            if not self.visible(hook):
                continue
            paint = self._element_paint(self.locator(hook))
            value = self._contrast_value(paint)
            if value is not None:
                seen += 1
                font_size = float(re.sub(r"[^0-9.]", "", paint.get("fontSize", "16")) or 16)
                weight = int(paint.get("fontWeight", "400")) if str(paint.get("fontWeight", "400")).isdigit() else 400
                threshold = 3.0 if font_size >= 24 or (font_size >= 18.66 and weight >= 700) else 4.5
                self.book.check(gate, value >= threshold, "text-contrast", f"{hook}: {value:.2f} < {threshold:.2f}")
        self.book.check(gate, seen >= 3, "computed-text-contrast-samples", seen)
        if self.count("place-order"):
            paint = self._element_paint(self.locator("place-order"))
            value = self._contrast_value(paint, "border")
            if value is not None:
                self.book.check(gate, value >= 3.0, "non-text-control-contrast", f"place-order border: {value:.2f}")
            focus = self._focus_style(self.locator("place-order"))
            outline = dict(paint)
            outline["foreground"] = focus.get("outlineColor")
            outline_value = self._contrast_value(outline)
            self.book.check(
                gate,
                outline_value is not None and outline_value >= 3.0 and focus.get("outlineStyle") not in ("none", ""),
                "focus-contrast",
                f"focus contrast={outline_value}",
            )

    def keyboard_gate(self) -> None:
        gate = "keyboard-completion-gate"
        assert self.page is not None
        self.page.reload(wait_until="load")
        self.page.emulate_media(reduced_motion="reduce")
        focusables = self.page.locator(
            f'{hook_selector("checkout-root")} button, {hook_selector("checkout-root")} input, '
            f'{hook_selector("checkout-root")} select, {hook_selector("checkout-root")} textarea, '
            f'{hook_selector("checkout-root")} a[href], {hook_selector("checkout-root")} [tabindex]:not([tabindex="-1"])'
        )
        visible_count = sum(1 for i in range(focusables.count()) if focusables.nth(i).is_visible() and focusables.nth(i).is_enabled())
        self.metrics["focusable_controls_traversed"] += visible_count
        self.book.check(gate, visible_count >= 8, "keyboard-focusable-controls", visible_count)
        if visible_count:
            first = next((focusables.nth(i) for i in range(focusables.count()) if focusables.nth(i).is_visible() and focusables.nth(i).is_enabled()), None)
            if first:
                first.focus()
                sequence: list[str] = []
                for _ in range(min(visible_count + 3, 60)):
                    active = self.page.evaluate("() => document.activeElement && (document.activeElement.id || document.activeElement.outerHTML.slice(0, 80))")
                    sequence.append(str(active))
                    self.page.keyboard.press("Tab")
                escaped = "BODY" in sequence or "" in sequence
                self.book.check(gate, not escaped, "tab-order-remains-in-checkout", sequence[-5:])
                self.page.keyboard.press("Shift+Tab")
                back = self.page.evaluate("() => document.activeElement && document.activeElement.tagName")
                self.book.check(gate, back not in ("BODY", "HTML"), "shift-tab-operates", back)
        self.book.check(gate, self.count("place-order") == 1, "keyboard-place-order-target")
        completed = self.fill_all(keyboard=True)
        self.book.check(gate, completed, "keyboard-text-entry-and-task-controls")
        edit_hook = next(
            (hook for hook in ("edit-contact", "edit-address", "edit-shipping", "edit-payment") if self.visible(hook)),
            None,
        )
        self.book.check(gate, edit_hook is not None, "keyboard-edit-control-available", edit_hook)
        if edit_hook:
            self.book.check(gate, self.activate(edit_hook), "keyboard-edit-activation", edit_hook)
            self.book.check(gate, self.visible("contact-name"), "keyboard-edit-restores-field", self.value("contact-name"))
        self.book.check(gate, self.set_shipping("standard"), "keyboard-space-shipping")
        self.book.check(gate, self.set_review(True), "keyboard-space-review")
        self.book.check(gate, self.submit(), "keyboard-enter-place-order")
        try:
            self.page.wait_for_selector(hook_selector("confirmation-id"), state="visible", timeout=1200)
        except PlaywrightTimeoutError:
            pass
        self.metrics["completion_interactions"] += 1
        self.book.check(gate, self.confirmation_count() == 1, "keyboard-confirmation", self.confirmation_count())
        self._screenshot("keyboard-completion")
        self.contrast_gate()

    def error_gate(self) -> None:
        gate = "error-recovery-gate"
        assert self.page is not None
        self.page.reload(wait_until="load")
        self.clear_fields()
        self.set_review(False)
        self.submit()
        self.page.wait_for_timeout(40)
        summary_text = self.text("error-summary")
        self.book.check(gate, bool(summary_text) and self.visible("error-summary"), "empty-submit-actionable-summary", summary_text)
        invalid_fields = 0
        for hook in FIELDS:
            if self.count(hook) and self.reveal(hook):
                control = self.locator(hook)
                invalid = control.get_attribute("aria-invalid") == "true"
                described = control.get_attribute("aria-describedby") or ""
                if invalid:
                    invalid_fields += 1
                    targets_exist = bool(described.strip()) and all(
                        self.page.locator(f"#{re.escape(target)}").count() == 1
                        for target in described.split()
                    )
                    self.book.check(gate, targets_exist, "invalid-field-error-association", f"{hook}: {described}")
        self.book.check(gate, invalid_fields >= 1, "empty-submit-invalid-fields", invalid_fields)
        active = self.page.evaluate("() => document.activeElement && (document.activeElement.getAttribute('data-hook') || document.activeElement.id || document.activeElement.tagName)")
        self.book.check(gate, active not in ("BODY", "HTML", None), "useful-error-focus", active)
        self.fill("contact-name", FIELDS["contact-name"])
        self.fill("contact-email", "not-an-email")
        self.fill("contact-phone", FIELDS["contact-phone"])
        self.fill("address-line1", FIELDS["address-line1"])
        self.fill("address-city", FIELDS["address-city"])
        self.fill("address-state", FIELDS["address-state"])
        self.fill("address-postcode", FIELDS["address-postcode"])
        self.fill("address-country", FIELDS["address-country"])
        self.fill("card-number", "1")
        self.fill("card-expiry", "1")
        self.fill("card-security", "1")
        self.fill("card-name", FIELDS["card-name"])
        self.set_shipping("standard")
        self.set_review(True)
        self.submit()
        self.page.wait_for_timeout(40)
        self.book.check(gate, self.visible("error-summary") or invalid_fields > 0, "invalid-submit-summary", self.text("error-summary"))
        self.book.check(gate, self.value("contact-name") == FIELDS["contact-name"], "preserve-valid-safe-value", self.value("contact-name"))
        self.metrics["corrections"] += 4
        corrected = self.fill_all()
        self.book.check(gate, corrected, "correction-and-resubmission-entry")
        self.submit()
        try:
            self.page.wait_for_selector(hook_selector("confirmation-id"), state="visible", timeout=1200)
        except PlaywrightTimeoutError:
            pass
        self.book.check(gate, self.confirmation_count() == 1, "corrected-resubmission-confirmation", self.confirmation_count())

    def mobile_gate(self) -> None:
        gate = "mobile-touch-gate"
        assert self.page is not None
        for width, height in VIEWPORTS:
            self.page.set_viewport_size({"width": width, "height": height})
            self.page.wait_for_timeout(20)
            dimensions = self.page.evaluate(
                """() => ({
                  width: innerWidth, scrollWidth: document.documentElement.scrollWidth,
                  height: innerHeight, bodyScrollWidth: document.body.scrollWidth
                })"""
            )
            self.book.check(gate, dimensions["scrollWidth"] <= width and dimensions["bodyScrollWidth"] <= width, "no-page-horizontal-overflow", f"{width}x{height}: {dimensions}")
            for hook in ("checkout-root", "synthetic-banner", "cart", "contact-section", "address-section", "shipping-section", "payment-section", "review-section", "place-order"):
                if not self.count(hook):
                    self.book.fail(gate, "required-element-present", f"{hook} at {width}x{height}")
                    continue
                rect = self.locator(hook).bounding_box()
                if rect:
                    self.book.check(gate, rect["x"] >= 0 and rect["x"] + rect["width"] <= width + 1, "required-element-not-clipped", f"{hook}: {rect}")
            interactive = self.page.locator(
                f'{hook_selector("checkout-root")} button, {hook_selector("checkout-root")} input, '
                f'{hook_selector("checkout-root")} select, {hook_selector("checkout-root")} textarea, '
                f'{hook_selector("checkout-root")} a[href], {hook_selector("checkout-root")} [data-checkout-interactive]'
            )
            for index in range(interactive.count()):
                target = interactive.nth(index)
                if not target.is_visible():
                    continue
                box = target.bounding_box()
                self.book.check(
                    gate,
                    bool(box and box["width"] >= 24 and box["height"] >= 24),
                    "interactive-target-minimum",
                    f"{width}x{height} target {index}: {box}",
                )
            self._screenshot(f"viewport-{width}x{height}")

    def resilience_gate(self) -> None:
        gate = "resilience-gate"
        assert self.page is not None
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.page.reload(wait_until="load")
        self.page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        self.page.reload(wait_until="load")
        for hook in SAFE_FIELDS:
            self.fill(hook, FIELDS[hook])
        self.set_shipping("standard")
        for hook in PAYMENT_FIELDS:
            self.fill(hook, FIELDS[hook])
        self.page.wait_for_timeout(50)
        before = self.storage()
        encoded = json.dumps(before, ensure_ascii=False).lower()
        for secret in ("4111", "12/34", "123", "card-number", "card-expiry", "card-security", "cvv", "security-code"):
            self.book.check(gate, secret.lower() not in encoded, "payment-secret-not-persisted", secret)
        self.page.reload(wait_until="load")
        restored = 0
        for hook in SAFE_FIELDS:
            try:
                if self.value(hook) == FIELDS[hook]:
                    restored += 1
            except PlaywrightError:
                pass
        self.book.check(gate, restored >= 5, "safe-state-restored-after-reload", restored)
        self.book.check(gate, all(self.value(hook) == "" for hook in PAYMENT_FIELDS), "payment-fields-cleared-after-reload")
        reduced = self.page.evaluate(
            """() => Array.from(document.querySelectorAll('*')).flatMap(el => {
              const s = getComputedStyle(el);
              return [...s.transitionDuration.split(','), ...s.animationDuration.split(',')]
                .map(x => parseFloat(x) * (x.includes('ms') ? 1 : 1000))
                .filter(x => Number.isFinite(x) && x > 10);
            })"""
        )
        self.book.check(gate, not reduced, "reduced-motion-nonessential-duration-max-10ms", reduced[:10])
        self.page.emulate_media(reduced_motion="reduce")
        complete = self.fill_all()
        self.submit()
        try:
            self.page.wait_for_selector(hook_selector("confirmation-id"), state="visible", timeout=1200)
        except PlaywrightTimeoutError:
            pass
        self.book.check(gate, complete and self.confirmation_count() == 1, "reduced-motion-completes-once", self.confirmation_count())

    def offline_gate(self) -> None:
        gate = "offline-safety-gate"
        assert self.page is not None
        self.page.reload(wait_until="load")
        self.page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        self.page.reload(wait_until="load")
        self.clear_fields()
        self.set_review(False)
        self.submit()
        self.page.wait_for_timeout(30)
        self.book.check(gate, self.confirmation_count() == 0, "invalid-or-unreviewed-placement-blocked", self.confirmation_count())
        completed = self.fill_all(include_review=False)
        self.book.check(gate, completed, "valid-local-fixture-entry")
        for hook, expected in FIELDS.items():
            self.book.check(
                "content-fidelity",
                self.value(hook) == expected,
                "canonical-field-value",
                f"{hook}: {self.value(hook)}",
            )
        self.book.check(
            "content-fidelity",
            "Standard — 3 to 5 business days" in self.text("shipping-standard"),
            "canonical-standard-shipping-label",
            self.text("shipping-standard"),
        )
        self.book.check(
            "content-fidelity",
            "Express — 1 to 2 business days" in self.text("shipping-express"),
            "canonical-express-shipping-label",
            self.text("shipping-express"),
        )
        self.page.evaluate(
            """() => {
              window.__harnessBusyEvents = [];
              const button = document.querySelector('[data-hook="place-order"]');
              const status = document.querySelector('[data-hook="status"]');
              const observer = new MutationObserver(() => {
                const buttonState = button && (
                  button.getAttribute('aria-busy') === 'true' ||
                  button.hasAttribute('disabled')
                );
                const statusText = status ? status.innerText.toLowerCase() : '';
                if (buttonState || /processing|placing|busy|saving/.test(statusText)) {
                  window.__harnessBusyEvents.push({buttonState, statusText});
                }
              });
              if (button) observer.observe(button, {attributes: true, attributeFilter: ['aria-busy', 'disabled']});
              if (status) observer.observe(status, {childList: true, subtree: true, characterData: true});
              window.__harnessBusyObserver = observer;
            }"""
        )
        review_checked = self.set_review(True)
        self.book.check(gate, review_checked, "review-required-before-placement")
        self.submit()
        self.page.wait_for_timeout(80)
        busy_events = self.page.evaluate("() => window.__harnessBusyEvents || []")
        self.book.check(gate, bool(busy_events), "busy-status-during-placement", busy_events)
        try:
            self.page.wait_for_selector(hook_selector("confirmation-id"), state="visible", timeout=1200)
        except PlaywrightTimeoutError:
            pass
        self.book.check(gate, self.confirmation_count() == 1, "deterministic-single-confirmation", self.confirmation_count())
        self.book.check(gate, self.text("confirmation-id") == "SYN-2048", "deterministic-confirmation-id", self.text("confirmation-id"))
        self.book.check(gate, not self.external_requests, "zero-external-runtime-requests", sorted(set(self.external_requests)))
        self.book.check(gate, self.visible("confirmation"), "confirmation-visible-after-explicit-placement")
        before = self.confirmation_count()
        self.activate("place-order", "Space")
        self.page.wait_for_timeout(150)
        self.book.check(gate, self.confirmation_count() == before == 1, "repeated-place-order-does-not-duplicate", self.confirmation_count())

    def report(self) -> dict[str, Any]:
        report = {
            "schema_version": REPORT_SCHEMA,
            "experiment_id": self.fixture.get("experiment_id"),
            "fixture_id": self.fixture.get("fixture_id"),
            "fixture_sha256": sha256(FIXTURE_PATH),
            "human_use": HUMAN_USE,
            "candidate": self.candidate.name,
            "candidate_entrypoint": "index.html",
            "gates": self.book.records(),
            "failed_gate_ids": self.book.failed_ids(),
            "metrics": self.metrics,
            "screenshots": sorted(self.screenshots),
            "external_requests": sorted(set(self.external_requests)),
            "blocking_failure": bool(self.book.failed_ids()),
        }
        atomic_json(self.out / "objective-report.json", report)
        lines = [
            "Accessible mobile checkout objective report",
            f"Fixture SHA-256: {report['fixture_sha256']}",
            f"Candidate: {report['candidate']}",
            "human_use.applicability = applicable",
            f"human_use.rationale: {HUMAN_USE['rationale']}",
            "",
        ]
        for entry in report["gates"]:
            lines.append(f"{entry['id']}: {entry['status'].upper()}")
            for assertion in entry["assertions"]:
                if assertion["status"] == "fail":
                    lines.append(f"  FAIL {assertion['assertion']}: {assertion['detail']}")
        lines.extend(
            [
                "",
                f"Failed gate IDs: {', '.join(report['failed_gate_ids']) or 'none'}",
                f"Blocking failure: {'yes' if report['blocking_failure'] else 'no'}",
                f"Non-gating task-efficiency metrics: {json.dumps(report['metrics'], sort_keys=True)}",
                f"Screenshots: {', '.join(report['screenshots']) or 'none'}",
            ]
        )
        atomic_write(self.out / "objective-report.txt", "\n".join(lines) + "\n")
        return report


def manifest_candidates(manifest_path: Path) -> list[tuple[str, Path]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    found: list[tuple[str, Path]] = []

    def walk(value: Any, context: str = "artifact") -> None:
        if isinstance(value, dict):
            presentation = str(value.get("presentation", "")).lower()
            role = str(value.get("role", "")).lower()
            artifact_type = str(value.get("type", "")).lower()
            is_html = "interactive_html" in (presentation, role, artifact_type) or artifact_type == "interactive_html"
            path_value = None
            for key in ("path", "relative_path", "file", "artifact_path", "relativePath"):
                if isinstance(value.get(key), str) and value[key].lower().endswith(".html"):
                    path_value = value[key]
                    break
            if is_html and path_value:
                primary = value.get("primary", value.get("is_primary", value.get("featured", True)))
                if primary is not False:
                    candidate = Path(path_value)
                    if not candidate.is_absolute():
                        candidate = (manifest_path.parent / candidate).resolve()
                    found.append((str(value.get("id") or value.get("artifact_id") or context), candidate.parent))
            for key, child in value.items():
                walk(child, f"{context}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{context}[{index}]")

    walk(manifest)
    unique: dict[str, tuple[str, Path]] = {}
    for identifier, candidate in found:
        if (candidate / "index.html").is_file():
            unique[str(candidate)] = (identifier, candidate)
    return list(unique.values())


def run_single(candidate: Path, out: Path, fixture: dict[str, Any]) -> dict[str, Any]:
    try:
        return CheckoutHarness(candidate, out, fixture).run()
    except Exception as exc:  # ensure a diagnostic report exists for every candidate
        book = GateBook()
        for gate_id in GATE_IDS:
            book.fail(gate_id, "harness-exception", f"{type(exc).__name__}: {exc}")
        report = {
            "schema_version": REPORT_SCHEMA,
            "experiment_id": fixture.get("experiment_id"),
            "fixture_id": fixture.get("fixture_id"),
            "fixture_sha256": sha256(FIXTURE_PATH),
            "human_use": HUMAN_USE,
            "candidate": candidate.name,
            "candidate_entrypoint": "index.html",
            "gates": book.records(),
            "failed_gate_ids": book.failed_ids(),
            "metrics": {},
            "screenshots": [],
            "external_requests": [],
            "blocking_failure": True,
        }
        atomic_json(out / "objective-report.json", report)
        atomic_write(out / "objective-report.txt", f"Harness exception: {type(exc).__name__}: {exc}\nFailed gate IDs: {', '.join(report['failed_gate_ids'])}\n")
        return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate", type=Path)
    group.add_argument("--manifest", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--all", action="store_true", help="Run every primary interactive_html Artifact in a Manifest.")
    parser.add_argument("--require-all-gates", action="store_true", help="Return nonzero unless every report passes every blocking gate.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if args.candidate:
        out = args.out or (args.candidate / "evidence")
        report = run_single(args.candidate, out, fixture)
        return 1 if report["blocking_failure"] else 0
    manifest = args.manifest.resolve()
    candidates = manifest_candidates(manifest)
    out = (args.out or (manifest.parent / "evidence")).resolve()
    reports = []
    for identifier, candidate in candidates:
        safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", identifier).strip("_") or candidate.name
        reports.append(run_single(candidate, out / safe_id, fixture))
    summary = {
        "schema_version": REPORT_SCHEMA,
        "manifest": manifest.name,
        "human_use": HUMAN_USE,
        "candidate_count": len(reports),
        "reports": [
            {"candidate": report["candidate"], "failed_gate_ids": report["failed_gate_ids"], "blocking_failure": report["blocking_failure"]}
            for report in reports
        ],
        "all_gates_pass": bool(reports) and all(not report["blocking_failure"] for report in reports),
    }
    atomic_json(out / "manifest-objective-report.json", summary)
    atomic_write(
        out / "manifest-objective-report.txt",
        "\n".join(
            [
                f"Manifest: {manifest.name}",
                f"Candidates: {summary['candidate_count']}",
                f"All required gates pass: {'yes' if summary['all_gates_pass'] else 'no'}",
                *[
                    f"{row['candidate']}: {'PASS' if not row['blocking_failure'] else 'FAIL'} ({', '.join(row['failed_gate_ids']) or 'none'})"
                    for row in summary["reports"]
                ],
            ]
        )
        + "\n",
    )
    if args.require_all_gates:
        return 0 if summary["all_gates_pass"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
