# hatena-publisher
`essays/*.md`（1行目が `# タイトル`）を push すると、GitHub Actions がはてなブログに公開します。
公開済みは `published.txt` に記録され、二重投稿されません。

## 必要なSecrets（Settings → Secrets and variables → Actions）
- HATENA_ID = otst
- HATENA_BLOG_ID = otst.hatenablog.jp
- HATENA_API_KEY = （はてなブログ 設定→詳細設定→AtomPub のAPIキー）
