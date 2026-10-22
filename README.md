# 中文学术写作 Skills

面向中文学术任务的三个同级技能：修订已有稿、依据材料起草、检索与核对来源。

[![Release](https://img.shields.io/badge/release-v2026.10.21-blue)](https://github.com/moewu325-hue/chinese-academic-writing-skills/releases) ![Python](https://img.shields.io/badge/checker-Python%203.11%2B-3776AB) [![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

本项目把写作与来源核验拆成独立职责，让 AI 宿主根据当前请求选择入口，共用中文行文与语义保真约定。适合已有稿润色、论文段落与综述起草、开题和审稿答复，以及文献筛选、引文支持关系和参考文献整理；输出以用户材料或已核验来源为依据。

发行版本 `2026.10.21`（标签 `v2026.10.21`）；修订、起草的执行规则版本 `2026-10-20.1`，检索的职责版本 `2026-10-12.1`。发行版本标识文件包，不表示三个职责都修改过。

## 主要能力与分工

| 当前任务 | 入口 | 工作重点 |
| --- | --- | --- |
| 已有稿润色、去套话、表达审阅 | `aigc-down-skill` | 保留命题、条件、数值归属、作者立场与判断强度；允许零修改 |
| 依据材料起草、综述、开题、审稿回复或获准重组 | `research-writing-skill` | 按对象、理论、问题、材料与发现组织正文，保持研究计划与事实的区别 |
| 找文献、核来源、核引文、整理题录 | `academic-researcher` | 记录实际检索与读到的范围，核对主张、证据、版本和适用条件 |
| 修订差异与版本检查 | Python差异检查器 | 只读比较与定位可疑变化，输出结构化JSON供人工回读 |

两个写作入口须完整读取共享语义约定与六项行文规则。正文沿研究对象、理论、问题、材料与发现推进，逐项回应放在审稿答复；重复免责可合并，事实性否定、真实否定结果和独立边界须保留。规则不规定通用节号、否定词配额或「全文只留一次」。

## 三步开始

1. 从 [Releases](https://github.com/moewu325-hue/chinese-academic-writing-skills/releases) 下载并解压发行ZIP。
2. 将 `skills/` 下三个完整目录复制到宿主技能目录，保持同级关系，不只复制 `SKILL.md`。
3. 按宿主要求刷新/重启并确认三个入口可见，提供原文或材料后选择对应技能。

例如 Codex 可使用 `~/.agents/skills/`，Claude Code可使用 `~/.claude/skills/`；已有同名技能时先核对自定义修改再替换。缺少相邻共享参考时无法执行完整写作规则。

```text
技能目录/
├── aigc-down-skill/
├── research-writing-skill/
└── academic-researcher/
```

## 使用示例

```text
使用 aigc-down-skill 润色这段中文学术稿，保留所有数值、条件和作者判断。
使用 research-writing-skill，根据这些已提供材料起草综述小节，缺少证据处单列。
使用 academic-researcher，核对这些句子与所引文献的支持关系，附核对位置。
```

技能由 AI 宿主读取并执行，不是独立聊天客户端。纯润色不自动扩展为章节重写或新检索；起草不会补造数据、来源或机制。DOCX、PDF、TeX等交付格式按宿主已有文档能力处理，文件格式不改变三个入口的职责。

## 差异检查器

Python 3.11以上，纯标准库、只读输入、无网络；TXT、Markdown、TeX须为UTF-8，DOCX/PDF先由已有文档工具取得同范围文本。

```sh
python -I -B skills/aigc-down-skill/scripts/check_tells.py --orig 原稿.txt --rev 改稿.txt --json
python -I -B skills/aigc-down-skill/scripts/check_tells.py --check --root skills --json
```

只审阅时两个参数传同一路径；明确压缩、摘要、扩写、翻译或重组时加 `--non-preserving-length`。读取 `execution_status=ok/error` 判断执行状态，CLI退出码固定为0。数字、公式、引用、否定和限定词统计仅帮助定位；相同计数仍可能错绑对象，机械通过不证明语义等价。

`--check` 比较两个写作入口与共享参考的执行规则版本。检索职责版本单独记录并检查缺失或重复，不与写作版本比较；可选共享索引与宿主入口仅在显式指定时读取。

## 技术栈与目录

核心是 Markdown技能入口与相对路径参考，读取技能本身不依赖额外运行器。Python **3.11+ 标准库**用于差异检查、单元测试和发行打包；检索辅助资源中的Node.js脚本按需使用，不是安装技能的前提。

```text
chinese-academic-writing-skills/
├── skills/
│   ├── aigc-down-skill/           # 修订、共享规则、差异检查器
│   ├── research-writing-skill/    # 起草与论证组织
│   └── academic-researcher/       # 检索、核验、题录与按需模板
├── tools/build_release.py        # 按审核清单打包
├── tests/                        # 发行完整性测试
├── RELEASE_FILES / SHA256SUMS     # 文件白名单与内容校验和
└── SOURCE.md / NOTICE.md          # 公共适配与权属
```

## 验证与构建

从仓库根运行，均不安装依赖：

```sh
python -I -B -m unittest discover -s skills/aigc-down-skill/tests -v
python -I -B -m unittest discover -s tests -v
python -I -B tools/build_release.py --output build/chinese-academic-writing-skills_20261021.zip
```

构建器只收录 [RELEASE_FILES](RELEASE_FILES) 中已审核的文件，生成逐文件 `SHA256SUMS`，固定顺序、时间戳和权限。同一文件内容在同一Python/zlib环境可复现相同ZIP；跨压缩库版本可能产生不同压缩字节。新增资源须更新清单；构建不自动纳入目录中的额外文件。

CI运行检查器32项测试、发行完整性测试及实际构建。发行测试检查资源链接、路径迁移、归档安装结构、内容校验和与确定性。它们不证明写作行为在所有模型、学科与稿件上正确。[冻结输入](skills/aigc-down-skill/evals/cases.json)与[标签](skills/aigc-down-skill/evals/expected.json)只在修改规则时使用，须先冻结独立评审再读标签。

`academic-researcher` 的参考、示例、TeX模板和三个Node.js脚本按需使用；模板服从目标单位当前要求。`check-citations.js`核引用键，`validate-bib.js`及`resolve-papers.js`会联网；使用前核对源码、服务要求和实际可用性。本发行未验证在线服务，不为使用技能安装Node.js或其他工具。

TeX模板编译与在线检索服务未在本发行中验证；模板存在不表示满足任一学校或期刊的现行要求。

## 常见问题

**一定能降低AIGC检测率吗？** 不作检测率、作者身份或投稿结果承诺。技能目标是准确、清楚和符合文体，原文合适时允许零修改。

**差异检查器返回0，为什么还有错误？** CLI退出码固定为0，必须读取JSON的 `execution_status`、`errors` 与 `findings`。计数与机械检查用于定位，不能证明语义等价。

**为什么三个版本号不同？** 发行版描述文件包，修订/起草共享执行规则版本，检索职责独立演进；检查器不会把职责版本与执行版本强行比较。

**能只装其中一个目录吗？** 本发行要求三个目录保持同级；两个写作入口共读修订目录的参考，拆散或只复制入口会破坏相对资源路径。

**需要安装所有脚本依赖吗？** 不需要。核心技能是文本规则，Python检查器仅用标准库；在线Node.js辅助脚本与TeX模板在任务确有需要时再核对和运行。

## 来源与许可

规则同步范围及公共适配见 [SOURCE.md](SOURCE.md)，发行变化见 [CHANGELOG.md](CHANGELOG.md)。根目录采用 [MIT许可](LICENSE)；SiluPanda的参考、模板、脚本保留其[原MIT许可](skills/academic-researcher/LICENSE)，详见 [NOTICE.md](NOTICE.md)。
