#!/usr/bin/env python3
"""List the English text blocks of index.html that a language file does not translate yet.

    python3 i18n/check.py            # report, exit 1 if anything is missing
    python3 i18n/check.py --dump     # also write i18n/_keys.json (all English blocks, for translating; not committed)

Opens the page in Chromium (Playwright) in light and dark mode, so blocks written by the page's own scripts
(project list, theme button) are counted too. i18n/keep.json lists blocks that stay as they are in every
language (names of people, tools and repositories). Dates in <time> are left to the browser and are not listed.
"""
import functools
import http.server
import json
import re
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
LANGS = ['bn', 'es', 'zh', 'tl', 'vi']
# text set by scripts only after a click
EXTRA = ['Copied', 'Selected', 'Copy']


def has_words(s):
    plain = re.sub(r'<[^>]+>', ' ', s)
    return re.search(r'[A-Za-z]{2,}', plain) is not None


def page_keys():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/index.html?lang=en'
    keys = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for scheme in ('light', 'dark'):
            page = browser.new_page(color_scheme=scheme)
            page.route('**/*', lambda r: r.continue_() if '127.0.0.1' in r.request.url else r.abort())
            page.goto(url)
            page.wait_for_function('window.rbI18n')
            for item in page.evaluate('rbI18n.keys()'):
                if not item['time']:
                    keys.setdefault(item['k'], None)
            page.close()
        browser.close()
    server.shutdown()
    for k in EXTRA:
        keys.setdefault(k, None)
    return [k for k in keys if has_words(k)]


def main():
    keys = page_keys()
    if '--dump' in sys.argv:
        (ROOT / 'i18n' / '_keys.json').write_text(json.dumps(keys, ensure_ascii=False, indent=1))
    keep_file = ROOT / 'i18n' / 'keep.json'
    keep = set(json.loads(keep_file.read_text())) if keep_file.exists() else set()
    keys = [k for k in keys if k not in keep]
    missing_any = False
    for code in LANGS:
        f = ROOT / 'i18n' / f'{code}.json'
        d = json.loads(f.read_text()) if f.exists() else {}
        missing = [k for k in keys if k not in d]
        unused = [k for k in d if k not in keys and k not in ('now',)]
        print(f'{code}: {len(keys) - len(missing)}/{len(keys)} blocks translated, {len(unused)} unused entries')
        for k in missing[:20]:
            print('   missing:', k[:110])
        missing_any |= bool(missing)
    sys.exit(1 if missing_any else 0)


if __name__ == '__main__':
    main()
