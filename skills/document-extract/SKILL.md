---
name: document-extract
description: >
  Extract-only conversion of Word (.docx), PowerPoint (.pptx), Excel (.xlsx/.xlsm),
  and PDF into Markdown. Use when the user asks to read, extract, convert, 提取,
  读取, or 转换 Office/PDF files for an agent to consume. Default to MarkItDown;
  use Docling for scanned PDFs, two-column papers, complex tables, or garbled
  MarkItDown output. Do not use for editing documents, and do not replace
  ppt-master source intake (`source_to_md.py`) during PPT generation.
---

# 文档提取

只把 Word / PPT / Excel / PDF **提取成 Markdown**，供 agent 阅读。不编辑、不回写原文件。

**触发**：用户要求读取、提取、转 Markdown、或让 agent 消化这些格式的内容。  
**范围外**：改 Word/PPT/Excel、美化 PPT、生成新稿。那些任务走别的 skill；PPT 生成走 [`ppt-master/SKILL.md`](../ppt-master/SKILL.md)。

---

## 1. 先分流，再动手

| 当前任务 | 用什么 |
|---|---|
| 只要提取内容，给 agent 读 | 本 skill：在 MarkItDown / Docling 里选一个 |
| ppt-master 生成 / 填模板 / 美化 / 增强 | **禁止**用本 skill 替代摄入。走 `python skills/ppt-master/scripts/source_to_md.py` |
| 要改原文件、写回、精细排版 | 停。本 skill 不负责编辑 |

**硬性规则**：同一文件默认只跑一种工具。先 MarkItDown；只有输出不合格时，才对该文件改跑 Docling。

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

## 5. 执行约定

1. **先确认解释器**：`python` / `python -m pip` 必须是装过 `markitdown` 和 `docling` 的那一套。Cursor 工作区解释器不一致时先对齐，再转换。
2. **输出位置**：用户指定了目录就用指定目录；否则写到源文件旁边，扩展名改为 `.md`。不要覆盖源文件。
3. **一次一种工具**：对每个文件在日志里写清用了 MarkItDown 还是 Docling。
4. **只提取**：禁止用这些库（或 Office 自动化）写回 `.docx` / `.pptx` / `.xlsx` / `.pdf`。
5. **Excel 要按单元格算数**：不要指望 Markdown。说明本 skill 只提取展示用文本；需要单元格级数据时改用 `pandas` / `openpyxl` 读表，而不是改跑 Docling。

---

## 6. 禁止

- 为「以防万一」对每个文件同时跑 MarkItDown 和 Docling
- 用本 skill 替代 ppt-master 的 `source_to_md.py`
- 把提取结果当成已编辑的正式稿写回原格式
- 因为 CLI 不在 PATH 就报告「没装好」——先试 `python -m markitdown` / `python -m docling`
