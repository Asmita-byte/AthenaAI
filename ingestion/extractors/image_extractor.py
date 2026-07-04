from pathlib import Path

from backend.config import get_settings
from backend.core.logging import get_logger
from ingestion.parsers.base_parser import ParsedImage

settings = get_settings()
logger = get_logger(__name__)


class ImageExtractor:

    def extract_from_pdf(self, file_path: Path) -> list[ParsedImage]:
        images = []
        images_dir = settings.storage_images_dir

        try:
            import fitz

            with fitz.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf, start=1):
                    for img_idx, img_info in enumerate(page.get_images(full=True)):
                        xref = img_info[0]
                        try:
                            base_image = pdf.extract_image(xref)
                            image_bytes = base_image["image"]
                            image_ext = base_image["ext"]

                            image_filename = (
                                f"{file_path.stem}_page{page_num}_img{img_idx}.{image_ext}"
                            )
                            image_path = images_dir / image_filename

                            with open(image_path, "wb") as f:
                                f.write(image_bytes)

                            images.append(
                                ParsedImage(
                                    image_index=img_idx,
                                    page_number=page_num,
                                    image_path=str(image_path),
                                    image_type="image",
                                )
                            )
                        except Exception as e:
                            logger.warning(
                                "Image extraction failed",
                                page=page_num,
                                error=str(e),
                            )

        except Exception as e:
            logger.warning("PDF image extraction failed", file=file_path.name, error=str(e))

        logger.info("Images extracted", file=file_path.name, count=len(images))
        return images
