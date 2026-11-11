#!/usr/bin/env python3
"""Draw project-status.svg (the README's Project Status Board) from data/portfolio.json.

    python3 tools/make_status_svg.py           # write project-status.svg
    python3 tools/make_status_svg.py --check   # exit 1 if project-status.svg is out of date (used in CI)
"""
import json
import math
import pathlib
import sys
from html import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = "font-family=\"'Segoe UI', Helvetica, Arial, sans-serif\""


def text(x, y, s, size=13, weight=None, fill='#c3c2b7', anchor=None):
    w = f' font-weight="{weight}"' if weight else ''
    a = f' text-anchor="{anchor}"' if anchor else ''
    return f'<text x="{x}" y="{y}" {FONT} font-size="{size}"{w}{a} fill="{fill}">{escape(s)}</text>'


def fmt(n):
    return f'{n:,}'


def build(data):
    repos = data['repos']
    areas = data['areas']
    tested = [r for r in repos if r['tests'] > 0]
    with_ci = [r for r in repos if r.get('workflow')]
    total = sum(r['tests'] for r in repos)
    shop = next(r for r in repos if r['name'] == 'RbcTcsWorld')
    W, H = 1000, 560
    out = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
           f'aria-label="Project status board ({data["as_of"]}): {len(repos)} public repositories, {len(with_ci)} with green CI, '
           f'{fmt(total)} automated tests; RbcTcsWorld Shop {fmt(shop["tests"])} tests.">',
           f'<rect width="{W}" height="{H}" rx="12" fill="#141321"/>',
           text(32, 48, 'Project Status Board', 24, 700, '#fe428e'),
           text(32, 72, f'{len(repos)} public repositories · numbers from the latest green CI run on main ({data["as_of"]})')]
    tiles = [(str(len(repos)), 'public repositories', f'{len(tested)} with automated tests'),
             (f'{len(with_ci)} / {len(repos)}', 'green CI on main', 'GitHub Actions on every push'),
             (fmt(total), 'automated tests', 'sum over all repositories'),
             (fmt(shop['tests']), 'RbcTcsWorld Shop', '19 / 19 CI quality gates')]
    for i, (big, label, small) in enumerate(tiles):
        x = 32 + i * 237
        out += [f'<rect x="{x}" y="92" width="221" height="92" rx="10" fill="#1f1e33"/>',
                text(x + 16, 134, big, 30, 700, '#ffffff'), text(x + 16, 156, label, 13, 600),
                text(x + 16, 173, small, 12, fill='#8b8a9e')]

    # donut: automated tests by area
    out.append(text(32, 222, 'Automated tests by area', 15, 700, '#ffffff'))
    cx, cy, rad = 130, 345, 82
    by_area = [(a, sum(r['tests'] for r in repos if r['area'] == a['key'])) for a in areas]
    by_area = [(a, n) for a, n in by_area if n]
    start = -math.pi / 2
    for a, n in by_area:
        sweep = 2 * math.pi * n / total
        end = start + sweep
        large = 1 if sweep > math.pi else 0
        x1, y1 = cx + rad * math.cos(start), cy + rad * math.sin(start)
        x2, y2 = cx + rad * math.cos(end - 0.0001), cy + rad * math.sin(end - 0.0001)
        out.append(f'<path d="M{x1:.2f},{y1:.2f} A{rad},{rad} 0 {large} 1 {x2:.2f},{y2:.2f}" fill="none" '
                   f'stroke="{a["color"]}" stroke-width="26"><title>{escape(a["label"])}: {fmt(n)}</title></path>')
        start = end
    out += [text(cx, cy + 4, fmt(total), 24, 700, '#ffffff', 'middle'), text(cx, cy + 24, 'tests', 12, anchor='middle')]
    ly = 272
    for a, n in by_area:
        repos_in = sum(1 for r in repos if r['area'] == a['key'])
        out += [f'<rect x="246" y="{ly - 11}" width="12" height="12" rx="3" fill="{a["color"]}"/>',
                text(266, ly, a['label'], 13, 600, '#ffffff'),
                text(266, ly + 18, f'{fmt(n)} tests · {repos_in} repositories', 12, fill='#8b8a9e')]
        ly += 48

    # bars: the 12 repositories with the most tests
    out.append(text(470, 222, 'Tests per repository (top 12)', 15, 700, '#ffffff'))
    top = sorted(tested, key=lambda r: -r['tests'])[:12]
    colors = {a['key']: a['color'] for a in areas}
    peak = top[0]['tests']
    y = 244
    for r in top:
        name = r['name'] if len(r['name']) <= 30 else r['name'][:28] + '…'
        width = max(3, 250 * r['tests'] / peak)
        out += [text(470, y + 12, name, 12, fill='#c3c2b7'),
                f'<rect x="690" y="{y + 1}" width="{width:.1f}" height="14" rx="3" fill="{colors[r["area"]]}">'
                f'<title>{escape(r["name"])}: {fmt(r["tests"])} tests</title></rect>',
                text(696 + width, y + 12, fmt(r['tests']), 12, 600, '#ffffff')]
        y += 24
    out.append(text(32, H - 20, 'Source: data/portfolio.json (mirror of rbchy/ranajitchowdhury docs/portfolio.json)', 11,
                    fill='#8b8a9e'))
    out.append('</svg>')
    return '\n'.join(out) + '\n'


def main():
    data = json.loads((ROOT / 'data' / 'portfolio.json').read_text(encoding='utf-8'))
    svg = build(data)
    target = ROOT / 'project-status.svg'
    if '--check' in sys.argv:
        if target.read_text(encoding='utf-8') != svg:
            print('project-status.svg is out of date: run python3 tools/make_status_svg.py')
            return 1
        print('project-status.svg is up to date')
        return 0
    target.write_text(svg, encoding='utf-8')
    print(f'wrote {target.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
