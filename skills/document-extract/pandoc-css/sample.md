---
title: 季度进展备忘
subtitle: 产品与工程联席纪要
author: 文档提取预览
date: 2026-08-19
lang: zh-CN
---

# 背景

本页用来核对 Pandoc 默认 HTML 在各套 CSS 下的观感：标题块、目录、正文、引用、表格、代码与脚注。正文混排 **加粗**、*斜体* 与 `inline code`，并保留 [链接](https://github.com/sindresorhus/github-markdown-css)。

## 关键结论

- 默认文本提取走 MarkItDown，扫描件与复杂表再升级 Docling。
- Word / PPT 图片落到源文件同级 `images/`，不回写原件。
- HTML 分发时用 `--embed-resources`，避免 CSS 路径丢失。

1. 先确认 Python 解释器与包装在同一环境。
2. 再选主题导出 HTML。

> 版式目标是「打开即读」，而不是复刻 Office 分页。引用块应一眼能从正文里分开。

## 对照表

| 主题 | 场景 | 强调 |
|---|---|---|
| GitHub | 技术说明 | 边框与代码底 |
| Tufte | 讲义随笔 | 衬线与留白 |
| 宋体报告 | 中文纪要 | 标题黑体、正文衬线 |

### 代码

```python
from pathlib import Path

def export_html(md: Path, css: Path) -> Path:
    out = md.with_suffix(".html")
    print(f"pandoc {md.name} --css {css.name} -o {out.name}")
    return out
```

细节见脚注。[^1]

[^1]: 预览文稿仅用于核对样式，不代表真实业务数据。
