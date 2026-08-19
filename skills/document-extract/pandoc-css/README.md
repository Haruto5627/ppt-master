# Pandoc CSS 主题

给 Pandoc 把 Markdown 转成 HTML 用。每份都是**独立 CSS 源文件**。默认用 **清新卡片** 系列；旧的文档灰 / 深色风在 [`classic/`](classic/)。

## 怎么用

```bash
pandoc 报告.md -s --embed-resources --toc --css=fresh-mint.css -o 报告.html
```

| 文件 | 风格 | 参考 |
|---|---|---|
| `fresh-mint.css` | 薄荷绿（默认） | Tailwind emerald/teal 的高亮清新 |
| `fresh-sky.css` | 天空蓝 | Catppuccin Latte 的 sky |
| `fresh-peach.css` | 蜜桃粉 | 日系浅珊瑚 |
| `fresh-lilac.css` | 丁香紫 | Catppuccin Latte lavender |
| `fresh-latte.css` | 奶茶色 | [catppuccin/catppuccin](https://github.com/catppuccin/catppuccin) Latte |

`--embed-resources` 会把 CSS 打进 HTML。本地预览打开 [`preview/index.html`](preview/index.html)。

改配色：编辑 [`_emit_fresh.py`](_emit_fresh.py) 后运行 `python3 _emit_fresh.py`。
