# 貢献ガイド

[English](CONTRIBUTING.md) · [简体中文](CONTRIBUTING.zh-CN.md)

実在する有用なリソースを一件ずつ提案してください。金融・投資、調査、コンテンツ・SNS、動画と関連スキル・ガイドを重視します。
IssueフォームまたはPRに、出典と掲載する理由を添えてください。

1. 共有URLは `data/bots.yaml`、スキル・プラグイン・MCPは `data/skills.yaml`、ガイドは `data/guides.yaml` に追加。
2. URL、作者、アカウントを出典から写し、個人の身元を推測しないでください。不明なハンドルはnull、言語は `[und]` にします。
3. `schema/entry.schema.json` に従い、重複しないID/URL、主分類、1–6個のタグ、英語・中国語・日本語の一行レビュー（各220文字以内）を記載。
4. `source.repo` とメタデータのライセンスを保持。CC-BY-4.0には `source.attribution` と `source.changes` も必要です。[LICENSE-DATA](LICENSE-DATA)を参照。
5. ブラウザーのUser-Agentでリダイレクトを追うHTTP GETを実行し、<400だけを追加。日付は引用符付きISO形式で、`status: active`、`tier: listed` にします。
6. 以下を実行し、生成されたファイルもコミットしてください。

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/validate.py
python scripts/build.py
python scripts/build.py --check
python scripts/check_links.py --dry-run
python -m unittest discover -s tests
python -m http.server 8000 --directory site
```

リンクの応答だけではテスト済みになりません。テスト済みにはタスク、設定、日付、観測した結果、制約を管理者がPRまたは
`docs/reviews/<id>.md` に記録します。厳選には推薦理由も必要です。作者バッジは厳選レビュー後に授与します。

`data/picks.yaml` は `{week: "YYYY-MM-DD", entries: [id]}` 形式。月曜日の日付と1–6個の重複しない有効IDを指定します。
ピックアップは評価段階を自動変更しません。掲載終了時には参照を除去し、空になった週も除きます。

リンク確認は既定で読み取りのみ。`--write` は404/410だけを `data/retired.yaml` に移します。403、429、サーバー・通信エラーは削除の理由にしません。
ブロック・エラーが25%を超えると全体を中止し、レポートも含め一切書き込みません。終了コードは0（正常・適用済み）、1（ドライランで無効リンク）、2（遮断）。
遮断未満でもエラー項目の確認日は保持されます。`--dry-run` は `--report` があっても書き込みません。

サイトを変更する場合は `web/` を編集。`site/`、`dist/`、README、llms.txtは生成物です。同じキー構成の `i18n/<locale>.yaml` 一つでUI言語を追加できます。
項目の翻訳がなければ英語を表示します。公開前にOWNERを置換し、GitHub Actions Pages、既定ブランチ、日次ワークフローの書き込み権限を設定してください。
任意のPlaywrightプレビューと公開設定は[英語版](CONTRIBUTING.md)を参照。[行動規範](CODE_OF_CONDUCT.md)を守ってください。
