---
name: document-extract
description: >
  Extract Word/PPT/Excel/PDF into Markdown for an agent to read. Use when the
  user asks to 提取, 读取, or 转换 Office/PDF text or images. MarkItDown by
  default; Docling for scanned or layout-heavy PDFs; dump Word/PPT images into
  a sibling images/ folder. Do not rewrite long Word into a human-facing draft
  (use word-rewrite). Do not export HTML. Do not replace ppt-master source
  intake (`source_to_md.py`) during PPT generation.
---

# 文档提取

从 Office / PDF **提取**原料，给 agent 读。不回写原文件。

**触发**：提取、转 Markdown、提取图片。  
**范围外**：把长 Word 改写成给人看的稿（走 [`word-rewrite`](../word-rewrite/SKILL.md)）；导出 HTML；改回 Word/PPT/Excel；美化 PPT。PPT 生成走 [`ppt-master/SKILL.md`](../ppt-master/SKILL.md)。

---

## 1. 先分流，再动手

| 当前任务 | 用什么 |
|---|---|
| 长 Word → 按正文精简改写成给人看的 Markdown | **停。走 [`word-rewrite`](../word-rewrite/SKILL.md)** |
| 只要提取内容，给 agent 读 | MarkItDown 或 Docling；Word / PPT 再抽图片 |
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

命令（一律 `python`，不要用 `python3`）：

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

stdout 每行一个写出的图片路径。调用一律用 `python`，不要用 `python3`。

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
- 用本 skill 改写长 Word 给人看（走 `word-rewrite`）
- 用本 skill 替代 ppt-master 的 `source_to_md.py`
- 把提取结果当成已编辑的正式稿写回原格式
- 因为 CLI 不在 PATH 就报告「没装好」——先试 `python -m markitdown` / `python -m docling`
- 把 Word / PPT 图片写到当前工作目录、Markdown 旁的 `_files/`，或任何不是源文件同级 `images/` 的地方
- 导出 HTML（用户自己做）
