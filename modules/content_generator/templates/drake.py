"""Drake meme template (two panels: reject / approve)."""
from PIL import Image, ImageDraw
from .base_template import BaseMemeTemplate


class DrakeTemplate(BaseMemeTemplate):
    name = "drake"
    template_filename = "drake.jpg"

    def render(self, meme_data: dict) -> Image.Image:
        text_top = meme_data.get("text_top", "")
        text_bottom = meme_data.get("text_bottom", "")

        try:
            img = self.get_template_image()
        except FileNotFoundError:
            img = self._generate_placeholder()

        draw = ImageDraw.Draw(img)
        w, h = img.size

        # Drake template: left half is Drake, right half is text
        # Top-right box: reject text
        # Bottom-right box: approve text
        text_x1 = w // 2
        text_x2 = w
        mid_y = h // 2

        font = self.get_font(32)

        # Top panel text (reject)
        self.draw_text_in_box(
            draw, text_top,
            box=(text_x1, 0, text_x2, mid_y),
            font=font, fill=(0, 0, 0), padding=15,
        )

        # Bottom panel text (approve)
        self.draw_text_in_box(
            draw, text_bottom,
            box=(text_x1, mid_y, text_x2, h),
            font=font, fill=(0, 0, 0), padding=15,
        )

        return img

    def _generate_placeholder(self) -> Image.Image:
        """Generate a simple placeholder if template image is missing."""
        img = Image.new("RGB", (800, 800), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Top panel - red background (reject)
        draw.rectangle([0, 0, 400, 400], fill=(255, 200, 200))
        # Bottom panel - green background (approve)
        draw.rectangle([0, 400, 400, 800], fill=(200, 255, 200))

        font = self.get_font(24)
        draw.text((200, 200), "\u274c", font=font, fill=(200, 0, 0), anchor="mm")
        draw.text((200, 600), "\u2705", font=font, fill=(0, 150, 0), anchor="mm")

        # Divider lines
        draw.line([(0, 400), (800, 400)], fill=(0, 0, 0), width=2)
        draw.line([(400, 0), (400, 800)], fill=(0, 0, 0), width=2)

        return img
