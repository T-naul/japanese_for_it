from dataclasses import dataclass, field
import os
import re
from .exceptions import PDFProcessingError

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz  # Legacy name for PyMuPDF < 1.24.3
    except ImportError:
        fitz = None


@dataclass
class ParsedPage:
    page_number: int
    text: str
    width: float | None = None
    height: float | None = None
    has_text: bool = False
    metadata: dict = field(default_factory=dict)


class PDFParser:
    def __init__(self, fitz_lib=None):
        self._fitz = fitz_lib if fitz_lib is not None else fitz

    def parse(self, file_path: str) -> list[ParsedPage]:
        if not os.path.exists(file_path):
            raise PDFProcessingError(f"File not found: {file_path}")

        # Check basic file validity
        try:
            with open(file_path, "rb") as f:
                header = f.read(1024)
            if b"%PDF" not in header:
                raise PDFProcessingError(f"Invalid PDF file header: {file_path}")
        except PDFProcessingError:
            raise
        except Exception as exc:
            raise PDFProcessingError(f"Cannot read PDF file: {exc}") from exc

        if self._fitz is not None:
            return self._parse_with_fitz(file_path)
        else:
            return self._parse_fallback(file_path)

    def _parse_with_fitz(self, file_path: str) -> list[ParsedPage]:
        try:
            doc = self._fitz.open(file_path)
        except Exception as exc:
            raise PDFProcessingError(f"PyMuPDF failed to open file: {exc}") from exc

        parsed_pages = []
        try:
            for idx, page in enumerate(doc, start=1):
                try:
                    text = page.get_text() or ""
                except Exception:
                    text = ""

                width = None
                height = None
                if hasattr(page, "rect") and page.rect:
                    try:
                        width = float(page.rect.width)
                        height = float(page.rect.height)
                    except Exception:
                        pass

                has_text = bool(text and text.strip())
                metadata = {
                    "page_number": idx,
                    "char_count": len(text),
                    "has_text": has_text,
                }
                parsed_pages.append(
                    ParsedPage(
                        page_number=idx,
                        text=text,
                        width=width,
                        height=height,
                        has_text=has_text,
                        metadata=metadata,
                    )
                )
        finally:
            if hasattr(doc, "close"):
                doc.close()

        return parsed_pages

    def _parse_fallback(self, file_path: str) -> list[ParsedPage]:
        """
        Pure-Python fallback parser for synthetic PDF fixtures and environments
        where PyMuPDF is not installed.
        """
        try:
            with open(file_path, "rb") as f:
                content = f.read()
        except Exception as exc:
            raise PDFProcessingError(f"Error reading file {file_path}: {exc}") from exc

        # Check for uncompressed page markers or stream content
        # Standard synthetic test PDFs often separate pages by /Type /Page or page comments
        page_splits = re.split(rb"/Type\s*/Page\b", content)
        parsed_pages = []

        if len(page_splits) > 1:
            for idx, chunk in enumerate(page_splits[1:], start=1):
                page_text = self._extract_text_from_chunk(chunk)
                has_text = bool(page_text and page_text.strip())
                metadata = {
                    "page_number": idx,
                    "char_count": len(page_text),
                    "has_text": has_text,
                }
                parsed_pages.append(
                    ParsedPage(
                        page_number=idx,
                        text=page_text,
                        width=595.0,
                        height=842.0,
                        has_text=has_text,
                        metadata=metadata,
                    )
                )
        else:
            # Single page or fallback
            page_text = self._extract_text_from_chunk(content)
            has_text = bool(page_text and page_text.strip())
            parsed_pages.append(
                ParsedPage(
                    page_number=1,
                    text=page_text,
                    width=595.0,
                    height=842.0,
                    has_text=has_text,
                    metadata={
                        "page_number": 1,
                        "char_count": len(page_text),
                        "has_text": has_text,
                    },
                )
            )

        return parsed_pages

    def _extract_text_from_chunk(self, chunk: bytes) -> str:
        extracted = []
        # Match text in stream ... endstream
        streams = re.findall(rb"stream[\r\n]+([\s\S]*?)[\r\n]+endstream", chunk)
        target_bytes = b"\n".join(streams) if streams else chunk

        # Match (string) Tj or [(string)] TJ
        matches = re.findall(rb"\(([\s\S]*?)\)\s*Tj", target_bytes)
        for m in matches:
            try:
                extracted.append(m.decode("utf-8"))
            except UnicodeDecodeError:
                try:
                    extracted.append(m.decode("latin1"))
                except Exception:
                    pass

        if not extracted:
            # Check for hex strings <...> Tj
            hex_matches = re.findall(rb"<([0-9a-fA-F]+)>\s*Tj", target_bytes)
            for h in hex_matches:
                try:
                    extracted.append(bytes.fromhex(h.decode("ascii")).decode("utf-8"))
                except Exception:
                    pass

        return "\n".join(extracted)
