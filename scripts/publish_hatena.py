#!/usr/bin/env python3
"""essays/*.md のうち未公開のものを、はてなブログ(AtomPub)に公開する。

環境変数: HATENA_ID, HATENA_BLOG_ID, HATENA_API_KEY
オプション: --dry-run  (送信せずXMLだけ表示)
"""
import base64, glob, html, os, random, re, sys, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLISHED = os.path.join(ROOT, "published.txt")


def load_published():
    if not os.path.exists(PUBLISHED):
        return set()
    with open(PUBLISHED, encoding="utf-8") as f:
        return {l.strip() for l in f if l.strip()}


def parse(path):
    text = open(path, encoding="utf-8").read().strip()
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError(f"{path}: 1行目が '# タイトル' ではありません")
    return lines[0][2:].strip(), "\n".join(lines[1:]).strip()


def to_html(body):
    """空行=段落、行末の改行=<br> に変換（表示の記法設定に依存しないようHTMLで送る）"""
    paras = [p for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
    out = []
    for para in paras:
        lines = [html.escape(l.strip()) for l in para.splitlines() if l.strip()]
        out.append("<p>" + "<br />\n".join(lines) + "</p>")
    return "\n\n".join(out)


BANNER = "[blog:g:6653812171403971647:banner]"  # 記事の末尾に自動で付けるバナー記法


def to_markdown(body):
    """本文はHTML(<p>/<br />)のまま、末尾にバナー記法を1段落で付ける（Markdownモードで両方が効く）"""
    return to_html(body) + "\n\n" + BANNER


JST = timezone(timedelta(hours=9))


def random_post_time():
    """実行日(日本時間)の 18:00:00〜19:59:59 からランダムに選んだ投稿時刻"""
    start = datetime.now(JST).replace(hour=18, minute=0, second=0, microsecond=0)
    return (start + timedelta(seconds=random.randrange(2 * 60 * 60))).isoformat()


def build_xml(title, body):
    posted = random_post_time()
    return f"""<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
  <title>{escape(title)}</title>
  <author><name>{escape(os.environ.get('HATENA_ID', ''))}</name></author>
  <content type="text/x-markdown">{escape(to_markdown(body))}</content>
  <updated>{posted}</updated>
  <app:control><app:draft>yes</app:draft></app:control>
</entry>
"""


def post(xml):
    hid, blog, key = (os.environ[k].strip() for k in ("HATENA_ID", "HATENA_BLOG_ID", "HATENA_API_KEY"))
    url = f"https://blog.hatena.ne.jp/{hid}/{blog}/atom/entry"
    token = base64.b64encode(f"{hid}:{key}".encode()).decode()
    req = urllib.request.Request(
        url, data=xml.encode("utf-8"), method="POST",
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/xml; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def main():
    dry = "--dry-run" in sys.argv
    done = load_published()
    todo = [p for p in sorted(glob.glob(os.path.join(ROOT, "essays", "*.md")))
            if os.path.basename(p) not in done]
    if not todo:
        print("公開するものはありません")
        return
    for p in todo:
        name = os.path.basename(p)
        title, body = parse(p)
        xml = build_xml(title, body)
        if dry:
            print(f"--- {name} ---\n{xml[:500]}...")
            continue
        try:
            status = post(xml)
        except urllib.error.HTTPError as e:
            print(f"失敗 {name}: HTTP {e.code}", file=sys.stderr)
            if e.code == 401:
                print("401: はてなID または AtomPub のAPIキー（設定→詳細設定→AtomPub）を確認してください", file=sys.stderr)
            elif e.code == 404:
                print("404: HATENA_BLOG_ID（例: otst.hatenablog.jp）を確認してください", file=sys.stderr)
            sys.exit(1)
        print(f"公開 {name}: HTTP {status} 「{title}」")
        with open(PUBLISHED, "a", encoding="utf-8") as f:
            f.write(name + "\n")


if __name__ == "__main__":
    main()
