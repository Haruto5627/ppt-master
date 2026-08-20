---
name: word-rewrite
description: >
  Rewrite a long Word document into human-readable Markdown. Use when the user
  asks to 精简设计文档, 改写 Word, or turn a .docx into readable md with
  LaTeX formulas, merged tables, and captions. Pandoc extracts docx→md;
  stdlib scripts extract images/captions and merged-table HTML for rewriting.
  Deliver {slug}.md only. Do not export HTML. Do not use MarkItDown for
  formulas. Do not replace ppt-master source intake (`source_to_md.py`).
---

# Word 改写

把过长的 Word 改写成给人看的 Markdown。不回写原文件。定位和文件名按正文确定。

**触发**：精简设计文档、改写 Word、把 `.docx` 写成可读 md。  
**范围外**：导出 HTML（用户自己做）；只提取、不改写（走 [`document-extract`](../document-extract/SKILL.md)）；改回 Word；做 PPT（走 [`ppt-master`](../ppt-master/SKILL.md)）。

**交付**：`{slug}.md`。不要写 `{slug}.html`。

---

## 1. 提取原料（不给读者看）

需要 **Pandoc** 和 **Python**（标准库即可）。**Hard rule**：命令一律写 `python`，禁止写 `python3`（本机 `python3` 会失败）。不要用 MarkItDown 抽公式。老格式 `.doc` 先另存为 `.docx`。

脚本和 Word 放在同一台机器即可，不必在 ppt-master 仓库里。在 Word 所在目录：

```bash
pandoc "设计文档.docx" -t markdown -o "_extracted.md"
python extract_office_images.py "设计文档.docx"
python docx_to_html.py "设计文档.docx" --check
```

`--check` 若打印 `html`，再跑：

```bash
python docx_to_html.py "设计文档.docx"
```

| 文件 | 用途 |
|---|---|
| `_extracted.md` | 叙事 + **LaTeX 公式**（Pandoc 从 OMML 转出）。表可以丑 |
| `images/` | 该目录只有一个 Word：插图直接放这里 |
| `images/<Word主文件名>/` | 该目录有多个 Word：每个文件一个子目录 |
| 题注 JSON | 单文件：`images/<stem>.captions.json`；多文件：`images/<stem>/captions.json` |
| `设计文档.body.html` | 仅当有合并格：看清 `colspan`/`rowspan`，不是交付物 |

抽图行为：无图则不建空文件夹；不改 Word 原件。题注 JSON 含文档顺序和供 md 使用的 `path`。

---

## 2. 按正文定名，再重写成 `{slug}.md`

读完 `_extracted.md` 后，根据正文确定定位和文件名，再重写。不要覆盖 Word。

| 项 | 规则 |
|---|---|
| 定位 | 按内容判断：教程、操作说明、设计说明、纪要、指南等。用户指定了定位就用用户的 |
| 文件名 | `{slug}.md`。slug 取标题或主题，中文或 ASCII 均可 |
| 用户指定了文件名 | 用用户的，不要另起一套 |
| **禁止** | 不管正文一律写成 `教材.md`；不要写 `{slug}.html` |

重写目标：**缩短、拆步骤、改说法**，让人能读；不是 Word 保真排版。

| 元素 | 重写规则 |
|---|---|
| 正文 | 精简，保留必要术语 |
| 公式 | 必须仍是 `$...$` / `$$...$$`，禁止改成纯文字或截图（除非用户明确不要公式） |
| 无合并的表 | Markdown 管道表 |
| **有合并的表** | **只写 HTML `<table>`**（`colspan`/`rowspan`），禁止写成 `\| a \| b \|` |
| **图** | 必须写入 `{slug}.md`（路径相对该 md）；**每张图下方必须有非空题注** |

**图的写法**（二选一；图在上、题注在下）。路径以题注 JSON 的 `path` 为准（相对 Word 所在目录）：

```markdown
![图 1 登录页](images/image1.png)
![图 1 登录页](images/设计文档/image1.png)
```

前一例用于目录里只有一个 Word；后一例用于多个 Word（子目录名等于该 Word 主文件名）。

或：

```html
<figure>
  <img src="images/设计文档/image1.png" alt="图 1 登录页" />
  <figcaption>图 1 登录页</figcaption>
</figure>
```

**Hard rule**：禁止空题注 `![](images/...)`。读对应 captions JSON：`caption` 非空则采用（可略改通顺，保留原编号）；为空则根据该图前后文补一句短题注。`path` 写进 md，不要把多份 Word 的图平铺到 `images/` 根下。装饰性页眉 logo 与理解无关则可不用；正文插图不要丢。

合并表示例：

```html
<table>
  <tr>
    <th rowspan="2">模块</th>
    <th colspan="2">步骤</th>
  </tr>
  <tr><th>序号</th><th>说明</th></tr>
  <tr>
    <td rowspan="2">登录</td>
    <td>1</td><td>输入账号</td>
  </tr>
  <tr><td>2</td><td>校验密码</td></tr>
</table>
```

MD 预览里管道表对合并格会乱是正常的；以 `<table>` 源码为准。不要为了预览把合并格填开（除非改写上确实该拆成两张表）。不要把 `.body.html` 当成交付物。

---

## 3. 交付

交付 `{slug}.md` 即停。不要导出 HTML，不要 Word 直出 HTML。
