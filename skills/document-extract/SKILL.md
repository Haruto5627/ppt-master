---
name: document-extract
description: >
  Extract Word/PPT/Excel/PDF; rewrite long Word into Markdown then Pandoc HTML.
  Use when the user asks to 提取, 读取, 转换, 精简设计文档, or turn Markdown
  into HTML. Word→HTML uses Pandoc docx→md for LaTeX, stdlib image+caption
  extract, HTML <table> for merged cells, then pandoc --mathjax --css.
  Output filenames follow the rewritten content. Do not convert Word straight
  to HTML as the deliverable. Do not replace ppt-master source intake
  (`source_to_md.py`) during PPT generation.
---

# 文档提取

从 Office / PDF **提取**原料；若用户要把过长的 Word 改写成给人看的材料，则 **提取 → 重写 Markdown → Pandoc HTML**。不回写原文件。成品定位（教程、说明、纪要、指南等）和文件名按正文确定，不固定叫「教材」。

**触发**：提取、转 Markdown、提取图片、精简设计文档、或导出 HTML。  
**范围外**：改回 Word/PPT/Excel、美化 PPT。PPT 生成走 [`ppt-master/SKILL.md`](../ppt-master/SKILL.md)。

---

## 0. Word → 重写稿 + HTML（完整路径）

**适用**：原稿是长 Word；Markdown 只给作者/agent 看；**成品是 HTML**；公式必须是 LaTeX；合并单元格要保留到 HTML；Word 插图要进 MD 和 HTML，图下要有题注。

**禁止**：Word 直出 HTML 当成品；用 MarkItDown 当公式主通道；把合并格拆掉只为了 MD 预览好看；一律把成品写成 `教材.md` / `教材.html`。

假设文件为 `设计文档.docx`，和脚本、CSS 放在同一台机器（不必在 ppt-master 仓库里）。Windows 若 `python3` 不可用，改用 `python`。

### 0.1 提取原料（不给读者看）

在 Word 所在目录：

```bash
pandoc "设计文档.docx" -t markdown -o "_extracted.md"
python extract_office_images.py "设计文档.docx"
python docx_to_html.py "设计文档.docx" --check
```

`--check` 若打印 `html`，再跑：

```bash
python docx_to_html.py "设计文档.docx"
```

得到：

| 文件 | 用途 |
|---|---|
| `_extracted.md` | 叙事 + **LaTeX 公式**（Pandoc 从 OMML 转出）。表可以丑 |
| `images/` | 该目录只有一个 Word：插图直接放这里 |
| `images/<Word主文件名>/` | 该目录有多个 Word：每个文件一个子目录 |
| 题注 JSON | 单文件：`images/<stem>.captions.json`；多文件：`images/<stem>/captions.json` |
| `设计文档.body.html` | 仅当有合并格：给重写看清 `colspan`/`rowspan`，不是成品 |

### 0.2 按正文定名，再重写成 `{slug}.md`

读完 `_extracted.md` 后，根据正文确定文稿定位和文件名，再重写。不要覆盖 Word。

| 项 | 规则 |
|---|---|
| 定位 | 按内容判断：教程、操作说明、设计说明、纪要、指南等。用户指定了定位就用用户的 |
| 文件名 | `{slug}.md` / `{slug}.html`。slug 取标题或主题，中文或 ASCII 均可 |
| 用户指定了文件名 | 用用户的，不要另起一套 |
| **禁止** | 不管正文一律写成 `教材.md` / `教材.html` |

重写目标：**缩短、拆步骤、改说法**，让人能读；不是 Word 保真排版。

| 元素 | 重写规则 |
|---|---|
| 正文 | 精简，保留必要术语 |
| 公式 | 必须仍是 `$...$` / `$$...$$`，禁止改成纯文字或截图（除非用户明确不要公式） |
| 无合并的表 | Markdown 管道表 |
| **有合并的表** | **只写 HTML `<table>`**（`colspan`/`rowspan`），禁止写成 `\| a \| b \|` |
| **图** | 必须写入 `{slug}.md`（路径相对该 md）；**每张图下方必须有非空题注** |

**图的写法**（二选一；图在上、题注在下）。路径以题注 JSON 的 `path` 为准（相对 Word 所在目录）：

单独成段的 Markdown（Pandoc 默认会变成 `<figure>` + `<figcaption>`）：

```markdown
![图 1 登录页](images/image1.png)
![图 1 登录页](images/设计文档/image1.png)
```

前一例用于目录里只有一个 Word；后一例用于多个 Word（子目录名等于该 Word 主文件名）。

或 HTML：

```html
<figure>
  <img src="images/设计文档/image1.png" alt="图 1 登录页" />
  <figcaption>图 1 登录页</figcaption>
</figure>
```

**Hard rule**：禁止空题注 `![](images/...)`。读对应 captions JSON：`caption` 非空则采用（可略改通顺，保留原编号）；为空则根据该图前后文补一句短题注。`path` 写进 md，不要自行把多份 Word 的图平铺到 `images/` 根下。装饰性页眉 logo 与理解无关则可不用；正文插图不要丢。

合并表示例（放进 `{slug}.md` 正文）：

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

作者自己看 `{slug}.md` 时，管道表预览合并格会坏是正常的；**以导出的 HTML 核对表和图注。**

### 0.3 导出成品 HTML

```bash
pandoc "{slug}.md" -s --embed-resources --toc --mathjax --css=fresh-mint.css -o "{slug}.html"
```

CSS 默认 `fresh-mint.css`（栏宽 64rem）。用户指定了 `fresh-sky` / `fresh-peach` / `fresh-lilac` / `fresh-latte` 则换文件。图片已被 `--embed-resources` 打进 HTML，题注随 `<figcaption>` 出现在图下。

**成品是 `{slug}.html`，不是 `_extracted.md`，也不是 `设计文档.body.html`。**

---

## 1. 先分流，再动手

| 当前任务 | 用什么 |
|---|---|
| 长 Word → 按正文精简改写并发布 HTML | **只走第 0 节完整路径** |
| 只要提取内容，给 agent 读（不发布 HTML） | MarkItDown 或 Docling；Word / PPT 再抽图片 |
| 只要 Word / PPT 里的图片 | 直接跑 `extract_office_images.py` |
| ppt-master 生成 / 填模板 / 美化 / 增强 | **禁止**用本 skill 替代摄入。走 `python skills/ppt-master/scripts/source_to_md.py` |
| 要改原文件、写回 | 停。本 skill 不负责编辑 |

**硬性规则**：同一文件默认只跑一种文本工具。先 MarkItDown；只有输出不合格时，才对该文件改跑 Docling。  
**硬性规则**：处理 `.docx` / `.pptx`（含 `.docm` / `.pptm`）时，必须再跑图片提取，输出到**该 Office 文件所在目录**下的 `images/`（多个 Word 时再分子目录），不是 Markdown 输出目录，也不是当前工作目录。

---

## 2. 什么时候用 MarkItDown（默认）

**用 MarkItDown**：

- `.docx` / `.pptx` / `.xlsx` / `.xlsm`
- 有文本层的普通 PDF（能选中、能复制文字）
- 只要标题、列表、表格变成 Markdown，结构大概对即可
- 要快、要省资源、要批量处理很多文件
- Excel 以「读成 Markdown 表」为目的

**不要用 MarkItDown 硬啃**：

- 扫描件 / 图片型 PDF（整页是图，几乎选不中字）
- 论文双栏、跨页大表、财报/合同里表格结构必须对
- 上一次 MarkItDown 结果已经乱了（见第 4 节）

命令（Windows 若 `python3` 不可用，改用 `python`）：

```bash
python -m markitdown "材料.pdf" -o "材料.md"
python -m markitdown "报告.docx" -o "报告.md"
python -m markitdown "幻灯片.pptx" -o "幻灯片.md"
python -m markitdown "表格.xlsx" -o "表格.md"
```

Python：

```python
from markitdown import MarkItDown
md = MarkItDown()
print(md.convert("报告.docx").text_content)
```

---

## 3. 什么时候用 Docling

**用 Docling**：

- 扫描件、拍照件、图片型 PDF，需要 OCR / 版面分析
- 学术论文（双栏、公式、图表混排）
- 复杂表格、表单、财报、合同，行列不能挤成一段
- MarkItDown 输出已判定不合格，需要提高保真度
- 用户明确要求更好的 PDF 结构 / 阅读顺序

**不要默认用 Docling**：

- 普通 Word / PPT / Excel（MarkItDown 更快、更够用）
- 只是想「快速看一眼」的文本 PDF
- 为了 Excel 公式或单元格精度（Docling 也不是表格计算引擎）

命令：

```bash
docling "论文.pdf"
```

若 `docling` 不在 PATH：

```bash
python -m docling "论文.pdf"
```

Python：

```python
from docling.document_converter import DocumentConverter
result = DocumentConverter().convert("论文.pdf")
print(result.document.export_to_markdown())
```

**说明**：Docling 首次运行可能下载模型，会更慢、更占磁盘。等它结束，不要当成死机立刻杀掉。

---

## 4. 判定 MarkItDown 失败后再升级

抽出的 Markdown 若出现下面任一情况，**只对失败文件**改跑 Docling：

- 几乎是空的，或大量 `[image]` / 空白页
- 双栏文字左右交错、阅读顺序乱
- 表格变成一坨字，行列对不上
- 扫描件只有噪点、没有正文

合格则停，不要再跑一遍 Docling。

---

## 5. Word / PPT 图片提取（必须）

MarkItDown / Docling **不会**把嵌入图存成独立文件。Word / PPT 抽完文本后，立刻跑：

```bash
python skills/document-extract/extract_office_images.py "报告.docx" "幻灯片.pptx"
python skills/document-extract/extract_office_images.py "./材料"
```

目录递归：

```bash
python skills/document-extract/extract_office_images.py "./材料" -r
```

行为：

| 项 | 约定 |
|---|---|
| 输出目录 | `<Office文件所在目录>/images/` |
| 仅一个 Word | 图直接进 `images/`；题注 `images/<stem>.captions.json` |
| 多个 Word 同目录 | 每个 Word 进 `images/<主文件名>/`；题注该子目录里的 `captions.json` |
| PPT / 单文件混放 | PPT 仍写在 `images/` 根下；与 Word 重名时加源文件名前缀 |
| 无图 | 不创建空文件夹，stderr 打印 `[SKIP]` |
| 不支持 | 老格式 `.doc` / `.ppt`（先另存为 `.docx` / `.pptx`） |
| 不做 | 不改 Office 原文件；不从 Excel / PDF 抽图（用户未要求时不要自行扩大） |

stdout 每行一个写出的图片路径。Windows 若 `python3` 不可用，改用 `python`。

---

## 6. 执行约定

1. **先确认解释器**：`python` / `python -m pip` 必须是装过 `markitdown` 和 `docling` 的那一套。图片脚本只需标准库，与是否装过这两个包无关。Cursor 工作区解释器不一致时先对齐，再转换。
2. **Markdown 输出位置**：用户指定了目录就用指定目录；否则写到源文件旁边，扩展名改为 `.md`。不要覆盖源文件。
3. **图片输出位置**：跟 Office 源文件走，写到同级 `images/`。同一目录有两个及以上 Word 时，每个 Word 再进 `images/<主文件名>/`。即使 Markdown 写到别处，图片仍不改地方。
4. **一次一种文本工具**：对每个文件在日志里写清用了 MarkItDown 还是 Docling；Word / PPT 另写清图片提取结果。
5. **只提取**：禁止用这些库（或 Office 自动化）写回 `.docx` / `.pptx` / `.xlsx` / `.pdf`。
6. **Excel 要按单元格算数**：不要指望 Markdown。说明本 skill 只提取展示用文本；需要单元格级数据时改用 `pandas` / `openpyxl` 读表，而不是改跑 Docling。

---

## 7. 禁止

- 为「以防万一」对每个文件同时跑 MarkItDown 和 Docling
- 用本 skill 替代 ppt-master 的 `source_to_md.py`
- 把提取结果当成已编辑的正式稿写回原格式
- 因为 CLI 不在 PATH 就报告「没装好」——先试 `python -m markitdown` / `python -m docling`
- 把 Word / PPT 图片写到当前工作目录、Markdown 旁的 `_files/`，或任何不是源文件同级 `images/` 的地方

---

## 8. Markdown → HTML（Pandoc CSS）

用户要把 `.md` 做成可分发 HTML 时，用 [`pandoc-css/`](pandoc-css/) 里的**独立 CSS 源文件**，不要再去网上拼一套。

```bash
pandoc "{slug}.md" -s --embed-resources --toc --mathjax --css=skills/document-extract/pandoc-css/fresh-mint.css -o "{slug}.html"
```

| CSS | 适用 |
|---|---|
| `fresh-mint.css` | 默认清新：薄荷绿卡片 |
| `fresh-sky.css` | 天空蓝 |
| `fresh-peach.css` | 蜜桃粉 |
| `fresh-lilac.css` | 丁香紫 |
| `fresh-latte.css` | Catppuccin Latte 奶茶 |

用户指定颜色则用对应文件；未指定时用 `fresh-mint.css`。含公式的重写稿必须加 `--mathjax`。旧主题在 [`pandoc-css/classic/`](pandoc-css/classic/)，仅在用户明确要「GitHub / 公文 / 深色」时再用。只交付 CSS / HTML，不要改回 Office 原件。

---

## 9. 合并单元格（重写稿写法）

管道表没有 `colspan`。有合并的表在 `{slug}.md` 里写成 HTML `<table>`（见第 0.2 节），Pandoc 会带进成品 HTML。

提取时可用 `docx_to_html.py` 看清原表合并结构。**不要**把 `设计文档.body.html` 直接当成品；**不要**为了 MD 预览把合并格填开（除非教学上确实该拆成两张表）。
