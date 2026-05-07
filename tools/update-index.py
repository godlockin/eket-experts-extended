#!/usr/bin/env python3
"""
update-index.py — 自动重建 experts/INDEX.md

扫描所有专家 .md 文件，提取 YAML front matter，
按目录分组生成带专家数量、id、role、trigger 的索引表。

用法：
  python3 tools/update-index.py
  python3 tools/update-index.py --dry-run   # 仅打印，不写文件
"""

import re, sys, argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def extract_front_matter(path: Path) -> dict | None:
    import yaml
    content = path.read_text(encoding="utf-8")
    m = re.match(r"```yaml\n(.*?)\n```", content, re.DOTALL)
    if m:
        try: return yaml.safe_load(m.group(1))
        except: return None
    m = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
    if m:
        try: return yaml.safe_load(m.group(1))
        except: return None
    return None

DOMAIN_LABELS = {
    "tech":       "⚙️  工程技术",
    "ai":         "🤖 AI / ML / 数据",
    "design":     "🎨 设计",
    "marketing":  "📣 市场营销",
    "pr":         "📰 公关传播",
    "business":   "💼 商业法务",
    "consulting": "🧭 咨询管理",
    "hr":         "👥 人力资源",
    "training":   "🎓 培训教育",
    "knowledge":  "📚 知识管理",
    "ops":        "🔧 运营",
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    experts_dir = repo_root / "experts"

    # 收集并分组
    groups: dict[str, list[dict]] = defaultdict(list)
    for md in sorted(experts_dir.rglob("*.md")):
        if md.name.upper() == "INDEX.MD":
            continue
        meta = extract_front_matter(md)
        if not meta:
            continue
        # 目录名作为分组 key
        group = md.parent.name
        meta["_file"] = md.name
        meta["_relpath"] = str(md.relative_to(experts_dir))
        meta["_group"] = group
        groups[group].append(meta)

    total = sum(len(v) for v in groups.items())

    lines = []
    lines.append(f"# EKET 扩展专家库索引")
    lines.append("")
    lines.append(f"> 自动生成 · 最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')} · 共 {sum(len(v) for v in groups.values())} 位专家")
    lines.append(">")
    lines.append("> **路径**：`~/.claude/skills/eket/experts/extended/experts/<group>/<file>`")
    lines.append("> **搜索**：`eket expert:search \"<keyword>\" --pkg extended`")
    lines.append("> **加载**：专家文件由 ExpertSkillBridge 在 task:claim / expert:compose 时自动加载")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🗺️ 目录总览")
    lines.append("")
    lines.append("| 目录 | 领域 | 专家数 | 包含角色 |")
    lines.append("|------|------|--------|----------|")
    for group in sorted(groups.keys()):
        experts = groups[group]
        label = DOMAIN_LABELS.get(group, f"📁 {group}")
        roles = "、".join(e.get("name_cn", e.get("id", "?")) for e in experts[:4])
        if len(experts) > 4:
            roles += f" +{len(experts)-4}"
        lines.append(f"| `{group}/` | {label} | {len(experts)} | {roles} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 每个分组详细表
    for group in sorted(groups.keys()):
        experts = groups[group]
        label = DOMAIN_LABELS.get(group, f"📁 {group}")
        lines.append(f"## {label}（{len(experts)} 位）")
        lines.append("")
        lines.append("| 文件 | ID | 角色 | Skills | 触发词 |")
        lines.append("|------|----|------|--------|--------|")
        for e in sorted(experts, key=lambda x: x.get("id", "")):
            fpath = f"`{e['_relpath']}`"
            eid = e.get("id", "—")
            role = f"{e.get('emoji','')}{e.get('name_cn', e.get('role',''))}"
            skills = e.get("skills", {})
            skill_list = skills.get("primary", []) if skills else []
            skill_str = ", ".join(f"`{s}`" for s in skill_list[:3])
            if len(skill_list) > 3:
                skill_str += f" +{len(skill_list)-3}"
            trigger = e.get("trigger", "—")
            if len(str(trigger)) > 30:
                trigger = str(trigger)[:30] + "…"
            lines.append(f"| {fpath} | `{eid}` | {role} | {skill_str or '—'} | {trigger} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 新增专家 SOP")
    lines.append("")
    lines.append("1. 在对应目录新建 `<role>.md`，复制 `tools/expert-template.md`")
    lines.append("2. 填写 YAML front matter（必填：id/name_cn/role/emoji/domain/tier/skills）")
    lines.append("3. 运行 `python3 tools/validate.py --with-default` 检查重复/overlap/互斥")
    lines.append("4. 运行 `python3 tools/update-index.py` 重建索引")
    lines.append("5. 运行 `python3 tools/test-search.py` 验证搜索+加载")
    lines.append("6. `git add -A && git commit -m 'feat(experts): add <role>'`")
    lines.append("")

    content = "\n".join(lines) + "\n"

    if args.dry_run:
        print(content)
    else:
        out = experts_dir / "INDEX.md"
        out.write_text(content, encoding="utf-8")
        print(f"✅ INDEX.md 已更新 ({sum(len(v) for v in groups.values())} 位专家)")

if __name__ == "__main__":
    main()
