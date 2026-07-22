import re

def _contrast_value(paint, prop="foreground") -> float:
    from math import pow
    def luminance(channels: tuple[float, float, float, float]) -> float:
        r, g, b, _ = channels
        return (
            0.2126 * (r / 12.92 if r <= 0.03928 else pow((r + 0.055) / 1.055, 2.4))
            + 0.7152 * (g / 12.92 if g <= 0.03928 else pow((g + 0.055) / 1.055, 2.4))
            + 0.0722 * (b / 12.92 if b <= 0.03928 else pow((b + 0.055) / 1.055, 2.4))
        )
    return (luminance((1.0, 1.0, 1.0, 1.0)) + 0.05) / (luminance((0.0, 0.0, 0.0, 1.0)) + 0.05)

paint = {'background': 'rgb(255, 255, 255)', 'foreground': 'rgb(0, 0, 0)'}
focus = {'active': True, 'outlineColor': 'rgb(0, 0, 0)', 'outlineWidth': '4px', 'outlineStyle': 'solid', 'boxShadow': 'none', 'borderColor': 'rgb(0, 0, 0)'}

outline = dict(paint)
outline['foreground'] = focus.get('outlineColor')

def luminance(channels) -> float:
    r, g, b, _ = channels
    return (
        0.2126 * (r / 12.92 if r <= 0.03928 else pow((r + 0.055) / 1.055, 2.4))
        + 0.7152 * (g / 12.92 if g <= 0.03928 else pow((g + 0.055) / 1.055, 2.4))
        + 0.0722 * (b / 12.92 if b <= 0.03928 else pow((b + 0.055) / 1.055, 2.4))
    )

def rgb(value: str):
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
    return None

c1 = rgb(outline.get('foreground', ''))
c2 = rgb(outline.get('background', ''))

l1 = luminance(c1)
l2 = luminance(c2)

contrast = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

condition = contrast is not None and contrast >= 3.0 and focus.get("outlineStyle") not in ("none", "")
print("Contrast:", contrast)
print("Condition:", condition)
