"""Expanding Brain meme template (4 levels)."""
from PIL import Image, ImageDraw
from .base_template import BaseMemeTemplate


class ExpandingBrainTemplate(BaseMemeTemplate):
    name = "expanding_brain"
    template_filename = "expanding_brain.jpg"

    def render(self, meme_data: dict) -> Image.Image:
        panels = meme_data.get("panels", [])
        while len(panels) < 4:
            panels.append("")

        try:
            img = self.get_template_image()
        except FileNotFoundError:
            img = self._generate_placeholder(panels)
            return img

        draw = ImageDraw.Draw(img)
        w, h = img.size
        panel_h = h // 4
        font = self.get_font(28)

        # Text goes on the left side of each panel
        for i, text in enumerate(panels[:4]):
            y_start = i * panel_h
            self.draw_text_in_box(
                draw, text,
                box=(0, y_start, w // 2, y_start + panel_h),
                font=font, fill=(0, 0, 0), padding=10,
            )

        return img

    def _generate_placeholder(self, panels: list) -> Image.Image:
        panel_h = 150
        w = 800
        h = panel_h * 4
        img = Image.new("RGB", (w, h), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        font = self.get_font(24)

        colors = [
            (240, 240, 240),
            (220, 230, 255),
            (200, 220, 255),
            (180, 200, 255),
        ]
        brain_labels = [
            "\U0001f9e0",
            "\U0001f9e0\u2728",
            "\U0001f9e0\U0001f4a1",
            "\U0001f9e0\U0001f525\U0001f680",
        ]

        for i in range(4):
            y = i * panel_h
            # Background
            draw.rectangle([0, y, w, y + panel_h], fill=colors[i])
            # Divider
            draw.line([(0, y), (w, y)], fill=(200, 200, 200), width=1)
            # Brain icon on right
            draw.text((w * 0.75, y + panel_h // 2), brain_labels[i],
                      font=font, fill=(0, 0, 0), anchor="mm")
            # Text on left
            if i < len(panels) and panels[i]:
                self.draw_text_in_box(
                    draw, panels[i],
                    box=(0, y, w // 2, y + panel_h),
                    font=font, fill=(0, 0, 0), padding=10,
                )

        return img
