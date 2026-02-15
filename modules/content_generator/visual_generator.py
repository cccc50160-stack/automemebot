"""Main visual meme generator — selects template and renders image."""
import uuid
from pathlib import Path
from PIL import Image
from config.settings import settings
from .templates.drake import DrakeTemplate
from .templates.distracted_bf import DistractedBfTemplate
from .templates.expanding_brain import ExpandingBrainTemplate
from .templates.two_buttons import TwoButtonsTemplate
from .templates.this_is_fine import ThisIsFineTemplate


class VisualGenerator:
    def __init__(self, logger=None):
        self.logger = logger
        self.output_dir = settings.data_dir / "generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.templates = {
            "drake": DrakeTemplate(),
            "distracted_bf": DistractedBfTemplate(),
            "expanding_brain": ExpandingBrainTemplate(),
            "two_buttons": TwoButtonsTemplate(),
            "this_is_fine": ThisIsFineTemplate(),
        }

    async def generate(self, meme_data: dict) -> str | None:
        """
        Generate a visual meme image.
        Returns the file path to the generated image, or None on failure.
        """
        meme_type = meme_data.get("type", "text_only")

        if meme_type == "text_only":
            return None  # Text memes don't need images

        template = self.templates.get(meme_type)
        if not template:
            if self.logger:
                await self.logger.log_warning(
                    "Unknown Template",
                    f"Template '{meme_type}' not found. Available: {list(self.templates.keys())}"
                )
            return None

        try:
            image = template.render(meme_data)
            filename = f"meme_{uuid.uuid4().hex[:8]}.jpg"
            output_path = self.output_dir / filename
            saved_path = template.save(image, output_path)

            if self.logger:
                file_size = Path(saved_path).stat().st_size // 1024
                await self.logger.log_system_event(
                    "Visual Meme Created",
                    f"Template: {meme_type}\nFile: {filename}\nSize: {file_size}KB"
                )

            return saved_path

        except Exception as e:
            if self.logger:
                await self.logger.log_error(
                    "Visual Generation Failed",
                    e,
                    {"module": "visual_generator", "function": "generate", "template": meme_type}
                )
            return None

    def get_available_templates(self) -> list[str]:
        return list(self.templates.keys())
