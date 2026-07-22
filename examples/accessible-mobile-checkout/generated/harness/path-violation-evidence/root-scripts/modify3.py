import sys
path = '.experiments/accessible-mobile-checkout/generated/harness/run_checkout_gates_debug.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

target = '''    def semantic_accessibility_gate(self) -> None:'''

replacement = '''    def semantic_accessibility_gate(self) -> None:
        self.page.screenshot(path="debug_before_semantic.png")'''

text = text.replace(target, replacement)
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
