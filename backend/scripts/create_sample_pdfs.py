from pathlib import Path

import fitz


SAMPLES = {
    "trap_claims.pdf": [
        "ChatGPT launched in 2018.",
        "India has 900 million internet users.",
        "The company reported revenue of $12.8 billion in 2024.",
    ],
    "mixed_claims.pdf": [
        "Global smartphone shipments were 1.17 billion units in 2023.",
        "The Eiffel Tower is located in Berlin.",
        "OpenAI released GPT-4 in 2023.",
    ],
}


def create_pdf(path: Path, lines: list[str]) -> None:
    doc = fitz.open()
    page = doc.new_page()
    y = 72
    for line in lines:
        page.insert_text((72, y), line, fontsize=12)
        y += 28
    doc.save(path)
    doc.close()


def main() -> None:
    output_dir = Path(__file__).resolve().parents[1] / "sample_pdfs"
    output_dir.mkdir(exist_ok=True)
    for filename, lines in SAMPLES.items():
        create_pdf(output_dir / filename, lines)
    print(f"Created {len(SAMPLES)} sample PDFs in {output_dir}")


if __name__ == "__main__":
    main()

