import google.generativeai as genai
from groq import Groq

from backend.config import get_settings
from backend.core.exceptions import LLMError, LLMRateLimitError
from backend.core.logging import get_logger
from generation.prompt_templates import SYSTEM_PROMPT, build_qa_prompt

settings = get_settings()
logger = get_logger(__name__)


class AnswerGenerator:

    def __init__(self):
        self._groq_client: Groq | None = None
        self._gemini_configured = False

    def _get_groq_client(self) -> Groq:
        if self._groq_client is None:
            if not settings.groq_api_key:
                raise LLMError(provider="groq", reason="GROQ_API_KEY not configured.")
            self._groq_client = Groq(api_key=settings.groq_api_key)
        return self._groq_client

    def _configure_gemini(self) -> None:
        if not self._gemini_configured:
            if not settings.gemini_api_key:
                raise LLMError(provider="gemini", reason="GEMINI_API_KEY not configured.")
            genai.configure(api_key=settings.gemini_api_key)
            self._gemini_configured = True

    def generate(self, query: str, context_chunks: list[dict]) -> dict:
        prompt = build_qa_prompt(query, context_chunks)

        try:
            answer = self._generate_with_groq(prompt)
            return {
                "answer": answer,
                "provider": "groq",
                "model": settings.groq_model,
            }
        except (LLMError, LLMRateLimitError) as e:
            logger.warning("Groq failed, falling back to Gemini", error=str(e))

        try:
            answer = self._generate_with_gemini(prompt)
            return {
                "answer": answer,
                "provider": "gemini",
                "model": settings.gemini_model,
            }
        except (LLMError, LLMRateLimitError) as e:
            logger.error("Both LLM providers failed", error=str(e))
            raise LLMError(
                provider="all", reason="Both Groq and Gemini failed to generate an answer."
            )

    def _generate_with_groq(self, prompt: str) -> str:
        try:
            client = self._get_groq_client()
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            return response.choices[0].message.content

        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "429" in error_str:
                raise LLMRateLimitError(provider="groq")
            raise LLMError(provider="groq", reason=str(e))

    def _generate_with_gemini(self, prompt: str) -> str:
        try:
            self._configure_gemini()
            model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                system_instruction=SYSTEM_PROMPT,
            )
            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "429" in error_str or "quota" in error_str:
                raise LLMRateLimitError(provider="gemini")
            raise LLMError(provider="gemini", reason=str(e))
