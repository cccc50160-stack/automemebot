"""Distracted Boyfriend meme template."""
from PIL import Image, ImageDraw
from .base_template import BaseMemeTemplate


class DistractedBfTemplate(BaseMemeTemplate):
    name = "distracted_bf"
    template_filename = "distracted_bf.jpg"

    def render(self, meme_data: dict) -> Image.Image:
        panels = meme_data.get("panels", [])
        # panels[0] = Guy, panels[1] = Girlfriend, panels[2] = Other girl
        while len(panels) < 3:
            panels.append("")

        try:
            img = self.get_template_image()
        except FileNotFoundError:
            img = self._generate_placeholder()

        draw = ImageDraw.Draw(img)
        w, h = img.size
        font = self.get_font(28)

        # Label positions (approximate for standard distracted bf image)
        # Other girl (left): ~15% from left, ~60% from top
        # Guy (center): ~50% from left, ~50% from top
        # Girlfriend (right): ~80% from left, ~55% from top

        labels = [
            (panels[0], int(w * 0.50), int(h * 0.15)),  # Guy - top
            (panels[1], int(w * 0.82), int(h * 0.15)),   # Girlfriend - top right
            (panels[2], int(w * 0.18), int(h * 0.15)),   # Other girl - top left
        ]

        for text, x, y in labels:
            if text:
                wrapped = self.wrap_text(text, 18)
                self.draw_text_with_stroke(
                    draw, (x, y), wrapped, font,
                    fill=(255, 255, 255),
                    stroke_fill=(0, 0, 0),
                    stroke_width=3,
                    anchor="mt",
                )

        return img

    def _generate_placeholder(self) -> Image.Image:
        img = Image.new("RGB", (800, 500), (200, 220, 240))
        draw = ImageDraw.Draw(img)
        font = self.get_font(20)

        # Three figure placeholders
        positions = [
            (200, 250, "Other girl"),
            (400, 250, "Guy"),
            (600, 250, "Girlfriend"),
        ]
        for x, y, label in positions:
            draw.ellipse([x-40, y-80, x+40, y], fill=(180, 180, 180))
            draw.text((x, y+20), label, font=font, fill=(0, 0, 0), anchor="mt")

        return img
