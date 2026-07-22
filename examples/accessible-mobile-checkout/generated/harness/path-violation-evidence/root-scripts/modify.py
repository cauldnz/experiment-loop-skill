import sys
path = '.experiments/accessible-mobile-checkout/generated/harness/run_checkout_gates_debug.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

target = '''            outline_value = self._contrast_value(outline)
            self.book.check(
                gate,
                outline_value is not None and outline_value >= 3.0 and focus.get("outlineStyle") not in ("none", ""),
                "focus-contrast",
                f"focus contrast={outline_value}",
            )'''

replacement = '''            outline_value = self._contrast_value(outline)
            print("DEBUG FOCUS:", focus)
            self.book.check(
                gate,
                outline_value is not None and outline_value >= 3.0 and focus.get("outlineStyle") not in ("none", ""),
                "focus-contrast",
                f"focus contrast={outline_value}",
            )'''

text = text.replace(target, replacement)
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
