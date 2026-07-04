import os
import tempfile
import pytest
from pathlib import Path

from ingestion.parsers.txt_parser import TXTParser
from ingestion.parsers.base_parser import ParsedDocument


def create_temp_txt(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


class TestTXTParser:

    def test_parse_simple_text(self):
        path = create_temp_txt("Hello world.\n\nThis is a test paragraph.")
        parser = TXTParser()
        doc = parser.parse(path)

        assert isinstance(doc, ParsedDocument)
        assert doc.filename == path.name
        assert doc.file_extension == ".txt"
        assert len(doc.text_chunks) >= 1
        assert doc.has_text is True
        os.unlink(path)

    def test_parse_empty_file(self):
        path = create_temp_txt("")
        parser = TXTParser()
        doc = parser.parse(path)

        assert doc.total_chunks == 0
        os.unlink(path)

    def test_parse_multiple_paragraphs(self):
        content = "Para 1.\n\nPara 2.\n\nPara 3."
        path = create_temp_txt(content)
        parser = TXTParser()
        doc = parser.parse(path)

        assert len(doc.text_chunks) == 3
        os.unlink(path)

    def test_can_parse_txt(self):
        parser = TXTParser()
        assert parser.can_parse(Path("test.txt")) is True
        assert parser.can_parse(Path("test.pdf")) is False

    def test_supported_extensions(self):
        parser = TXTParser()
        assert ".txt" in parser.supported_extensions()