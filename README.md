# 中文学术写作 Skills

三个同级技能，共用中文行文与语义保真约定。发行版本 `2026.10.21`（标签 `v2026.10.21`）；修订、起草的执行规则版本 `2026-10-20.1`，检索的职责版本 `2026-10-12.1`。发行版本标识文件包，不表示三个职责都修改过。

## 安装与入口

解压发行ZIP，将 `skills/` 下三个完整目录复制到宿主的技能目录，保持同级关系；不要只复制 `SKILL.md`。例如 Codex 的 `~/.agents/skills/` 或 Claude Code 的 `~/.claude/skills/`；安装后在宿主中确认入口可见。已有同名技能时先核对自己的修改再替换。

```text
技能目录/
├── aigc-down-skill/
├── research-writing-skill/
└── academic-researcher/
```

| 请求 | 入口 |
| --- | --- |
| 已有稿润色、去套话、表达审阅 | `aigc-down-skill` |
| 根据材料起草、综述、开题、审稿回复或获准重组 | `research-writing-skill` |
| 找文献、核来源、核引文、整理题录 | `academic-researcher` |

两个写作入口须完整读取共享语义约定与六项行文规则。正文沿研究对象、理论、问题、材料与发现推进；重复免责可合并，事实性否定、真实否定结果和独立边界须保留。规则不规定通用节号、否定词配额或“全文只留一次”，允许零修改。

## 差异检查器

Python 3.11以上，纯标准库、只读输入、无网络；TXT、Markdown、TeX须为UTF-8，DOCX/PDF先由已有文档工具取得同范围文本。

```sh
python -I -B skills/aigc-down-skill/scripts/check_tells.py --orig 原稿.txt --rev 改稿.txt --json
python -I -B skills/aigc-down-skill/scripts/check_tells.py --check --root skills --json
```

只审阅时两个参数传同一路径；明确压缩、摘要、扩写、翻译或重组时加 `--non-preserving-length`。读取 `execution_status=ok/error` 判断执行状态，CLI退出码固定为0。数字、公式、引用、否定和限定词统计仅帮助定位；相同计数仍可能错绑对象，机械通过不证明语义等价。

`--check` 比较两个写作入口与共享参考的执行规则版本。检索职责版本单独记录并检查缺失或重复，不与写作版本比较；可选共享索引与宿主入口仅在显式指定时读取。

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

## 来源与许可

规则同步范围及公共适配见 [SOURCE.md](SOURCE.md)，发行变化见 [CHANGELOG.md](CHANGELOG.md)。根目录采用 [MIT许可](LICENSE)；SiluPanda的参考、模板、脚本保留其[原MIT许可](skills/academic-researcher/LICENSE)，详见 [NOTICE.md](NOTICE.md)。
