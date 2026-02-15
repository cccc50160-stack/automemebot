"""Abstract base class for all meme templates."""
import textwrap
from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config.settings import settings


class BaseMemeTemplate(ABC):
    """Base class for meme image generators."""

    name: str = "base"
    template_filename: str = ""

    # Default font settings
    FONT_SIZE = 42
    FONT_COLOR = (255, 255, 255)
    STROKE_COLOR = (0, 0, 0)
    STROKE_WIDTH = 2
    MAX_CHARS_PER_LINE = 25

    def __init__(self):
        self.fonts_dir = settings.fonts_dir
        self.templates_dir = settings.templates_dir

    def get_font(self, size: int = None) -> ImageFont.FreeTypeFont:
        """Load the Impact font (or fallback)."""
        size = size or self.FONT_SIZE
        font_path = self.fonts_dir / "impact.ttf"
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)
        # Fallback: try system fonts
        for name in ["impact.ttf", "Impact.ttf", "arial.ttf", "Arial.ttf"]:
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def get_template_image(self) -> Image.Image:
        """Load the template image."""
        path = self.templates_dir / self.template_filename
        if not path.exists():
            raise FileNotFoundError(f"Template image not found: {path}")
        return Image.open(path).convert("RGBA")

    def wrap_text(self, text: str, max_chars: int = None) -> str:
        """Wrap text to fit within max_chars per line."""
        max_chars = max_chars or self.MAX_CHARS_PER_LINE
        return "\n".join(textwrap.wrap(text, width=max_chars))

    def draw_text_with_stroke(self, draw: ImageDraw.ImageDraw, position: tuple,
                               text: str, font: ImageFont.FreeTypeFont,
                               fill=None, stroke_fill=None, stroke_width=None,
                               anchor=None):
        """Draw text with outline/stroke effect."""
        fill = fill or self.FONT_COLOR
        stroke_fill = stroke_fill or self.STROKE_COLOR
        stroke_width = stroke_width or self.STROKE_WIDTH

        draw.text(
            position, text, font=font, fill=fill,
            stroke_width=stroke_width, stroke_fill=stroke_fill,
            anchor=anchor,
        )

    def draw_centered_text(self, draw: ImageDraw.ImageDraw, text: str,
                            y: int, width: int, font: ImageFont.FreeTypeFont,
                            fill=None, stroke_fill=None):
        """Draw text centered horizontally at given y position."""
        wrapped = self.wrap_text(text)
        self.draw_text_with_stroke(
            draw, (width // 2, y), wrapped, font,
            fill=fill, stroke_fill=stroke_fill, anchor="mt"
        )

    def draw_text_in_box(self, draw: ImageDraw.ImageDraw, text: str,
                          box: tuple, font: ImageFont.FreeTypeFont,
                          fill=(0, 0, 0), stroke_fill=None, stroke_width=0,
                          padding: int = 10):
        """Draw text centered within a bounding box (x1, y1, x2, y2)."""
        x1, y1, x2, y2 = box
        box_w = x2 - x1 - 2 * padding
        box_h = y2 - y1 - 2 * padding

        # Auto-size font to fit box
        max_chars = max(10, box_w // (font.size * 0.6))
        wrapped = self.wrap_text(text, int(max_chars))

        # Reduce font size if text is too tall
        current_font = font
        bbox = draw.textbbox((0, 0), wrapped, font=current_font)
        text_h = bbox[3] - bbox[1]
        while text_h > box_h and current_font.size > 14:
            current_font = self.get_font(current_font.size - 2)
            max_chars = max(10, box_w // (current_font.size * 0.6))
            wrapped = self.wrap_text(text, int(max_chars))
            bbox = draw.textbbox((0, 0), wrapped, font=current_font)
            text_h = bbox[3] - bbox[1]

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        draw.text(
            (center_x, center_y), wrapped, font=current_font, fill=fill,
            anchor="mm", stroke_width=stroke_width, stroke_fill=stroke_fill,
        )

    @abstractmethod
    def render(self, meme_data: dict) -> Image.Image:
        """Render the meme and return a PIL Image."""
        ...

    def save(self, image: Image.Image, output_path: str | Path) -> str:
        """Save image to disk and return the path."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Convert RGBA to RGB for JPEG compatibility
        if image.mode == "RGBA":
            bg = Image.new("RGB", image.size, (255, 255, 255))
            bg.paste(image, mask=image.split()[3])
            image = bg
        image.save(str(output_path), quality=95)
        return str(output_path)
