#!/usr/bin/env python3
"""Build inline HTML forms from published Google Forms, and write them into a page.

Same idea as cv_form_wire.py, generalised: read the form itself rather than
transcribing entry ids and options by hand. Options are copied verbatim, because
a value Google does not recognise is recorded as nothing at all, silently.

    python3 form_inline.py                # show what it found in each form
    python3 form_inline.py --write        # write the forms into learn/index.html
    python3 form_inline.py --check        # exit 1 if the page and the forms disagree

Stdlib only.
"""
import argparse
import html as H
import json
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
# each form now lives on its own page, reached from a button on /learn/
PAGES = {"cohort": ROOT / "learn/apply/index.html",
         "mentor": ROOT / "learn/mentor/index.html"}

TYPES = {0: "short", 1: "paragraph", 2: "radio", 3: "dropdown", 4: "checkbox"}

FORMS = {
    "cohort": {
        "url": "https://docs.google.com/forms/d/e/1FAIpQLSetZTijhq0l2xNujow4Qc9kulguoO5PSRlpVX6grZopnp9rPg/viewform",
        "slug": "coh",
        "heading": "Apply for a cohort place",
        "done": "Thanks. Your application is in, and AK will come back to you.",
    },
    "mentor": {
        "url": "https://docs.google.com/forms/d/e/1FAIpQLSfeyJ-DlHsev53d_D5zJn8BsQVzzivL76RB6qDZ4QY80pbf8w/viewform",
        "slug": "men",
        "heading": "Be a mentor",
        "done": "Thanks for volunteering. AK will be in touch about matching you with a mentee.",
    },
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse(url):
    """(endpoint, [question]) read out of the form's own published data."""
    page = fetch(url)
    m = re.search(r"FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);\s*</script>", page, re.S)
    if not m:
        sys.exit(f"no form data at {url}; is it the public /viewform link?")
    data = json.loads(m.group(1))
    out = []
    for item in (data[1][1] or []):
        kind = TYPES.get(item[3] if len(item) > 3 else None)
        title = (item[1] or "").strip()
        for e in (item[4] or []):
            if e and e[0]:
                out.append({
                    "entry": f"entry.{e[0]}",
                    "title": title,
                    "kind": kind or "short",
                    "options": [o[0] for o in (e[1] or []) if o and o[0]],
                    "required": bool(e[2]) if len(e) > 2 else False,
                })
    endpoint = url.replace("/viewform", "/formResponse")
    return endpoint, out


def field_html(q, slug, i):
    fid = f"{slug}{i}"
    label = H.escape(q["title"])
    req = " required" if q["required"] else ""
    star = "" if q["required"] else ' <span class="opt">optional</span>'
    if q["kind"] in ("radio", "checkbox"):
        tag = "radio" if q["kind"] == "radio" else "checkbox"
        boxes = "\n".join(
            f'          <label class="opt-row"><input type="{tag}" name="{q["entry"]}" '
            f'value="{H.escape(o, quote=True)}"><span>{H.escape(o)}</span></label>'
            for o in q["options"])
        return (f'        <fieldset class="field" data-entry="{q["entry"]}" '
                f'data-kind="{q["kind"]}"{req}>\n'
                f'          <legend>{label}{star}</legend>\n{boxes}\n        </fieldset>')
    if q["kind"] == "paragraph":
        return (f'        <div class="field"><label for="{fid}">{label}{star}</label>'
                f'<textarea id="{fid}" name="{q["entry"]}" rows="3"{req}></textarea></div>')
    return (f'        <div class="field"><label for="{fid}">{label}{star}</label>'
            f'<input id="{fid}" name="{fid}" data-entry="{q["entry"]}" type="text"{req}></div>')


def build(name, cfg):
    endpoint, qs = parse(cfg["url"])
    slug = cfg["slug"]
    fields = "\n".join(field_html(q, slug, i) for i, q in enumerate(qs))
    return endpoint, qs, f"""      <form class="gform" id="{slug}Form" data-endpoint="{endpoint}" novalidate>
{fields}
        <button class="btn btn-dark" type="submit">Send</button>
        <p class="err" id="{slug}Err" hidden></p>
      </form>
      <p class="gdone" id="{slug}Done" hidden>{H.escape(cfg["done"])}</p>"""


SCRIPT = """<script>
/* The two forms post straight into their Google Forms, so nobody leaves the site.
   Same shape as the CV page: a no-cors POST, which Google accepts but whose reply
   the browser will not let us read. That means a failed write is invisible, so the
   fallback link under each form stays, and it opens the real form. */
(function(){
  var forms=document.querySelectorAll('.gform');
  Array.prototype.forEach.call(forms,function(f){
    var err=document.getElementById(f.id.replace('Form','Err'));
    var done=document.getElementById(f.id.replace('Form','Done'));
    f.addEventListener('submit',function(ev){
      ev.preventDefault();
      var body=new URLSearchParams(), missing=[];
      Array.prototype.forEach.call(f.querySelectorAll('.field'),function(field){
        var entry=field.getAttribute('data-entry'), kind=field.getAttribute('data-kind');
        var control0=field.querySelector('input[type=text],textarea');
        var need=field.hasAttribute('required')||(control0!==null&&control0.hasAttribute('required'));
        if(kind==='radio'||kind==='checkbox'){
          var picked=field.querySelectorAll('input:checked');
          if(need&&picked.length===0){missing.push(field);return;}
          Array.prototype.forEach.call(picked,function(p){body.append(entry,p.value);});
        }else{
          var control=field.querySelector('input,textarea');
          var entry2=control.getAttribute('data-entry')||control.getAttribute('name');
          var val=(control.value||'').trim();
          if(need&&val===''){missing.push(field);return;}
          if(val!==''){body.append(entry2,val);}
        }
      });
      if(missing.length>0){
        err.textContent='Please fill in every question marked as needed.';
        err.hidden=false;
        missing[0].scrollIntoView({block:'center'});
        return;
      }
      err.hidden=true;
      var btn=f.querySelector('button');
      btn.disabled=true; btn.textContent='Sending';
      try{
        fetch(f.getAttribute('data-endpoint'),{method:'POST',mode:'no-cors',body:body});
      }catch(e){}
      f.hidden=true; done.hidden=false;
      done.scrollIntoView({block:'center'});
    });
  });
})();
</script>"""

CSS = """
  /* Inline application forms, so nobody is routed off the site. */
  .gform{max-width:560px;margin:18px 0 0;}
  .gform .field{margin:0 0 18px;border:0;padding:0;}
  .gform label,.gform legend{display:block;font-size:14px;color:var(--ink);margin:0 0 8px;padding:0;}
  .gform .opt{color:var(--muted);font-size:12px;}
  .gform input[type=text],.gform textarea{width:100%;font:inherit;font-size:15px;
    padding:12px 14px;border:1px solid var(--rule);border-radius:11px;background:#fff;
    color:var(--ink);}
  .gform textarea{resize:vertical;}
  .gform input:focus,.gform textarea:focus{outline:2px solid var(--accent);outline-offset:1px;
    border-color:var(--ink);}
  /* 44px rows: the same tap-target standard the nav uses. The label wraps the
     input, so the whole row is the target, not just the box. */
  .gform .opt-row{display:flex;gap:12px;align-items:center;font-size:14px;color:var(--muted);
    margin:0 0 2px;cursor:pointer;min-height:44px;padding:4px 0;}
  .gform .opt-row input{flex:none;width:18px;height:18px;accent-color:var(--accent);}
  .gform .opt-row:hover{color:var(--ink);}
  .gform button[disabled]{opacity:.55;cursor:default;}
  .err{color:#B00020;font-size:14px;margin:12px 0 0;}
  .gdone{border:1px solid var(--rule);border-radius:18px;background:var(--panel);
    padding:20px 22px;margin:18px 0 0;color:var(--ink);max-width:560px;}
  .fallback{font-size:13px;color:var(--muted);margin:14px 0 0;}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    built = {}
    for name, cfg in FORMS.items():
        endpoint, qs, markup = build(name, cfg)
        built[name] = (endpoint, qs, markup)
        print(f"{name}: {len(qs)} questions -> {endpoint[:76]}")
        for q in qs:
            print(f"  {q['entry']:22} {q['kind']:10} req={q['required']}  {q['title'][:50]}")

    if a.check:
        bad = []
        for n, (ep, qs, _) in built.items():
            page = PAGES[n].read_text()
            if ep not in page or any(q["entry"] not in page for q in qs):
                bad.append(n)
        if bad:
            print("check: page is out of sync with", ", ".join(bad))
            return 1
        print("check: every form page carries its endpoint and entry ids")
        return 0

    if a.write:
        print("\n--write is retired. The forms moved to their own pages on 2026-08-25,")
        print("so regenerating them means editing learn/apply/ and learn/mentor/ directly.")
        print("Use --check to catch drift after editing a question in Google Forms.")
        return 1
    print("\ndry run. Use --check to compare these against the two form pages.")
    return 0

    for name, cfg in FORMS.items():
        endpoint, qs, markup = built[name]
        slug = cfg["slug"]
        marker = "COHORT" if name == "cohort" else "MENTOR"
        # one of the blocks carries an inline style attribute, so match any
        # attributes on the div rather than assuming a bare class
        old = re.search(
            r'    <div class="ask"[^>]*>\s*\n      <h3>%s</h3>.*?\n    </div>'
            % re.escape(cfg["heading"]), page, re.S)
        assert old, f"could not find the {name} block"
        link = re.search(r'<!-- FORM:%s -->\s*\n\s*<a[^>]*href="([^"]*)"' % marker,
                         old.group(0)).group(1)
        style = ' style="margin-top:22px"' if 'style=' in old.group(0)[:60] else ''
        new = (f'    <div class="ask"{style}>\n      <h3>{cfg["heading"]}</h3>\n'
               f'{markup}\n'
               f'      <p class="fallback">Prefer the Google form?\n'
               f'      <!-- FORM:{marker} -->\n'
               f'      <a class="inline" href="{link}">Open it in a new tab</a>.</p>\n'
               f'    </div>')
        page = page[:old.start()] + new + page[old.end():]

    page = page.replace('  .ask{', CSS + '  .ask{', 1)
    page = page.replace('</body>', SCRIPT + '\n</body>', 1)
    PAGE.write_text(page)
    print("\nwrote both forms into learn/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
