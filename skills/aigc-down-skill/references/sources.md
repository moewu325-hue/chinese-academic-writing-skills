# 来源与取舍

本包提供中文学术任务的行文与语义约定，执行版本2026-10-20.1。文体选择和保真边界优先于任何仓库建议。以下是理念参考，不整包安装或逐字复制外部SKILL、代码、语料；来源数量不构成独立实证。

| 固定来源 | 取舍 |
| --- | --- |
| [Anbeeld/WRITING.md](https://github.com/Anbeeld/WRITING.md/tree/0c127ca4a4e51debec5adf4816f2bf464d83438b) | 句内层次、隐藏清单、段首与结尾；限制其过度合句与未经授权软化主张。 |
| [tw93/Waza](https://github.com/tw93/Waza/tree/d8fa34ff50a37043d40bbd3b9e622029a12dd37b) | 中文节奏和具体表达；不采用个人emoji、禁标点、工程口吻与项目数配额。 |
| [Kiterlin/anti-defensive-writing](https://github.com/Kiterlin/anti-defensive-writing/tree/c7edf8fc91ae9c4f7e58345bd12934bb4cf41c46) | 表达功能与防御性边界，纳入S6/模式17；不机械删除否定。 |
| [Hyacehila/humanizer-zh-next](https://github.com/Hyacehila/humanizer-zh-next/tree/a43616751ddd7187a35f516b9c0e77061f5cf234) | 关系、范围和主张强度；作者独立判断不因证据疑问自动撤回。 |
| [jefeerzhang/academic-humanizer-zh](https://github.com/jefeerzhang/academic-humanizer-zh/tree/0e6931c08154f46d07d70c6de9d6740256a4cdba) | 只借案例设计回归；不新增其规则、配额或研究状态改法。 |
| [stephenlzc/humanize-mba-text-skill](https://github.com/stephenlzc/humanize-mba-text-skill/tree/160902bb3469199f53bc276d7d7905eea923f3cf) | 规则附误报说明；不采用MBA文体为所有论文默认。 |
| [MrGeDiao/shuorenhua](https://github.com/MrGeDiao/shuorenhua/tree/e7c2b8670bd3e1988bfec199e861cebd87fc5e9c) | 保守改写与宿主入口思路；不引入外部运行器。 |

S5为针对中文多先行词/抽象二分的专项整合，不把通用代词提示冒称完整现成方案。旧16个模式编号保留作历史检索，旧例子的无据加料、检测率保证、口语/情绪/噪声配额和固定句式目标已撤出执行规则。

本包不包含patina完整插件、外部CLI、自动检测器或多agent常驻流程。脚本只负责它可确定检查的字段和范围；数字集合相同、锚点命中或机械PASS不足以证明语义保真。验收输入与标签分离存于evals，标签只在评审输出冻结后读取；不放入日常必读资源。

本包采用以下模块思想：

| 固定来源 | 采纳范围 |
| --- | --- |
| [humanize-paper](https://github.com/SyntaxSmith/humanize-paper/tree/ba796b08539319e71f1111d1073908d3c8142bab) | 数字、公式、引用差异思路；自主实现只报告工具。 |
| [evidence-aligned-scientific-revision](https://github.com/outrotim/evidence-aligned-scientific-revision/tree/ef04ea8be98dd3827a3f0d0f0001f0776460d96b) | 原位置、命中片段、具体核对问题，合入同一工具。 |
| [academic-writing-skills](https://github.com/WenyuChiou/academic-writing-skills/tree/edc5ede61a7900ae51a9959ad35a5fffab296c66) | 正式要求的来源、适用范围与核验日期，按需加载。 |
| [qiongli](https://github.com/jxpeng98/qiongli/tree/2081a0335d3784dd00708ecc8223fea4a0127b42) | 现有证据栏补来源定位；不引入图谱和编号体系。 |
| [Agent Skills](https://github.com/agentskills/agentskills/tree/69ef37e9424c0a7ea9dd2293b559e43ec8176379) | 冻结输入、标签分离、旧新逐处比较；只在修改技能时使用。 |
| [溯光](https://github.com/TanKenglim/suguang-ai-disclosure/tree/8a01dbef9ee25171c1477ddbf8e9533f2f5ec747) | 只借声明字段；不采用网页表单与未经核验的固定事实。 |

规则核对使用evals中的冻结输入与标签；评审输出冻结后再读取标签。本包保留验证用例，不附私人任务报告。上游更新应审查差异并重跑受影响项，不能直接覆盖本包约定。
