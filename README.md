# 中文学术写作 Skills

三个同级技能，共用一套中文行文与语义保真规则。默认表达紧凑，材料、做法和结果交代完成后停住；保留实质条件、否定结果、计划与作者评价。

规则版本：`2026-10-12.1`。发行日期：2026-10-13。

## 选择入口

| 请求 | 技能 | 示例 |
| --- | --- | --- |
| 修改已有稿、去套话、表达审阅 | `aigc-down-skill` | “润色这段，保留原意，直接给正文。” |
| 根据材料起草、综述、开题、审稿回复 | `research-writing-skill` | “根据这些材料写一段研究背景。” |
| 查文献、核来源、核引文、整理参考文献 | `academic-researcher` | “核对这段主张的证据，注明来源位置。” |

紧密信息可合句，层次或条件范围变化时分句；精简重复免责，自行追加的保险式收尾撤出默认写法。原稿已有的实质否定、研究计划、限定和独立判断随其对象保留。原文已经清楚时允许零修改。具体行文规则只维护在 `aigc-down-skill/references/`。

## 安装

下载本仓库或完整 ZIP，将 `skills/` 下三个目录完整复制到同一个技能目录，保持同级关系：

```text
技能目录/
├── aigc-down-skill/
├── research-writing-skill/
└── academic-researcher/
```

| 工具 | 个人技能目录 |
| --- | --- |
| Codex | `~/.agents/skills/` |
| Claude Code | `~/.claude/skills/` |

Windows 中 `~` 是用户目录。已有同名技能时先保存原目录，再替换为这三个完整目录；不要只复制 `SKILL.md`。这是完整文件包，无自动复制安装器。安装后在目标工具中确认三个入口可见。

目录依据：[Codex 官方说明](https://learn.chatgpt.com/docs/build-skills)、[Claude Code 官方说明](https://code.claude.com/docs/en/skills)，2026-10-13核对。

## 按需能力

- 整节、整篇稿件或明确要求审阅时，运行同一个差异检查器；日常小段直接交付正文。
- 正式提交时按需核对目标要求、官方来源及核验日期；需要披露时生成真实的中英文AI使用声明。
- 核证据时，在已有证据栏补已核实页码、章节或表号。取不到的位置记录具体缺口。
- 只在修改技能时使用冻结回归输入与标签，日常写作不加载测试资产。

## 差异检查器

Python 3.11或更高版本，纯标准库，只读输入，无网络。输入使用同范围UTF-8 TXT、Markdown或TeX；DOCX/PDF先由现有文档工具取得文本。

从仓库根目录运行：

```sh
python -I skills/aigc-down-skill/scripts/check_tells.py --orig 原稿.txt --rev 改稿.txt --json
python -I skills/aigc-down-skill/scripts/check_tells.py --check --root skills --json
```

只审阅一个文件时，两个参数传同一路径，输出单稿定位。明确压缩、摘要、扩写、翻译或结构重写时加 `--non-preserving-length`。

工具报告数字、公式、引文、否定与限定词等变化及原始行列。长度和标点统计供回读；重复片段的位置为计数候选。CLI返回路径退出码为0，须读取 `execution_status=ok/error` 判断执行是否完成。数学和作者年份识别范围见源码docstring。

例如“甲为3，乙为4；甲未增加，乙增加”改成“甲为4，乙为3；甲增加，乙未增加”，计数可能完全相同，对象归属已经改变；语义仍需逐处核对。工具不打分、不设文本质量通过线、不接检测器、不计算句长CV。

## 学术检索辅助资源

`academic-researcher/references/`和`examples/`保留题录格式、证据表、专题参考与模板，按任务加载。TeX模板是结构示例，实际投稿使用目标单位的当前要求。

三个原有Node.js脚本保留为可选资源，无第三方包依赖：`check-citations.js`检查键对应，`validate-bib.js`查询Crossref，`resolve-papers.js`查询论文元数据。后两项会联网，先核对源码、用途与服务要求再使用。核心中文写作与Python检查器不依赖Node.js；这些旧脚本的在线服务可用性不作为本次发行验收结果。

## 验证

```sh
python -I -B -m unittest discover -s skills/aigc-down-skill/tests -v
python -I -B -m unittest discover -s tests -v
```

首个发行包实测：第一组31项通过，第二组4项通过，三个SKILL入口的元数据检查通过。第一组验证检查器契约，第二组验证发行包路径、引用及资源完整性。构造回归例在 [cases.json](skills/aigc-down-skill/evals/cases.json)，标签在 [expected.json](skills/aigc-down-skill/evals/expected.json)；先冻结改稿和无标签评审，再读取标签。计数检查与构造样例不能替代实际稿件的逐处核对。

## 来源与许可

本项目的规则与检查器为针对中文学术任务整理的实现；理念来源与固定提交见两个写作技能的 `references/sources.md`。`academic-researcher`部分参考、模板和Node.js脚本源自SiluPanda项目，保留其MIT许可。详见 [NOTICE.md](NOTICE.md) 与 [LICENSE](LICENSE)。
