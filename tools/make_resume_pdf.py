#!/usr/bin/env python3
"""Print resume.html to resume.pdf (US Letter, two pages, real text so an ATS can read it).

    python3 tools/make_resume_pdf.py            # write resume.pdf
    python3 tools/make_resume_pdf.py --check    # exit 1 if the PDF is longer than 2 pages or misses text
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARGIN = dict(top='0.4in', bottom='0.4in', left='0.55in', right='0.55in')


def render(path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(color_scheme='light')
        page.goto((ROOT / 'resume.html').as_uri())
        page.emulate_media(media='print')
        page.pdf(path=str(path), format='Letter', margin=MARGIN, print_background=False)
        browser.close()


def check(path):
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    text = ' '.join(pg.extract_text() for pg in reader.pages)
    problems = []
    if len(reader.pages) > 2:
        problems.append(f'{len(reader.pages)} pages, keep it to 2')
    for must in ('Ranajit Baran Chowdhury', 'QA Automation', 'PROFESSIONAL SUMMARY', 'TECHNICAL SKILLS',
                 'PROFESSIONAL EXPERIENCE', 'EDUCATION', 'chyranajit@gmail.com'):
        if must not in text:
            problems.append(f'"{must}" not readable in the PDF')
    return problems


def main():
    if '--check' in sys.argv:
        out = ROOT / 'build' / 'resume-check.pdf'
        out.parent.mkdir(exist_ok=True)
        render(out)
        problems = check(out) + check(ROOT / 'resume.pdf')
        print('\n'.join(problems) or 'resume PDF: 2 pages or less, text readable')
        return 1 if problems else 0
    render(ROOT / 'resume.pdf')
    print('wrote resume.pdf')
    return 0


if __name__ == '__main__':
    sys.exit(main())
