# 参与贡献

[English](CONTRIBUTING.md) · [日本語](CONTRIBUTING.ja.md)

每次提交一个真实且实用的资源，优先金融投资、研究、内容社交、视频及相关技能与指南。
可以使用 Issue 表单或提交 PR，附上来源与收录理由。

1. 分享链接放在 `data/bots.yaml`；技能、插件、MCP 放在 `data/skills.yaml`；指南放在 `data/guides.yaml`。
2. 从来源复制真实 URL、作者与账号，不猜测个人身份。未知账号可为 null，语言未知时用 `[und]`。
3. 遵循 `schema/entry.schema.json`：唯一 ID/URL、主分类、1–6 个标签，以及英、中、日三种单行短评（各不超过 220 字符）。
4. 保留 `source.repo` 与元数据许可。CC-BY-4.0 还需 `source.attribution`、`source.changes`，详见 [LICENSE-DATA](LICENSE-DATA)。
5. 用浏览器 User-Agent 发起跟随重定向的 HTTP GET，仅接收 <400。日期使用带引号的 ISO 格式，设为 `status: active`、`tier: listed`。
6. 执行下列检查，并一同提交生成文件。

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

链接可访问不代表经过测试。「已测试」需要维护者记录任务、配置、日期、实际结果与限制；「精选」还需推荐理由。
记录可以放在 PR 或 `docs/reviews/<id>.md`。精选作者徽章仅在完成精选评审后授予。

`data/picks.yaml` 用 `{week: "YYYY-MM-DD", entries: [id]}` 引用条目。日期必须是周一，每周 1–6 个不重复的活跃 ID。
精选不会自动改变等级。下架时会清除相关引用；清空的周记录一并移除。

链接检查默认只读。`--write` 仅将 404/410 移入 `data/retired.yaml`。403、429、服务器错误、网络错误均不会导致下架。
阻止或错误比例超过 25% 时整次中止，任何文件都不写入。退出码为 0（正常或已应用）、1（只读发现失效）、2（熔断）。
未熔断时仍有错误的条目保留原检查日期。`--dry-run` 即使带 `--report` 也不会写文件。

网站源文件在 `web/`；`site/`、`dist/`、README 与 llms.txt 都由脚本生成。新增语言只需添加键结构相同的 `i18n/<locale>.yaml`。
缺失条目翻译回退英语。部署前替换 OWNER 占位符，启用 GitHub Actions Pages，确认默认分支及每日工作流写入权限。
可选 Playwright 预览与部署细节见[英文指南](CONTRIBUTING.md)。请遵守[行为准则](CODE_OF_CONDUCT.md)。
