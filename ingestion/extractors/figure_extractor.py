from pathlib import Path

from backend.core.logging import get_logger
from ingestion.parsers.base_parser import ParsedImage

logger = get_logger(__name__)


class FigureExtractor:

    FIGURE_KEYWORDS = [
        "figure",
        "fig",
        "chart",
        "graph",
        "diagram",
        "plot",
        "visualization",
        "illustration",
    ]

    def classify_image(self, image_path: str, context_text: str = "") -> str:
        context_lower = context_text.lower()

        for keyword in self.FIGURE_KEYWORDS:
            if keyword in context_lower:
                return "figure"

        return "image"

    def extract_figures_from_pdf(self, file_path: Path) -> list[ParsedImage]:
        from ingestion.extractors.image_extractor import ImageExtractor

        all_images = ImageExtractor().extract_from_pdf(file_path)

        figures = []
        for image in all_images:
            image.image_type = self.classify_image(
                image.image_path,
                context_text="",
            )
            figures.append(image)

        logger.info(
            "Figures classified",
            file=file_path.name,
            total=len(figures),
            figures=[f for f in figures if f.image_type == "figure"],
        )

        return figures
