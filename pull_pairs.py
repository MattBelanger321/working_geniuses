import fitz  # PyMuPDF
import requests
import json
import re
from io import BytesIO


PDF_URL = (
    "https://files.tablegroup.com/wp-content/uploads/2024/03/"
    "28064610/Student_Pairing_Descriptions.pdf"
)

OUTPUT_FILE = "working_genius_pairings.json"


def download_pdf(url):
    """Download PDF from website."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return BytesIO(response.content)


def extract_pdf_text(pdf_stream):
    """Extract text from PDF."""
    doc = fitz.open(stream=pdf_stream, filetype="pdf")

    pages = []

    for page in doc:
        pages.append(page.get_text("text"))

    return "\n".join(pages)


def clean_lines(text):
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def split_sections(lines):
    """
    Attempts to identify pairing sections.
    Adjust title detection if the PDF layout changes.
    """

    title_pattern = re.compile(
        r"(Creative Dreamer|"
        r"Contemplative Counselor|"
        r"Philosophical Motivator|"
        r"Idealistic Supporter|"
        r"Careful Implementer|"
        r"Discriminating Ideator|"
        r"Evangelizing Innovator|"
        r"Adaptable Designer|"
        r"Methodical Architect|"
        r"Intuitive Activator|"
        r"Insightful Collaborator|"
        r"Judicious Accomplisher|"
        r"Enthusiastic Encourager|"
        r"Driven Mobilizer|"
        r"Loyal Finisher)",
        re.IGNORECASE
    )

    sections = []
    current = None

    for line in lines:

        if title_pattern.search(line):

            if current:
                sections.append(current)

            current = {
                "title": line,
                "content": []
            }

        elif current:
            current["content"].append(line)

    if current:
        sections.append(current)

    return sections


def parse_section(section):

    geniuses = [
        "Wonder",
        "Invention",
        "Discernment",
        "Galvanizing",
        "Enablement",
        "Tenacity"
    ]

    content = section["content"]

    result = {
        "id": "",
        "title": section["title"],
        "geniuses": [],
        "description": [],
        "highlights": [],
        "craves": [],
        "crushedBy": []
    }

    text = " ".join(content)

    for genius in geniuses:
        if genius in text:
            result["geniuses"].append(genius)

    result["id"] = "".join(
        g[0] for g in result["geniuses"]
    )

    current_section = "description"

    for line in content:

        lower = line.lower()

        if "highlight" in lower:
            current_section = "highlights"
            continue

        if "crave" in lower:
            current_section = "craves"
            continue

        if "crushed" in lower:
            current_section = "crushedBy"
            continue

        result[current_section].append(line)

    return result


def main():

    print("Downloading PDF...")
    pdf = download_pdf(PDF_URL)

    print("Extracting text...")
    text = extract_pdf_text(pdf)

    lines = clean_lines(text)

    print("Finding pairings...")
    sections = split_sections(lines)

    print(f"Found {len(sections)} sections")

    data = {
        "version": "2024",
        "source": PDF_URL,
        "pairings": []
    }

    for section in sections:
        data["pairings"].append(
            parse_section(section)
        )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
