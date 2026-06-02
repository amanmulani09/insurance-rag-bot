import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def pdf_to_text(pdf_path: str) -> str:
    logger.info("PDF read started: path=%s", pdf_path)
    reader = PdfReader(pdf_path)
    logger.info("PDF loaded: pages=%s", len(reader.pages))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        logger.debug("PDF page extracted: page=%s chars=%s", page_number, len(page_text))
        pages.append(page_text)
    text = "\n".join(pages)

    text = text.replace("\r", "\n")
    text = "\n".join([line.strip() for line in text.split("\n") if line.strip()])
    logger.info("PDF read complete: text_chars=%s", len(text))
    return text
