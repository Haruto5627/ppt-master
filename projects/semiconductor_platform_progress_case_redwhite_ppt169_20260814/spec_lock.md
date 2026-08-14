<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: zh-CN
- audience: 公司管理层，以及研发、工程、采购、EHS负责人
- objective: 说明平台建设阶段、能力形成和关键阻塞，使管理层能够确认未来90天行动及五项资源决策
- core_message: 项目总体完成68.6%，按节点关闭关键阻塞并及时决策，可追回7–10天并维持2026年12月15日阶段验收目标
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
- inventory: tabler-outline/building-factory-2, tabler-outline/circuit-resistor, tabler-outline/timeline, tabler-outline/tools, tabler-outline/shield-check, tabler-outline/alert-triangle, tabler-outline/route, tabler-outline/database, tabler-outline/chart-dots-3, tabler-outline/checklist

## page_rhythm
- P01: anchor
- P02: anchor
- P03: breathing
- P04: dense
- P05: dense
- P06: anchor
- P07: dense
- P08: dense
- P09: dense
- P10: dense
- P11: breathing

## page_charts
- P04: progress_bar_chart
- P06: funnel_chart
- P07: heatmap_chart
- P10: roadmap_vertical

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
