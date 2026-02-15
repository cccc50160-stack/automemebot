"""This Is Fine meme template."""
from PIL import Image, ImageDraw
from .base_template import BaseMemeTemplate


class ThisIsFineTemplate(BaseMemeTemplate):
    name = "this_is_fine"
    template_filename = "this_is_fine.jpg"

    def render(self, meme_data: dict) -> Image.Image:
        text = meme_data.get("text", meme_data.get("text_top", "This is fine"))

        try:
            img = self.get_template_image()
        except FileNotFoundError:
            img = self._generate_placeholder()

        draw = ImageDraw.Draw(img)
        w, h = img.size
        font = self.get_font(36)

        # Text at the top of the image
        self.draw_centered_text(
            draw, text, y=15, width=w, font=font,
            fill=(255, 255, 255), stroke_fill=(0, 0, 0),
        )

        return img

    def _generate_placeholder(self) -> Image.Image:
        img = Image.new("RGB", (800, 450), (255, 150, 50))
        draw = ImageDraw.Draw(img)
        font = self.get_font(30)

        # Fire background
        for y in range(0, 450, 20):
            opacity = min(255, y + 100)
            draw.rectangle([0, y, 800, y + 20], fill=(255, max(0, 150 - y // 3), 0))

        # Dog with coffee placeholder
        draw.text((400, 300), "\U0001f436\u2615", font=self.get_font(50),
                  fill=(0, 0, 0), anchor="mm")
        draw.text((400, 380), "This is fine.", font=font,
                  fill=(0, 0, 0), anchor="mm")

        return img
