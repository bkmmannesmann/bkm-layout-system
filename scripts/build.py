#!/usr/bin/env python3
"""
BKM Layout System – Build-Skript
=================================
Generiert druckfertige PDFs aus HTML-Templates und JSON-Content.

Verwendung:
    python3 scripts/build.py <template-name> [--content <content.json>] [--output <output.pdf>]

Beispiel:
    python3 scripts/build.py prospekt-fachbetrieb
    python3 scripts/build.py prospekt-fachbetrieb --content content/prospekt-fachbetrieb/content.json --output output/prospekt.pdf
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("ERROR: Jinja2 nicht installiert. Bitte ausführen: pip3 install jinja2")
    sys.exit(1)

try:
    from weasyprint import HTML
except ImportError:
    print("ERROR: WeasyPrint nicht installiert. Bitte ausführen: pip3 install weasyprint")
    sys.exit(1)


# ──────────────────────────────────────────────────────────
# KONFIGURATION
# ──────────────────────────────────────────────────────────

ROOT_DIR = Path(__file__).parent.parent.resolve()
TEMPLATES_DIR = ROOT_DIR / "templates"
CONTENT_DIR = ROOT_DIR / "content"
OUTPUT_DIR = ROOT_DIR / "output"


def load_content(content_path: Path) -> dict:
    """Lädt die JSON-Content-Datei und gibt ein flaches Dictionary zurück."""
    with open(content_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Flatten: Alle verschachtelten Dictionaries auf eine Ebene bringen
    flat = {}
    for key, value in data.items():
        if isinstance(value, dict):
            flat.update(value)
        else:
            flat[key] = value

    return flat


def render_template(template_name: str, content: dict) -> str:
    """Rendert das HTML-Template mit Jinja2 und den Content-Daten."""
    template_dir = TEMPLATES_DIR / template_name
    if not template_dir.exists():
        print(f"ERROR: Template '{template_name}' nicht gefunden in {TEMPLATES_DIR}")
        sys.exit(1)

    # Jinja2 Environment mit dem Template-Verzeichnis
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
    )

    template = env.get_template("template.html")
    rendered_html = template.render(**content)

    return rendered_html


def generate_pdf(html_content: str, template_name: str, output_path: Path):
    """Generiert ein PDF aus dem gerenderten HTML mit WeasyPrint."""
    template_dir = TEMPLATES_DIR / template_name
    base_url = str(template_dir)

    print(f"  → Generiere PDF mit WeasyPrint...")
    print(f"  → Base URL: {base_url}")

    html = HTML(string=html_content, base_url=base_url)
    html.write_pdf(str(output_path))

    file_size = output_path.stat().st_size / 1024
    print(f"  ✓ PDF erstellt: {output_path} ({file_size:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(
        description="BKM Layout System – PDF-Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python3 scripts/build.py prospekt-fachbetrieb
  python3 scripts/build.py prospekt-fachbetrieb --output mein-prospekt.pdf
  python3 scripts/build.py prospekt-fachbetrieb --content content/custom/my-content.json
        """,
    )
    parser.add_argument(
        "template",
        help="Name des Templates (Verzeichnisname unter /templates/)",
    )
    parser.add_argument(
        "--content",
        help="Pfad zur Content-JSON-Datei (relativ zum Repo-Root)",
        default=None,
    )
    parser.add_argument(
        "--output",
        help="Pfad zur Ausgabe-PDF-Datei (relativ zum Repo-Root)",
        default=None,
    )

    args = parser.parse_args()

    # Content-Pfad bestimmen
    if args.content:
        content_path = ROOT_DIR / args.content
    else:
        content_path = CONTENT_DIR / args.template / "content.json"

    # Output-Pfad bestimmen
    if args.output:
        output_path = ROOT_DIR / args.output
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"{args.template}.pdf"

    # Prüfungen
    if not content_path.exists():
        print(f"ERROR: Content-Datei nicht gefunden: {content_path}")
        sys.exit(1)

    print(f"╔══════════════════════════════════════════════════╗")
    print(f"║  BKM Layout System – PDF Build                  ║")
    print(f"╚══════════════════════════════════════════════════╝")
    print(f"")
    print(f"  Template:  {args.template}")
    print(f"  Content:   {content_path}")
    print(f"  Output:    {output_path}")
    print(f"")

    # 1. Content laden
    print("  [1/3] Lade Content...")
    content = load_content(content_path)
    print(f"        {len(content)} Variablen geladen.")

    # 2. Template rendern
    print("  [2/3] Rendere Template...")
    html_content = render_template(args.template, content)
    print(f"        HTML generiert ({len(html_content)} Zeichen).")

    # 3. PDF generieren
    print("  [3/3] Generiere PDF...")
    generate_pdf(html_content, args.template, output_path)

    print(f"")
    print(f"  ══════════════════════════════════════════════════")
    print(f"  ✓ Fertig! PDF wurde erfolgreich erstellt.")
    print(f"  ══════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
