from pathlib import Path
import tempfile

from playwright.sync_api import sync_playwright


def generate_pdf_from_html(html: str) -> bytes:
    tmp = Path(tempfile.mkdtemp())
    html_path = tmp / "report.html"
    html_path.write_text(html, encoding="utf-8")
    output_path = tmp / "report.pdf"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        page = browser.new_page(
            viewport={"width": 1240, "height": 1754},
            device_scale_factor=2,
        )
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.wait_for_timeout(500)
        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
        )
        browser.close()

    return output_path.read_bytes()
