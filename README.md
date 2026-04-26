# eket-experts-extended

EKET 扩展专家库 — 60位领域专家 persona，供 EKET 框架在 Master/Slaver 执行任务时动态加载。

## 目录结构

```
experts/
├── tech/        工程技术深化（8位）security/devops/qa/dba/sre/mobile/performance/platform
├── ai/          AI/ML/数据（8位）   aiml/ml/nlp/cv/mlops/bigdata/data-analyst/data
├── design/      设计（5位）         ux-research/visual/brand/motion/industrial
├── marketing/   市场营销（5位）      growth/content/seo/ads/product-marketing
├── pr/          公关宣传（4位）      pr-manager/crisis/media/kol
├── business/    商业法务（5位）      business/strategy/finance/legal/compliance
├── consulting/  咨询（3位）         mgmt/it-consulting/process
├── hr/          人力资源（5位）      hr/recruiter/hrbp/l-and-d/comp
├── training/    培训教育（3位）      trainer/coach/curriculum
├── knowledge/   知识管理（3位）      km/researcher/doc-writer
└── ops/         运营（4位）         product-ops/community/customer/supply-chain
```

## 安装

```bash
export EKET_EXTENDED_REPO=https://github.com/godlockin/eket-experts-extended
bash ~/.claude/skills/eket/scripts/install-extended.sh
```

## 使用

安装后在 ticket 中指派专家：

```markdown
**assigned_experts**: backend, security, tester
```

Slaver `task:claim` 时自动加载对应 profile 注入 ACTIVE_CONTEXT。

完整专家列表见 [experts/INDEX.md](experts/INDEX.md)。
