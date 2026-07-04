from pathlib import Path

from backend.config import get_settings
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class ImageCaptioner:

    def __init__(self):
        self._model = None
        self._processor = None

    def _load_model(self):
        if self._model is None:
            if not settings.use_vlm_captioning:
                logger.info("VLM captioning disabled in config")
                return None, None

            try:
                import torch
                from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

                logger.info("Loading VLM model", model=settings.vlm_model)

                self._processor = AutoProcessor.from_pretrained(settings.vlm_model)
                self._model = Qwen2VLForConditionalGeneration.from_pretrained(
                    settings.vlm_model,
                    torch_dtype="auto",
                    device_map="cpu",
                )
                logger.info("VLM model loaded")

            except Exception as e:
                logger.warning("VLM model load failed — using fallback", error=str(e))
                return None, None

        return self._model, self._processor

    def caption_image(self, image_path: str) -> str:
        if not settings.use_vlm_captioning:
            return self._fallback_caption(image_path)

        model, processor = self._load_model()
        if model is None:
            return self._fallback_caption(image_path)

        try:
            import torch
            from PIL import Image

            image = Image.open(image_path).convert("RGB")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {
                            "type": "text",
                            "text": "Describe this image in detail. If it contains a table, chart, or diagram, explain the data and key insights shown.",
                        },
                    ],
                }
            ]

            text_input = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            inputs = processor(
                text=[text_input],
                images=[image],
                return_tensors="pt",
            )

            with torch.no_grad():
                output_ids = model.generate(**inputs, max_new_tokens=256)

            caption = processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()

            logger.info("Image captioned", image_path=image_path, caption_length=len(caption))
            return caption

        except Exception as e:
            logger.warning("VLM captioning failed", image_path=image_path, error=str(e))
            return self._fallback_caption(image_path)

    def caption_batch(self, image_paths: list[str]) -> list[str]:
        return [self.caption_image(path) for path in image_paths]

    def _fallback_caption(self, image_path: str) -> str:
        filename = Path(image_path).stem
        return f"Image: {filename}"
