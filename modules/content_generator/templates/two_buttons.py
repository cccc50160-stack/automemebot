"""Two Buttons meme template (sweating guy choosing between two buttons)."""
from PIL import Image, ImageDraw
from .base_template import BaseMemeTemplate


class TwoButtonsTemplate(BaseMemeTemplate):
    name = "two_buttons"
    template_filename = "two_buttons.jpg"

    def render(self, meme_data: dict) -> Image.Image:
        panels = meme_data.get("panels", [])
        while len(panels) < 2:
            panels.append("")

        try:
            img = self.get_template_image()
        except FileNotFoundError:
            img = self._generate_placeholder()

        draw = ImageDraw.Draw(img)
        w, h = img.size
        font = self.get_font(26)

        # Two buttons at the top of the image
        # Left button: ~25% from left, ~20% from top
        # Right button: ~75% from left, ~20% from top
        button_y = int(h * 0.18)

        self.draw_text_with_stroke(
            draw, (int(w * 0.25), button_y), self.wrap_text(panels[0], 15),
            font, fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width=3,
            anchor="mm",
        )

        self.draw_text_with_stroke(
            draw, (int(w * 0.65), button_y), self.wrap_text(panels[1], 15),
            font, fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width=3,
            anchor="mm",
        )

        return img

    def _generate_placeholder(self) -> Image.Image:
        img = Image.new("RGB", (600, 500), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        font = self.get_font(20)

        # Two buttons
        draw.rounded_rectangle([50, 50, 270, 120], radius=10, fill=(255, 50, 50))
        draw.text((160, 85), "Button A", font=font, fill=(255, 255, 255), anchor="mm")

        draw.rounded_rectangle([330, 50, 550, 120], radius=10, fill=(50, 50, 255))
        draw.text((440, 85), "Button B", font=font, fill=(255, 255, 255), anchor="mm")

        # Sweating guy placeholder
        draw.ellipse([240, 200, 360, 350], fill=(255, 220, 180))
        draw.text((300, 400), "\U0001f630", font=self.get_font(40), fill=(0, 0, 0), anchor="mm")

        return img
