import sys
path = '.experiments/accessible-mobile-checkout/generated/harness/run_checkout_gates_debug.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

target = '''        for hook in samples:
            if not self.visible(hook):
                continue
            paint = self._element_paint(self.locator(hook))
            value = self._contrast_value(paint)
            if value is not None:
                seen += 1'''

replacement = '''        for hook in samples:
            if not self.visible(hook):
                print("DEBUG NOT VISIBLE:", hook)
                continue
            paint = self._element_paint(self.locator(hook))
            value = self._contrast_value(paint)
            print("DEBUG HOOK:", hook, "VALUE:", value)
            if value is not None:
                seen += 1'''

text = text.replace(target, replacement)
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
