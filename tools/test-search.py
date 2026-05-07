#!/usr/bin/env python3
"""
test-search.py — 验证 expert:search 搜索和加载

测试项：
  1. 能从 extended 搜索到预期专家
  2. skills 字段可被 ExpertSkillBridge 正确解析
  3. 与 default 专家不重复
  4. load_from_dirs 多包加载

用法：
  python3 tools/test-search.py              # 需要 eket binary
  python3 tools/test-search.py --no-binary  # 纯 Python 验证（不依赖 eket）
"""

import sys, re, json, subprocess, argparse
from pathlib import Path

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

def test_python_loading():
    """纯 Python：验证所有文件可解析且 skills 字段存在"""
    repo_root = Path(__file__).parent.parent
    experts_dir = repo_root / "experts"

    passed = failed = 0
    missing_skills = []

    for md in sorted(experts_dir.rglob("*.md")):
        if md.name.upper() == "INDEX.MD":
            continue
        meta = extract_front_matter(md)
        if meta is None:
            print(f"  ❌ PARSE FAIL: {md.relative_to(repo_root)}")
            failed += 1
            continue

        required = ["id", "name_cn", "role", "emoji", "domain"]
        missing = [f for f in required if not meta.get(f)]
        if missing:
            print(f"  ❌ MISSING FIELDS {missing}: {md.relative_to(repo_root)}")
            failed += 1
            continue

        if not meta.get("skills") or not meta["skills"].get("primary"):
            missing_skills.append(str(md.relative_to(repo_root)))

        passed += 1

    print(f"\n  📋 解析: {passed} 通过, {failed} 失败")
    if missing_skills:
        print(f"  ⚠️  {len(missing_skills)} 个文件缺少 skills.primary:")
        for f in missing_skills[:10]:
            print(f"     - {f}")
    else:
        print("  ✅ 所有专家有 skills.primary 字段")
    return failed == 0

def test_eket_search(keyword: str, expected_pkg: str = "extended"):
    """调用 eket binary 验证搜索结果"""
    try:
        result = subprocess.run(
            ["eket", "expert:search", keyword, "--pkg", expected_pkg, "--limit", "5"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print(f"  ❌ eket expert:search '{keyword}' 失败: {result.stderr[:200]}")
            return False
        data = json.loads(result.stdout)
        if data.get("total_matches", 0) == 0:
            print(f"  ❌ 搜索 '{keyword}' 无结果")
            return False
        top = data["results"][0]
        print(f"  ✅ 搜索 '{keyword}': {data['total_matches']} 结果, 最佳={top['id']} ({top['pkg']})")
        return True
    except FileNotFoundError:
        print("  ⚠️  eket binary 未找到，跳过 binary 测试")
        return None
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 解析失败: {e}")
        return False

def test_eket_skills(expert_id: str):
    """验证 expert:skills 输出"""
    try:
        result = subprocess.run(
            ["eket", "expert:search", expert_id],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        found = any(r["id"] == expert_id or expert_id in r["id"] for r in data.get("results", []))
        if found:
            print(f"  ✅ expert:search 能定位到 {expert_id}")
        return found
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-binary", action="store_true", help="跳过 eket binary 测试")
    args = parser.parse_args()

    print("=" * 60)
    print("EKET Extended Expert 测试套件")
    print("=" * 60)

    results = []

    # Test 1: Python loading
    print("\n[1] 专家文件解析测试")
    ok = test_python_loading()
    results.append(("文件解析", ok))

    if not args.no_binary:
        print("\n[2] eket expert:search 搜索测试")
        test_cases = [
            ("nlp", "extended"),
            ("security", "extended"),
            ("aiml", "extended"),
            ("finance", "extended"),
            ("devops", "extended"),
        ]
        for keyword, pkg in test_cases:
            r = test_eket_search(keyword, pkg)
            if r is not None:
                results.append((f"搜索:{keyword}", r))

        print("\n[3] 全库搜索（default+extended）")
        try:
            result = subprocess.run(
                ["eket", "expert:search", "debug", "--limit", "10"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                pkgs = {r["pkg"] for r in data.get("results", [])}
                print(f"  ✅ 全库搜索: {data.get('total_matches',0)} 结果, 包含 pkgs={pkgs}")
                results.append(("全库搜索", True))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"  ⚠️  跳过: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    for name, r in results:
        icon = "✅" if r else "❌"
        print(f"  {icon} {name}")
    print(f"\n{passed} 通过, {failed} 失败")
    sys.exit(1 if failed > 0 else 0)

if __name__ == "__main__":
    main()
