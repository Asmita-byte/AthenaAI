import re

from backend.core.logging import get_logger

logger = get_logger(__name__)

MONEY_PATTERN = re.compile(r"\$[\d,]+(?:\.\d+)?(?:\s?(?:billion|million|thousand|B|M|K))?", re.IGNORECASE)
PERCENT_PATTERN = re.compile(r"\d+(?:\.\d+)?\s?%")
DATE_PATTERN = re.compile(r"\b(?:Q[1-4]\s)?\d{4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{4}\b", re.IGNORECASE)
ORG_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*(?:\s(?:Inc|Corp|Ltd|LLC|Co|Technologies|Solutions|Group|Holdings))?\b")


class EntityExtractor:

    def extract(self, text: str) -> dict:
        return {
            "monetary_values": self._extract_money(text),
            "percentages": self._extract_percentages(text),
            "dates": self._extract_dates(text),
            "organizations": self._extract_organizations(text),
        }

    def _extract_money(self, text: str) -> list[str]:
        return list(set(MONEY_PATTERN.findall(text)))

    def _extract_percentages(self, text: str) -> list[str]:
        return list(set(PERCENT_PATTERN.findall(text)))

    def _extract_dates(self, text: str) -> list[str]:
        return list(set(DATE_PATTERN.findall(text)))

    def _extract_organizations(self, text: str) -> list[str]:
        matches = ORG_PATTERN.findall(text)
        stopwords = {"The", "This", "That", "These", "Those", "With", "From", "Into"}
        return list(set(m for m in matches if m not in stopwords))