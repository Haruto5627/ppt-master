<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: zh-CN
- audience: 良率与工艺专项决策会
- objective: 说明 D0 从 0.51 收到 0.29、剩余 0.09 挂在后淋洗与 hood，并推动按 D0、PWP、捕获率签批 W35 释放
- core_message: 真实工艺/设备回收约 0.16；W32 recipe 回退使表观 D0 回升；剩余靠 hood 气帘与 EBR，禁止把 recipe 收热算作回收
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
- inventory: tabler-outline/target, tabler-outline/adjustments, tabler-outline/droplet, tabler-outline/chart-column, tabler-outline/activity, tabler-outline/filter, tabler-outline/checklist, tabler-outline/alert-triangle, tabler-outline/timeline, tabler-outline/chart-dots-3

## page_rhythm
- P01: anchor
- P02: anchor
- P03: dense
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: breathing

## page_charts
- P03: waterfall_chart
- P06: line_chart

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
