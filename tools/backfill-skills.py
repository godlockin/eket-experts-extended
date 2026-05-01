#!/usr/bin/env python3
"""
backfill-skills.py — 为 extended 专家批量补充 skills.primary 字段

根据 domain/role/trigger 自动推断 skills，写入 YAML front matter。
已有 skills 字段的文件跳过（幂等）。
"""

import re, sys
from pathlib import Path

# domain → primary skills 映射
DOMAIN_SKILLS = {
    "ai_ml":       ["systematic-debugging", "brainstorming", "improve-codebase-architecture"],
    "security":    ["systematic-debugging", "security-review"],
    "devops":      ["systematic-debugging", "improve-codebase-architecture"],
    "qa":          ["tdd", "webapp-testing", "systematic-debugging"],
    "mobile":      ["tdd", "frontend-design", "systematic-debugging"],
    "performance": ["improve-codebase-architecture", "systematic-debugging", "webapp-testing"],
    "platform":    ["improve-codebase-architecture", "systematic-debugging"],
    "database":    ["systematic-debugging", "improve-codebase-architecture"],
    "sre":         ["systematic-debugging", "improve-codebase-architecture"],
    "data":        ["systematic-debugging", "brainstorming"],
    "data_analyst":["brainstorming", "systematic-debugging"],
    "nlp":         ["brainstorming", "systematic-debugging"],
    "cv":          ["brainstorming", "systematic-debugging"],
    "mlops":       ["systematic-debugging", "improve-codebase-architecture"],
    "bigdata":     ["systematic-debugging", "improve-codebase-architecture"],
    "design":      ["frontend-design", "design-review"],
    "ux_research": ["frontend-design", "design-review", "design-consultation"],
    "brand":       ["brainstorming", "design-consultation"],
    "marketing":   ["brainstorming", "copywriting"],
    "growth":      ["brainstorming", "brainstorming"],
    "seo":         ["brainstorming"],
    "content":     ["copywriting", "brainstorming"],
    "product_marketing": ["brainstorming", "to-prd"],
    "pr":          ["brainstorming", "copywriting"],
    "business":    ["brainstorming", "to-prd"],
    "strategy":    ["brainstorming", "to-prd"],
    "finance":     ["brainstorming"],
    "legal":       ["brainstorming"],
    "compliance":  ["brainstorming", "security-review"],
    "consulting":  ["brainstorming", "improve-codebase-architecture"],
    "hr":          ["brainstorming"],
    "recruiter":   ["brainstorming"],
    "hrbp":        ["brainstorming"],
    "training":    ["brainstorming", "learn"],
    "knowledge":   ["brainstorming", "doc-coauthoring"],
    "ops":         ["brainstorming", "systematic-debugging"],
    "supply_chain":["brainstorming"],
    "community":   ["brainstorming", "copywriting"],
}

# role 关键词 → skills 补充
ROLE_EXTRA = {
    "nlp":      ["brainstorming"],
    "ml":       ["systematic-debugging"],
    "devops":   ["systematic-debugging", "improve-codebase-architecture"],
    "security": ["security-review", "systematic-debugging"],
    "qa":       ["tdd", "webapp-testing"],
    "dba":      ["systematic-debugging"],
    "sre":      ["systematic-debugging", "improve-codebase-architecture"],
}

def infer_skills(meta: dict) -> list[str]:
    domain = meta.get("domain", "").lower().replace("-", "_")
    role = meta.get("role", "").lower()
    trigger = meta.get("trigger", "").lower()

    skills = set(DOMAIN_SKILLS.get(domain, ["brainstorming", "systematic-debugging"]))

    for kw, extra in ROLE_EXTRA.items():
        if kw in role or kw in trigger:
            skills.update(extra)

    # 去重保序
    seen = set()
    result = []
    for s in list(skills):
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result[:5]  # 最多5个 primary skills

def add_skills_to_yaml(content: str, skills: list[str]) -> str:
    skills_yaml = "skills:\n  primary:\n" + "".join(f"    - {s}\n" for s in skills)

    def inject(yaml_body: str) -> str:
        if "skills:" in yaml_body:
            return yaml_body
        # 找 tier: <value> 这一行（tier: optional 之类的单行值）并在其后插入
        lines = yaml_body.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if re.match(r"^tier:\s*\S", line):
                lines.insert(i + 1, skills_yaml)
                return "".join(lines)
        # fallback: 在 phase: 行之前插入
        for i, line in enumerate(lines):
            if re.match(r"^phase:", line):
                lines.insert(i, skills_yaml)
                return "".join(lines)
        # 最后追加
        return yaml_body.rstrip() + "\n" + skills_yaml + "\n"

    # ```yaml ... ``` format
    m = re.match(r"(```yaml\n)(.*?)(\n```)", content, re.DOTALL)
    if m:
        new_yaml = inject(m.group(2))
        if new_yaml == m.group(2):
            return content  # already had skills
        return m.group(1) + new_yaml + m.group(3) + content[m.end():]

    # --- ... --- format
    m = re.match(r"(---\n)(.*?)(\n---)", content, re.DOTALL)
    if m:
        new_yaml = inject(m.group(2))
        if new_yaml == m.group(2):
            return content
        return m.group(1) + new_yaml + m.group(3) + content[m.end():]

    return content

def main():
    import yaml
    repo_root = Path(__file__).parent.parent
    experts_dir = repo_root / "experts"

    updated = skipped = failed = 0
    for md in sorted(experts_dir.rglob("*.md")):
        if md.name.upper() == "INDEX.MD":
            continue
        content = md.read_text(encoding="utf-8")

        # check if skills already present
        m = re.match(r"```yaml\n(.*?)\n```", content, re.DOTALL)
        if not m:
            m = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
        if not m:
            print(f"  ⚠️  no YAML front matter: {md.name}")
            failed += 1
            continue

        try:
            meta = yaml.safe_load(m.group(1))
        except Exception as e:
            print(f"  ❌ parse error {md.name}: {e}")
            failed += 1
            continue

        if meta.get("skills") and meta["skills"].get("primary"):
            skipped += 1
            continue

        skills = infer_skills(meta)
        new_content = add_skills_to_yaml(content, skills)
        if new_content != content:
            md.write_text(new_content, encoding="utf-8")
            print(f"  ✅ {md.relative_to(repo_root)}: {skills}")
            updated += 1
        else:
            print(f"  ⚠️  could not inject skills: {md.name}")
            failed += 1

    print(f"\n完成: {updated} 更新, {skipped} 跳过(已有), {failed} 失败")

if __name__ == "__main__":
    main()
