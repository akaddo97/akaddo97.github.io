#!/usr/bin/env python3
"""The canonical domain lives in domain.txt and nowhere else.

Same idea as apply_links.py, for the one thing that file does not cover: the
absolute URLs. Change domain.txt, run this, and the og:url and og:image tags on
every page, sitemap.xml, robots.txt, and the CNAME file all follow.

    python3 apply_domain.py            dry run, the default
    python3 apply_domain.py --commit   writes
    python3 apply_domain.py --check    exits 1 if the site and domain.txt disagree

A github.io domain writes no CNAME, because GitHub Pages only wants that file
when the site is served from a custom domain. Switching to one writes it, and
switching back removes it.

/cv/ is deliberately absent from sitemap.xml: it carries noindex, and listing a
page you have asked search engines not to index is a contradiction.
"""
import os, re, sys, subprocess, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DOMAIN_FILE = os.path.join(ROOT, 'domain.txt')

# path on the site -> file that serves it. Indexable pages only.
SITEMAP_PAGES = [('/', 'index.html'), ('/build/', 'build/index.html'),
                 ('/learn/', 'learn/index.html'), ('/pricing/', 'pricing/index.html')]
# every page carrying absolute og tags, including the noindex ones
OG_PAGES = SITEMAP_PAGES + [('/cv/', 'cv/index.html')]

changes = []


def read_domain():
    with open(DOMAIN_FILE) as f:
        for line in f:
            line = line.split('#')[0].strip()
            if line:
                return line.rstrip('/')
    raise SystemExit('domain.txt has no domain in it')


def last_modified(rel):
    """Git's last commit date for a file, so lastmod is a fact rather than today."""
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', rel],
                             cwd=ROOT, capture_output=True, text=True, timeout=10)
        d = out.stdout.strip()
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', d):
            return d
    except Exception:
        pass
    return datetime.date.today().isoformat()


def plan_file(rel, new_text):
    path = os.path.join(ROOT, rel)
    old = open(path).read() if os.path.exists(path) else None
    if old != new_text:
        changes.append((rel, 'create' if old is None else 'update', new_text))


def build(domain):
    base = 'https://' + domain

    # 1. og:url and og:image on every page
    for url_path, rel in OG_PAGES:
        path = os.path.join(ROOT, rel)
        s = open(path).read()
        s2 = re.sub(r'(<meta property="og:url" content=")[^"]*(")',
                    lambda m: m.group(1) + base + url_path + m.group(2), s)
        s2 = re.sub(r'(<meta property="og:image" content=")[^"]*(")',
                    lambda m: m.group(1) + base + '/ak-addo.jpg' + m.group(2), s2)
        if s2 != s:
            changes.append((rel, 'update', s2))

    # 2. sitemap.xml
    urls = ''.join(
        f'  <url>\n    <loc>{base}{u}</loc>\n'
        f'    <lastmod>{last_modified(rel)}</lastmod>\n  </url>\n'
        for u, rel in SITEMAP_PAGES)
    plan_file('sitemap.xml',
              '<?xml version="1.0" encoding="UTF-8"?>\n'
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
              + urls + '</urlset>\n')

    # 3. robots.txt
    plan_file('robots.txt',
              '# Everything here is public and may be crawled.\n'
              '# /cv/ is kept out of results by a noindex tag on the page itself,\n'
              '# which is the right tool: a path disallowed here can still be listed\n'
              '# as a bare URL if another site links to it.\n'
              'User-agent: *\n'
              'Allow: /\n\n'
              f'Sitemap: {base}/sitemap.xml\n')

    # 4. CNAME, only for a custom domain
    cname = os.path.join(ROOT, 'CNAME')
    if domain.endswith('.github.io'):
        if os.path.exists(cname):
            changes.append(('CNAME', 'delete', None))
    else:
        plan_file('CNAME', domain + '\n')


def main():
    mode = 'dry'
    if '--commit' in sys.argv:
        mode = 'commit'
    elif '--check' in sys.argv:
        mode = 'check'

    domain = read_domain()
    build(domain)
    print(f'domain.txt: {domain}')

    if not changes:
        print('check: everything already matches')
        return 0

    for rel, action, _ in changes:
        print(f'  {action:6} {rel}')

    if mode == 'check':
        print(f'check: {len(changes)} file(s) out of sync with domain.txt')
        return 1
    if mode == 'dry':
        print(f'dry run: {len(changes)} file(s) would change. Re-run with --commit.')
        return 0

    for rel, action, text in changes:
        path = os.path.join(ROOT, rel)
        if action == 'delete':
            os.remove(path)
        else:
            with open(path, 'w') as f:
                f.write(text)
    print(f'wrote {len(changes)} file(s)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
