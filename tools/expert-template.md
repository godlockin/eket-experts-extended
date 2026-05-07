```yaml
id: eket.<domain>.<NNN>
name: <English Name>
name_cn: <中文名>
role: <角色名称>
emoji: <emoji>
domain: <domain>
tier: optional

description: <一句话描述，≤60字>

personality:
  type: <MBTI>
  traits:
    - <特质1>
    - <特质2>
    - <特质3>
  communication_style: <沟通风格>
  strengths: <核心优势>
  weaknesses: <潜在盲点>

background:
  experience: <N年经验描述>
  domain_expertise:
    - <领域1>
    - <领域2>
  notable_skills:
    - <代表性能力1>
    - <代表性能力2>

skills:
  primary:
    - <skill-id-1>   # 必须与 ~/.claude/skills/ 下存在的 skill 对应
    - <skill-id-2>
    - <skill-id-3>
  contextual:
    - skill: <skill-id>
      when: "domain=<domain> OR task_type=<type>"

# 若与其他专家有业务互斥，声明如下（需双向）：
# exclusive_with:
#   - eket.<other_domain>.<NNN>

thinking_framework:
  - <思维框架1>
  - <思维框架2>
  - <思维框架3>

analysis_focus:
  - <分析重点1>
  - <分析重点2>
  - <分析重点3>

output_format: |
  ## <emoji> <角色名> 报告

  ### 亮点
  - ...

  ### 风险 / 问题
  - ...

  ### 改进建议
  1. [P0] ...
  2. [P1] ...
  3. [P2] ...

trigger: <触发词，逗号分隔>
phase: 2
```

## Overview

<2-3 句描述该专家的核心价值定位>

## When to Use

- <场景1>
- <场景2>
- <场景3>

## When NOT to Use

- <反例1>
- <反例2>

## Process

1. **<步骤1>**：...
2. **<步骤2>**：...
3. **<步骤3>**：...

## Common Rationalizations to Reject

| 常见借口 | 反驳 |
|---------|------|
| "<借口1>" | <反驳> |
| "<借口2>" | <反驳> |

## Verification

- [ ] <验收检查1>
- [ ] <验收检查2>
