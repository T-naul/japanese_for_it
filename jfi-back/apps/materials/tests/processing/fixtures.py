import tempfile


def create_synthetic_pdf_bytes(pages_text: list[str]) -> bytes:
    """
    Creates an uncompressed valid minimal PDF with the given list of page texts.
    """
    lines = [b"%PDF-1.4\n"]
    offsets = []

    def add(b: bytes):
        offsets.append(sum(len(x) for x in lines))
        lines.append(b)

    num_pages = len(pages_text)
    # obj 1: Catalog
    add(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    # obj 2: Pages
    kids = " ".join(f"{3 + i * 2} 0 R" for i in range(num_pages))
    add(f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {num_pages} >>\nendobj\n".encode("utf-8"))

    for i, text in enumerate(pages_text):
        p_id = 3 + i * 2
        c_id = 4 + i * 2
        add(
            f"{p_id} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {c_id} 0 R >>\nendobj\n".encode(
                "utf-8"
            )
        )
        stream_data = f"BT\n/F1 12 Tf\n72 712 Td\n({text}) Tj\nET".encode("utf-8")
        add(
            f"{c_id} 0 obj\n<< /Length {len(stream_data)} >>\nstream\n".encode("utf-8")
            + stream_data
            + b"\nendstream\nendobj\n"
        )

    xref_offset = sum(len(x) for x in lines)
    tot = 2 + num_pages * 2
    lines.append(f"xref\n0 {tot + 1}\n0000000000 65535 f \n".encode("utf-8"))
    for off in offsets:
        lines.append(f"{off:010d} 00000 n \n".encode("utf-8"))
    lines.append(
        f"trailer\n<< /Size {tot + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("utf-8")
    )
    return b"".join(lines)


def write_synthetic_pdf_file(pages_text: list[str], filepath: str):
    content = create_synthetic_pdf_bytes(pages_text)
    with open(filepath, "wb") as f:
        f.write(content)


class MockFitzRect:
    def __init__(self, width=595.0, height=842.0):
        self.width = width
        self.height = height


class MockFitzPage:
    def __init__(self, text, width=595.0, height=842.0):
        self._text = text
        self.rect = MockFitzRect(width, height)

    def get_text(self):
        return self._text


class MockFitzDoc:
    def __init__(self, pages_text: list[str]):
        self.pages = [MockFitzPage(t) for t in pages_text]
        self.closed = False

    def __iter__(self):
        return iter(self.pages)

    def close(self):
        self.closed = True


class MockFitzLib:
    def __init__(self, pages_text: list[str] = None, raise_on_open: Exception = None):
        self.pages_text = pages_text or []
        self.raise_on_open = raise_on_open

    def open(self, path):
        if self.raise_on_open:
            raise self.raise_on_open
        return MockFitzDoc(self.pages_text)
