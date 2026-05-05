# eket-experts-extended

EKET 扩展专家库 — 52位领域专家 persona + 配套 skills JSON，供 EKET 框架在 Master/Slaver 执行任务时动态加载。

## 实际目录结构

本目录（`extended/`）包含两个子树：

```
extended/
├── experts/             专家 persona（.md）
│   ├── tech/            工程技术深化（8位）  security/devops/qa/dba/sre/mobile/performance/platform
│   ├── ai/              AI/ML/数据（8位）   aiml/ml/nlp/cv/mlops/bigdata/data-analyst/data
│   ├── design/          设计（5位）         ux-research/visual/brand/motion/industrial
│   ├── marketing/       市场营销（5位）      growth/content/seo/ads/product-marketing
│   ├── pr/              公关宣传（4位）      pr-manager/crisis/media/kol
│   ├── business/        商业法务（5位）      business/strategy/finance/legal/compliance
│   ├── consulting/      咨询（3位）         mgmt/it-consulting/process
│   ├── hr/              人力资源（5位）      hr/recruiter/hrbp/l-and-d/comp
│   ├── training/        培训教育（3位）      trainer/coach/curriculum
│   ├── knowledge/       知识管理（3位）      km/researcher/doc-writer
│   ├── ops/             运营（4位）         product-ops/community/customer/supply-chain
│   └── INDEX.md         完整专家索引
└── skills/              配套工具 JSON（eket skill:run 可直接调用）
    ├── algorithm/       ML 训练/评估/部署（8个）
    ├── analysis/        需求/竞品/可行性分析（4个）
    ├── data/            数据管道/质量/ETL（4个）
    ├── devops/          CI/容器/监控（4个）
    ├── documentation/   API doc/架构文档/onboarding（3个）
    ├── hr/              JD/面试/绩效（4个）
    ├── implementation/  配置/迁移/集成（4个）
    ├── llm/             微调/评估/RAG/prompt（4个）
    ├── ops/             容量/事后分析/SLA（4个）
    ├── security/        威胁建模/渗透/扫描（4个）
    └── ux/              设计系统/可用性/原型（5个）
```

## 安装（本地）

扩展专家库已随 EKET skill 一同安装，无需额外操作。路径：

```
~/.claude/skills/eket/experts/extended/
```

如需手动重新安装整个 EKET skill（含扩展库）：

```bash
bash /path/to/eket/scripts/install-skill.sh --update
```

## 使用

在 ticket 中通过 `--expertise` 指派专家：

```bash
eket task:create "威胁建模评审" --expertise security --effort 2d
```

或在 `.md` ticket 文件中：

```markdown
- required_expertise: [security, devops]
```

`master:heartbeat` 派送时自动向量匹配最合适的 Slaver；`task:claim --role security` 精确过滤。

## 读取专家 persona

```bash
# 读取某位专家的完整 profile
cat ~/.claude/skills/eket/experts/extended/experts/tech/security.md

# 完整专家列表
cat ~/.claude/skills/eket/experts/extended/experts/INDEX.md
```

完整专家索引见 [experts/INDEX.md](experts/INDEX.md)。
