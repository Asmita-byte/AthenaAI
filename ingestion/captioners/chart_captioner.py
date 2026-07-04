from backend.core.logging import get_logger
from ingestion.captioners.image_captioner import ImageCaptioner

logger = get_logger(__name__)


class ChartCaptioner(ImageCaptioner):

    def caption_image(self, image_path: str) -> str:
        if not self._load_model()[0]:
            return self._fallback_caption(image_path)

        try:
            from PIL import Image
            import torch

            image = Image.open(image_path).convert("RGB")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {
                            "type": "text",
                            "text": "This image contains a chart or graph. Describe the type of chart, the axes, the data trends, and the key insights. Extract any numerical values visible.",
                        },
                    ],
                }
            ]

            model, processor = self._load_model()
            text_input = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = processor(text=[text_input], images=[image], return_tensors="pt")

            with torch.no_grad():
                output_ids = model.generate(**inputs, max_new_tokens=256)

            caption = processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
            logger.info("Chart captioned", image_path=image_path)
            return caption

        except Exception as e:
            logger.warning("Chart captioning failed", error=str(e))
            return self._fallback_caption(image_path)

    def _fallback_caption(self, image_path: str) -> str:
        from pathlib import Path
        return f"Chart or graph: {Path(image_path).stem}"