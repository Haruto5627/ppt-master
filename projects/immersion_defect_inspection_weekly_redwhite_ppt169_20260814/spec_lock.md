<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: zh-CN
- audience: 光刻、缺陷、良率和设备工程师，以及当值经理
- objective: 说明本周 D0 上升是 S02 水印而非漏检，并推动冻结 recipe、关闭残液路径
- core_message: W33 L28 D0 升至 0.42/cm²，捕获率稳定，4 个 killer lot 全部来自 S02，先做浸没头/台面与后淋洗
- consumption_mode: balanced

## mode
- mode: pyramid

## visual_style
- visual_style: custom
- visual_style_references: swiss-minimal, blueprint
- visual_style_behavior: 纯白工程图纸底；标题 #C00000；结构线与图纸标注 #87D9F5；完成用派生蓝 #3D9EC4；浅底 #E7F6FB；网格 #D4EEF6；风险与阻塞保持红系；正文 #222222。中文微软雅黑，英文 Times New Roman。

## colors
- background: #FFFFFF
- secondary_bg: #E7F6FB
- primary: #C00000
- accent: #87D9F5
- secondary_accent: #3D9EC4
- body_text: #222222
- grid: #D4EEF6
- muted_text: #6B6B6B
- blocking: #7A0000

## typography
- font_family: "Times New Roman", "Microsoft YaHei", "微软雅黑"
- title_family: "Times New Roman", "Microsoft YaHei", "微软雅黑"
- body_family: "Times New Roman", "Microsoft YaHei", "微软雅黑"
- data_family: "Times New Roman", "Microsoft YaHei", "微软雅黑"
- body: 24
- title: 36
- subtitle: 28
- lead: 28
- data: 20
- annotation: 18
- footnote: 16

## icons
- library: tabler-outline
- stroke_width: 2
- inventory: tabler-outline/droplet, tabler-outline/zoom-scan, tabler-outline/chart-column, tabler-outline/chart-funnel, tabler-outline/alert-triangle, tabler-outline/checklist, tabler-outline/chart-dots-3, tabler-outline/layers-intersect, tabler-outline/wave-sine, tabler-outline/circle-dot

## page_rhythm
- P01: anchor
- P02: anchor
- P03: dense
- P04: dense
- P05: anchor
- P06: dense
- P07: dense
- P08: breathing

## page_charts
- P04: pareto_chart
- P05: funnel_chart
- P06: grouped_bar_chart

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
