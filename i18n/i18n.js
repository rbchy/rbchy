/*
 * Language switch of the portfolio page: English (the page itself), Bangla, Spanish, Chinese, Tagalog, Vietnamese, Korean.
 *
 * The page stays written in English. Each other language is one dictionary file, i18n/<code>.json, that maps an
 * English text block (the inner HTML of the smallest element holding text, with spaces collapsed) to its translation.
 * Anything without an entry stays English, so a new news item or project never breaks the page; it shows in English
 * until its translation is added. `python3 i18n/check.py` lists what is missing.
 *
 * Blocks rendered later by the page's own scripts (project filter, theme button) are translated as they appear.
 * Dates in <time> are written by the browser in the chosen language. Choice: ?lang=bn in the link, then the saved
 * choice, then the browser's language.
 */
(function () {
  'use strict';
  var LANGS = [
    ['en', 'English'], ['bn', 'বাংলা'], ['es', 'Español'], ['zh', '中文'], ['tl', 'Tagalog'], ['vi', 'Tiếng Việt'], ['ko', '한국어']
  ];
  var CODES = LANGS.map(function (l) { return l[0]; });
  var ATTRS = ['aria-label', 'title', 'alt', 'placeholder'];
  var SVG = 'http://www.w3.org/2000/svg';
  var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, PRE: 1, CODE: 1, NOSCRIPT: 1, TEMPLATE: 1, SELECT: 1, title: 1 };
  var MONTHS = { jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11 };
  var LETTER = /\p{L}/u;  // any script: a translated block must still be found to switch back

  var state = new WeakMap();      // element -> { src, out } of its text block
  var attrState = new WeakMap();  // element -> { attr: { src, out } }
  var cache = { en: {} };
  var dict = {};
  var lang = 'en';
  var observer = null;
  var originalTitle = document.title;

  var norm = function (s) { return s.replace(/\s+/g, ' ').trim(); };

  function skipped(el) {
    return SKIP_TAGS[el.tagName] || el.getAttribute('translate') === 'no' || el.classList.contains('notranslate');
  }

  function hasOwnText(el) {
    for (var n = el.firstChild; n; n = n.nextSibling) {
      if (n.nodeType === 3 && LETTER.test(n.nodeValue)) return true;
    }
    return false;
  }

  // The smallest elements that hold text directly; their inner markup (links, <b>, <code>) moves with them.
  function blocks(root, out) {
    for (var el = root.firstElementChild; el; el = el.nextElementSibling) {
      if (skipped(el)) continue;
      if (el.namespaceURI === SVG) {
        if (el.tagName === 'text' && LETTER.test(el.textContent)) out.push(el);
        else blocks(el, out);
      } else if (hasOwnText(el) && !el.querySelector('svg')) out.push(el);  // never rewrite a drawing
      else blocks(el, out);
    }
    return out;
  }

  function withAttrs(root) {
    var list = [];
    var sel = ATTRS.map(function (a) { return '[' + a + ']'; }).join(',');
    root.querySelectorAll(sel).forEach(function (el) {
      if (!el.closest('[translate="no"],.notranslate')) list.push(el);
    });
    return list;
  }

  function englishDate(text) {
    var m = /^(\d{1,2}) ([A-Za-z]{3})[a-z]* (\d{4})$/.exec(text);
    if (!m || !(m[2].toLowerCase() in MONTHS)) return null;
    return new Date(Date.UTC(+m[3], MONTHS[m[2].toLowerCase()], +m[1]));
  }

  function translated(el, src) {
    if (lang === 'en') return src;
    if (Object.prototype.hasOwnProperty.call(dict, src)) return dict[src];
    if (el.tagName === 'TIME') {
      var d = englishDate(src);
      if (d) return new Intl.DateTimeFormat(document.documentElement.lang, { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(d);
      if (/–now$/.test(src) && dict['now']) return src.replace(/now$/, dict['now']);
    }
    return src;
  }

  function sourceOf(saved, current) {
    // the page's own script may have changed the block since we translated it: then the new text is the English one
    return saved && current === saved.out ? saved.src : current;
  }

  function translateBlock(el) {
    var cur = norm(el.innerHTML);
    var src = sourceOf(state.get(el), cur);
    var out = translated(el, src);
    if (out !== cur) {
      if (el.namespaceURI === SVG) el.textContent = out; else el.innerHTML = out;
    }
    state.set(el, { src: src, out: norm(el.innerHTML) });
  }

  function translateAttrs(el) {
    var saved = attrState.get(el) || {};
    ATTRS.forEach(function (a) {
      if (!el.hasAttribute(a)) return;
      var cur = el.getAttribute(a);
      var src = sourceOf(saved[a], cur);
      var out = lang === 'en' ? src : (dict[src] || src);
      if (out !== cur) el.setAttribute(a, out);
      saved[a] = { src: src, out: out };
    });
    attrState.set(el, saved);
  }

  function run() {
    if (observer) observer.disconnect();
    blocks(document.body, []).forEach(translateBlock);
    withAttrs(document.body).forEach(translateAttrs);
    document.title = lang === 'en' ? originalTitle : (dict[originalTitle] || originalTitle);
    if (observer) { observer.takeRecords(); watch(); }
  }

  var pending = false;
  function watch() {
    if (!observer) {
      observer = new MutationObserver(function () {
        if (pending) return;
        pending = true;
        (window.requestAnimationFrame || setTimeout)(function () { pending = false; run(); });
      });
    }
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  function load(code) {
    if (cache[code]) return Promise.resolve(cache[code]);
    return fetch(new URL(code + '.json', scriptSrc)).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }).then(function (d) { cache[code] = d; return d; });
  }

  function fonts(code) {
    if (code !== 'bn' || document.getElementById('font-bn')) return;
    var l = document.createElement('link');
    l.id = 'font-bn'; l.rel = 'stylesheet';
    l.href = 'https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;500;600;700;800&display=swap';
    document.head.appendChild(l);
  }

  function set(code) {
    if (CODES.indexOf(code) < 0) code = 'en';
    return load(code).then(function (d) {
      lang = code; dict = d;
      document.documentElement.lang = code === 'zh' ? 'zh-Hans' : code === 'tl' ? 'fil' : code;
      fonts(code);
      try { localStorage.setItem('rb-lang', code); } catch (e) { /* private mode: choice is not kept */ }
      var s = document.getElementById('langSel');
      if (s) s.value = code;
      run();
    }).catch(function (e) { if (window.console) console.warn('language', code, e); if (code !== 'en') set('en'); });
  }

  function initial() {
    var q = new URLSearchParams(location.search).get('lang');
    if (q && CODES.indexOf(q) >= 0) return q;
    try { var saved = localStorage.getItem('rb-lang'); if (saved && CODES.indexOf(saved) >= 0) return saved; } catch (e) { /* none */ }
    var nav = (navigator.languages || [navigator.language || 'en']);
    for (var i = 0; i < nav.length; i++) {
      var c = String(nav[i]).toLowerCase().split('-')[0];
      if (c === 'fil') c = 'tl';
      if (c === 'en') return 'en';
      if (CODES.indexOf(c) >= 0) return c;
    }
    return 'en';
  }

  var scriptSrc = document.currentScript ? document.currentScript.src : location.href;

  function picker() {
    var s = document.getElementById('langSel');
    if (!s) return;
    s.innerHTML = LANGS.map(function (l) {
      return '<option value="' + l[0] + '" lang="' + l[0] + '">' + l[1] + '</option>';
    }).join('');
    s.value = lang;
    s.addEventListener('change', function () {
      set(s.value);
      var u = new URL(location.href);
      if (u.searchParams.has('lang')) { u.searchParams.set('lang', s.value); history.replaceState(null, '', u); }
    });
  }

  window.rbI18n = {
    languages: LANGS,
    set: set,
    // for i18n/check.py: every English block and attribute on the page as it is now
    keys: function () {
      var k = blocks(document.body, []).map(function (el) { return { k: norm(el.innerHTML), time: el.tagName === 'TIME' }; });
      withAttrs(document.body).forEach(function (el) {
        ATTRS.forEach(function (a) { if (el.hasAttribute(a)) k.push({ k: el.getAttribute(a), time: false }); });
      });
      k.push({ k: originalTitle, time: false });
      return k;
    }
  };

  picker();
  var first = initial();
  if (first !== 'en') set(first);
  watch();
}());
