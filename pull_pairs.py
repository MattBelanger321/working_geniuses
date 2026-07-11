#!/usr/bin/env python3
"""
pdf_to_json.py

Downloads a PDF from a URL, parses each page, and extracts structured
"pairing description" data into a JSON file.

Expected per-page layout (Working Genius pairing description pages):
    PAIRING DESCRIPTIONS
    WI | IW
    The Genius of Wonder
    The Genius of Invention
    <highlight sentences...>
    POTENTIAL CHALLENGES:
    <challenge sentences...>
    THEY CRAVE:
    <2 bullets, each "<Value>. They ...">
    THEY ARE CRUSHED BY:
    <2 bullets, each "<Value>. They ...">
    <Title, e.g. "The Creative Dreamer">

Usage:
    python pdf_to_json.py <pdf_url> [-o output.json]

Example:
    python pdf_to_json.py "https://files.tablegroup.com/wp-content/uploads/2024/03/28064610/Student_Pairing_Descriptions.pdf" -o pairings.json

Output JSON structure (one object per page):
[
  {
    "pairing": "WI",
    "title": "The Creative Dreamer",
    "geniuses": ["Wonder", "Invention"],
    "sections": [
      {"heading": "Highlights", "content": ["...", "...", "..."]},
      {"heading": "Potential Challenges", "content": ["..."]},
      {"heading": "They Crave", "content": ["...", "..."]},
      {"heading": "They Are Crushed By", "content": ["...", "..."]}
    ]
  },
  ...
]
"""

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

import requests
import pdfplumber

# ---------------------------------------------------------------------------
# Regex patterns for the known page layout
# ---------------------------------------------------------------------------
FOOTER_RE = re.compile(r'^WorkingGenius\.com.*$', re.IGNORECASE)
HEADER_RE = re.compile(r'^PAIRING DESCRIPTIONS$', re.IGNORECASE)
CODE_RE = re.compile(r'^([A-Z]{2})\s*\|\s*([A-Z]{2})$')
GENIUS_RE = re.compile(r'^The Genius of\s+(\w+)\s*$', re.IGNORECASE)
TITLE_RE = re.compile(r'^The\s+[A-Z][a-zA-Z]*\s+[A-Z][a-zA-Z]*$')
POTENTIAL_RE = re.compile(r'^POTENTIAL CHALLENGES:?$', re.IGNORECASE)
CRAVE_RE = re.compile(r'^THEY CRAVE:?$', re.IGNORECASE)
CRUSHED_RE = re.compile(r'^THEY ARE CRUSHED BY:?$', re.IGNORECASE)

# Bullet items in "THEY CRAVE" / "THEY ARE CRUSHED BY" always look like:
#   "<Value phrase>. They <verb> ..."
# optionally with the value phrase itself wrapped in curly/straight quotes,
# e.g. "\u201cProve it.\u201d They dislike ..."
BULLET_START_RE = re.compile(
    r'(?:^|(?<=\s))([\u201c"]?[A-Z][A-Za-z\u2019\'\-\s]{0,30}?\.[\u201d"]?)\s+(?=They\s)'
)


def download_pdf(url: str, dest_path: Path, timeout: int = 30) -> None:
    """Download a PDF from a URL to a local path, streaming to disk."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PDFParserBot/1.0)"}
    with requests.get(url, headers=headers, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def split_sentences(text: str):
    """Split a block of prose into individual sentences."""
    text = text.strip()
    if not text:
        return []
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\u201c])', text)
    return [s.strip() for s in sentences if s.strip()]


def split_bullets(text: str):
    """Split a CRAVE / CRUSHED-BY block into its bullet items."""
    text = text.strip()
    if not text:
        return []
    starts = [m.start() for m in BULLET_START_RE.finditer(text)]
    if not starts:
        return [text]
    starts.append(len(text))
    bullets = []
    for i in range(len(starts) - 1):
        chunk = text[starts[i]:starts[i + 1]].strip()
        if chunk:
            bullets.append(chunk)
    return bullets


def parse_page(raw_text: str):
    """Parse a single page's raw extracted text into the structured schema."""
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    lines = [l for l in lines if not FOOTER_RE.match(
        l) and not HEADER_RE.match(l)]

    # Pairing code, e.g. "WI | IW" -> pairing = "WI"
    pairing = None
    code_idx = None
    for i, l in enumerate(lines):
        m = CODE_RE.match(l)
        if m:
            pairing = m.group(1)
            code_idx = i
            break
    lines = [l for i, l in enumerate(lines) if i != code_idx]

    # Geniuses, e.g. "The Genius of Wonder" -> "Wonder"
    geniuses = []
    genius_idxs = []
    for i, l in enumerate(lines):
        m = GENIUS_RE.match(l)
        if m and len(geniuses) < 2:
            geniuses.append(m.group(1))
            genius_idxs.append(i)
    lines = [l for i, l in enumerate(lines) if i not in genius_idxs]

    # Title, e.g. "The Creative Dreamer"
    title = None
    title_idx = None
    for i, l in enumerate(lines):
        if TITLE_RE.match(l) and 'genius' not in l.lower():
            title = l
            title_idx = i
            break
    lines = [l for i, l in enumerate(lines) if i != title_idx]

    # Locate section boundaries
    pc_idx = next((i for i, l in enumerate(lines)
                  if POTENTIAL_RE.match(l)), None)
    crave_idx = next((i for i, l in enumerate(
        lines) if CRAVE_RE.match(l)), None)
    crushed_idx = next((i for i, l in enumerate(lines)
                       if CRUSHED_RE.match(l)), None)

    highlights_lines = lines[:pc_idx] if pc_idx is not None else lines
    challenges_lines = lines[pc_idx +
                             1:crave_idx] if pc_idx is not None and crave_idx is not None else []
    crave_lines = lines[crave_idx +
                        1:crushed_idx] if crave_idx is not None and crushed_idx is not None else []
    crushed_lines = lines[crushed_idx + 1:] if crushed_idx is not None else []

    return {
        "pairing": pairing,
        "title": title,
        "geniuses": geniuses,
        "sections": [
            {"heading": "Highlights", "content": split_sentences(
                ' '.join(highlights_lines))},
            {"heading": "Potential Challenges",
                "content": split_sentences(' '.join(challenges_lines))},
            {"heading": "They Crave", "content": split_bullets(
                ' '.join(crave_lines))},
            {"heading": "They Are Crushed By",
                "content": split_bullets(' '.join(crushed_lines))},
        ],
    }


def parse_pdf(pdf_path: Path):
    """Parse every page of the PDF into the structured schema."""
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if not text.strip():
                continue
            results.append(parse_page(text))
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Parse each page of a Working Genius pairing-description PDF into structured JSON."
    )
    parser.add_argument("url", help="URL of the PDF to download and parse")
    parser.add_argument(
        "-o", "--output",
        default="output.json",
        help="Path to write the output JSON file (default: output.json)"
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_pdf_path = Path(tmp_dir) / "downloaded.pdf"

        print(f"Downloading PDF from: {args.url}")
        try:
            download_pdf(args.url, tmp_pdf_path)
        except requests.RequestException as e:
            print(f"Error downloading PDF: {e}", file=sys.stderr)
            sys.exit(1)

        print("Parsing PDF pages...")
        try:
            result = parse_pdf(tmp_pdf_path)
        except Exception as e:
            print(f"Error parsing PDF: {e}", file=sys.stderr)
            sys.exit(1)

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(
        f"Done. Parsed {len(result)} pairing pages -> {output_path.resolve()}")


if __name__ == "__main__":
    main()
