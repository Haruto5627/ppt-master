# Pandoc CSS 主题

给 Pandoc 把 Markdown 转成 HTML 用。每份都是**独立 CSS 源文件**，不互相依赖。样式元素选择器对准 Pandoc 默认 HTML（`#title-block-header`、`nav#TOC`、`div.sourceCode`、脚注）。

## 怎么用

```bash
pandoc 报告.md -s --embed-resources --toc --css=github-doc.css -o 报告.html
```

| 文件 | 风格 | 参考的 GitHub 库 |
|---|---|---|
| `github-doc.css` | GitHub 文档 | [sindresorhus/github-markdown-css](https://github.com/sindresorhus/github-markdown-css) |
| `tufte-essay.css` | 学术随笔 / 讲义 | [edwardtufte/tufte-css](https://github.com/edwardtufte/tufte-css)、[jez/tufte-pandoc-css](https://github.com/jez/tufte-pandoc-css) |
| `sakura-warm.css` | 暖灰 + 青绿 | [oxalorg/sakura](https://github.com/oxalorg/sakura) |
| `pico-product.css` | 产品文档 | [picocss/pico](https://github.com/picocss/pico)、[kognise/water.css](https://github.com/kognise/water.css) |
| `nord-night.css` | 深色工程文档 | [nordtheme/nord](https://github.com/nordtheme/nord) |
| `songti-report.css` | 中文报告 / 公文 | CLReq 衬线正文习惯 |
| `swiss-plain.css` | 国际主义平面 | [xz/new.css](https://github.com/xz/new.css) |

`--embed-resources` 会把 CSS 打进 HTML，双击打开也有样式。不要 CSS 时去掉即可。

本地预览：打开 [`preview/index.html`](preview/index.html)，或直接打开 `preview/*.html`。截图与 HTML 由同一份 [`sample.md`](sample.md) 经 Pandoc 生成。

这些文件是按上述开源风格**重写**的 classless 主题，不是整份拷贝上游仓库。
