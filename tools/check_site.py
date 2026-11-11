#!/usr/bin/env python3
"""Check that README.md, index.html and resume.html show the numbers in data/portfolio.json.

    python3 tools/check_site.py

Exit 1 with a list of problems if a page shows a number that no longer matches the data, still shows one of the
old numbers, or the resume lost what an applicant tracking system (ATS) needs (contact lines, standard headings,
no tables or images).
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# numbers that were true once and must not come back in current text
STALE = {
    'README.md': ['2,033 automated tests', 'automated%20tests-2033', 'pass%20rate-100%25', 'HRA/DA/PF',
                  'passed-12-22c55e', 'passed-14-22c55e', 'README-v2.7'],
    'index.html': ['<span>2,033</span>', '12 passed · 3 skipped', '14 passed · 1 pending', '"100% pass rate"'],
    'resume.html': ['2,033', '36 of them'],
}


def fmt(n):
    return f'{n:,}'


def main():
    data = json.loads((ROOT / 'data' / 'portfolio.json').read_text(encoding='utf-8'))
    repos = data['repos']
    by_name = {r['name']: r for r in repos}
    total = sum(r['tests'] for r in repos)
    green = sum(1 for r in repos if r.get('workflow'))
    shop = by_name['RbcTcsWorld']['tests']
    suite = by_name['RbcTcsWorld_ECommerceSuite']['tests']
    pages = {name: (ROOT / name).read_text(encoding='utf-8') for name in ('README.md', 'index.html', 'resume.html')}
    problems = []

    def need(page, text, why):
        if text not in pages[page]:
            problems.append(f'{page}: missing "{text}" ({why})')

    # README
    need('README.md', f'**{fmt(total)}**', 'total automated tests')
    need('README.md', f'**{green} / {len(repos)}**', 'green CI count')
    need('README.md', f'**{len(repos)}**', 'public repositories')
    need('README.md', f'Public%20Repos-{len(repos)}', 'repository badge')
    need('README.md', f'automated%20tests-{shop}', 'Shop test badge')
    need('README.md', f'automated%20tests-{suite}', 'Suite test badge')
    for area in data['areas']:
        n = sum(r['tests'] for r in repos if r['area'] == area['key'])
        if n:
            need('README.md', f'"{area["label"][0].upper() + area["label"][1:]}" : {n}', f'tests pie, {area["key"]}')
    count = sum(1 for r in repos if r['area'] == 'web')
    need('README.md', f'"Web UI Automation" : {count}', 'repository pie')
    for r in repos:
        if f'https://github.com/rbchy/{r["name"]})' not in pages['README.md']:
            problems.append(f'README.md: repository {r["name"]} is not in the list of repositories')

    # website
    need('index.html', f'<span>{fmt(shop)}</span>', 'Shop tile')
    need('index.html', f'{fmt(total)} automated tests', 'latest news')
    need('index.html', f'({fmt(shop)} automated tests', 'og:description')

    # resume
    need('resume.html', f'{fmt(total)} automated tests', 'summary')
    need('resume.html', f'{fmt(shop)} automated tests', 'Shop project')
    need('resume.html', f'{fmt(suite)} UI, API', 'Suite project')
    need('resume.html', f'{len(repos)} public GitHub repositories', 'summary')
    resume = pages['resume.html']
    for h in ('Professional Summary', 'Technical Skills', 'Professional Experience', 'Education'):
        if f'<h2>{h}</h2>' not in resume:
            problems.append(f'resume.html: standard heading "{h}" missing')
    if re.search(r'<(table|img)\b', resume):
        problems.append('resume.html: tables or images confuse applicant tracking systems')
    if not re.search(r'\+1 \(\d{3}\) \d{3}-\d{4}', resume) or 'mailto:' not in resume:
        problems.append('resume.html: phone or e-mail missing from the contact line')
    if not (ROOT / 'resume.pdf').exists():
        problems.append('resume.pdf missing (python3 tools/make_resume_pdf.py)')

    for page, olds in STALE.items():
        for old in olds:
            if old in pages[page]:
                problems.append(f'{page}: still shows the old "{old}"')

    if problems:
        print('\n'.join(problems))
        return 1
    print(f'ok: {len(repos)} repositories, {green} with CI, {fmt(total)} tests; README, website and resume agree')
    return 0


if __name__ == '__main__':
    sys.exit(main())
