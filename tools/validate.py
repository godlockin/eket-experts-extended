#!/usr/bin/env python3
"""
validate.py — EKET extended expert/skills 质量守护

功能：
  1. 解析所有专家 YAML front matter
  2. 检测 id/name_cn 重复
  3. 检测 skills 重度 overlap（≥70% 交集）
  4. 检测互斥声明（exclusive_with 字段）
  5. 检查必填字段完整性
  6. 与 default 专家对比（避免 extended 重复覆盖 default）

用法：
  python3 tools/validate.py                   # 仅检查 extended
  python3 tools/validate.py --with-default    # 同时与 default 专家对比
  python3 tools/validate.py --expert ai/nlp.md  # 仅检查单个文件
"""

import sys, re, json, argparse
from pathlib import Path
from collections import defaultdict

# ── YAML front matter parser (no external deps) ──────────────────────────────

def parse_yaml_block(text: str) -> dict:
    """极简 YAML subset 解析：支持 scalar/list/nested（够用于专家文件）"""
    import yaml  # stdlib pyyaml not guaranteed; try it
    return yaml.safe_load(text)

def extract_front_matter(path: Path) -> dict | None:
    content = path.read_text(encoding="utf-8")
    # ```yaml ... ``` format
    m = re.match(r"```yaml\n(.*?)\n```", content, re.DOTALL)
    if m:
        try:
            return parse_yaml_block(m.group(1))
        except Exception as e:
            print(f"  [WARN] YAML parse error in {path}: {e}")
            return None
    # --- ... --- format
    m = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
    if m:
        try:
            return parse_yaml_block(m.group(1))
        except Exception as e:
            print(f"  [WARN] YAML parse error in {path}: {e}")
            return None
    return None

def collect_experts(root: Path, pkg: str) -> list[dict]:
    experts = []
    for md in sorted(root.rglob("*.md")):
        if md.name.upper() == "INDEX.MD":
            continue
        meta = extract_front_matter(md)
        if meta is None:
            continue
        meta["_file"] = str(md.relative_to(root.parent))
        meta["_pkg"] = pkg
        experts.append(meta)
    return experts

# Skills that are too generic to indicate meaningful overlap
GENERIC_SKILLS = {
    "brainstorming", "systematic-debugging", "learn",
    "doc-coauthoring", "copywriting",
}

def get_all_skills(meta: dict) -> set[str]:
    skills = set()
    s = meta.get("skills")
    if not s:
        return skills
    for sk in s.get("primary", []):
        skills.add(str(sk).strip())
    for cs in s.get("contextual", []):
        if isinstance(cs, dict):
            skills.add(str(cs.get("skill", "")).strip())
        else:
            skills.add(str(cs).strip())
    return skills

def get_domain_skills(meta: dict) -> set[str]:
    """只返回非通用的领域特定 skills"""
    return get_all_skills(meta) - GENERIC_SKILLS
    skills = set()
    s = meta.get("skills")
    if not s:
        return skills
    for sk in s.get("primary", []):
        skills.add(str(sk).strip())
    for cs in s.get("contextual", []):
        if isinstance(cs, dict):
            skills.add(str(cs.get("skill", "")).strip())
        else:
            skills.add(str(cs).strip())
    return skills

# ── Checks ────────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = ["id", "name_cn", "role", "emoji", "domain", "tier"]

def check_required_fields(experts: list[dict]) -> list[str]:
    errors = []
    for e in experts:
        missing = [f for f in REQUIRED_FIELDS if not e.get(f)]
        if missing:
            errors.append(f"  ❌ {e['_file']}: 缺少必填字段 {missing}")
    return errors

def check_duplicate_ids(experts: list[dict]) -> list[str]:
    seen = defaultdict(list)
    for e in experts:
        seen[e.get("id", "")].append(e["_file"])
    return [
        f"  ❌ 重复 id={id_}: {files}"
        for id_, files in seen.items()
        if len(files) > 1 and id_
    ]

def check_duplicate_names(experts: list[dict]) -> list[str]:
    seen = defaultdict(list)
    for e in experts:
        seen[e.get("name_cn", "")].append(e["_file"])
    return [
        f"  ⚠️  重复 name_cn='{name}': {files}"
        for name, files in seen.items()
        if len(files) > 1 and name
    ]

def check_skill_overlap(experts: list[dict], threshold: float = 0.7) -> list[str]:
    warnings = []
    for i in range(len(experts)):
        for j in range(i + 1, len(experts)):
            a, b = experts[i], experts[j]
            sa, sb = get_domain_skills(a), get_domain_skills(b)
            # 只在双方都有领域特定 skill 时才比较
            if not sa or not sb:
                continue
            inter = sa & sb
            smaller = min(len(sa), len(sb))
            if smaller == 0:
                continue
            ratio = len(inter) / smaller
            if ratio >= threshold:
                warnings.append(
                    f"  ⚠️  高度 overlap ({ratio:.0%}) "
                    f"{a['_file']} ↔ {b['_file']}\n"
                    f"     共同 domain-specific skills: {sorted(inter)}"
                )
    return warnings

def check_exclusive_with(experts: list[dict]) -> list[str]:
    """检测 exclusive_with 声明的互斥是否双向一致"""
    id_map = {e.get("id"): e for e in experts}
    warnings = []
    for e in experts:
        excl = e.get("exclusive_with", [])
        for other_id in excl:
            other = id_map.get(other_id)
            if other is None:
                warnings.append(f"  ⚠️  {e['_file']}: exclusive_with 引用不存在的 id={other_id}")
                continue
            # 检查对方是否也声明了互斥
            if e.get("id") not in other.get("exclusive_with", []):
                warnings.append(
                    f"  ⚠️  互斥不对称: {e['_file']} → {other_id} "
                    f"但 {other['_file']} 未声明 exclusive_with {e.get('id')}"
                )
    return warnings

def check_skills_missing(experts: list[dict]) -> list[str]:
    missing = []
    for e in experts:
        if not e.get("skills") or not e["skills"].get("primary"):
            missing.append(f"  ⚠️  {e['_file']} ({e.get('id','?')}): 缺少 skills.primary 字段")
    return missing

def check_overlap_with_default(extended: list[dict], default: list[dict]) -> list[str]:
    warnings = []
    default_ids = {e.get("id") for e in default}
    default_names = {e.get("name_cn") for e in default}
    for e in extended:
        if e.get("id") in default_ids:
            warnings.append(f"  ❌ extended {e['_file']} id={e.get('id')} 与 default 重复")
        if e.get("name_cn") in default_names and e.get("name_cn"):
            warnings.append(f"  ⚠️  extended {e['_file']} name_cn='{e.get('name_cn')}' 与 default 重复")
        # skills overlap with default
        se = get_all_skills(e)
        for d in default:
            sd = get_all_skills(d)
            if not se or not sd:
                continue
            inter = se & sd
            ratio = len(inter) / min(len(se), len(sd))
            if ratio >= 0.8:
                warnings.append(
                    f"  ⚠️  {e['_file']} skills 与 default/{d.get('id')} 高度重叠 ({ratio:.0%}): {sorted(inter)}"
                )
    return warnings

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="EKET expert/skills validator")
    parser.add_argument("--with-default", action="store_true", help="同时与 default 专家对比")
    parser.add_argument("--expert", help="仅检查单个文件（相对于 experts/ 目录）")
    parser.add_argument("--threshold", type=float, default=0.7, help="overlap 阈值（默认 0.7）")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    experts_dir = repo_root / "experts"

    # 收集 extended 专家
    if args.expert:
        target = experts_dir / args.expert
        if not target.exists():
            print(f"File not found: {target}")
            sys.exit(1)
        meta = extract_front_matter(target)
        if not meta:
            print("No valid YAML front matter found")
            sys.exit(1)
        meta["_file"] = args.expert
        meta["_pkg"] = "extended"
        extended = [meta]
    else:
        extended = collect_experts(experts_dir, "extended")

    print(f"\n🔍 验证 {len(extended)} 个 extended 专家\n")

    errors, warnings = [], []

    errors += check_required_fields(extended)
    errors += check_duplicate_ids(extended)
    warnings += check_duplicate_names(extended)
    warnings += check_skill_overlap(extended, args.threshold)
    warnings += check_exclusive_with(extended)
    warnings += check_skills_missing(extended)

    # 与 default 对比
    default = []
    if args.with_default:
        default_dir = Path.home() / ".claude/skills/eket/experts/default"
        if default_dir.exists():
            default = collect_experts(default_dir, "default")
            print(f"📦 对比 {len(default)} 个 default 专家\n")
            errors += check_overlap_with_default(extended, default)

    # 输出
    all_issues = errors + warnings
    if args.json:
        print(json.dumps({
            "total_experts": len(extended),
            "errors": len(errors),
            "warnings": len(warnings),
            "issues": all_issues,
        }, ensure_ascii=False, indent=2))
    else:
        if errors:
            print(f"❌ Errors ({len(errors)}):")
            for e in errors: print(e)
            print()
        if warnings:
            print(f"⚠️  Warnings ({len(warnings)}):")
            for w in warnings: print(w)
            print()
        if not all_issues:
            print("✅ 全部检查通过！")
        else:
            print(f"\n总计：{len(errors)} errors, {len(warnings)} warnings")

    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
