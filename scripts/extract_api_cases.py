"""
从 data/test_cases.csv 中提取可 API 自动化的测试用例，
生成框架可用的参数化数据。

用法：
    py -3 scripts/extract_api_cases.py

输出：
    data/extracted_api_cases.json  — 所有 151 条分类结果
    data/auto_test_params.json     — 仅可自动化用例（框架兼容格式）
    data/model_mapping_template.json — 模型名映射模板
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "test_cases.csv"
OUT_FULL = PROJECT_ROOT / "data" / "extracted_api_cases.json"
OUT_AUTO = PROJECT_ROOT / "data" / "auto_test_params.json"
OUT_MODEL_MAP = PROJECT_ROOT / "data" / "model_mapping_template.json"

# ---------------------------------------------------------------------------
# 标题匹配规则  (regex, test_type, expected_success)
# 注意：列表中靠前的优先匹配
# ---------------------------------------------------------------------------
MODEL_SPECIFIC_RULES: list[tuple[str, str, bool]] = [
    # ── 提示词 ──
    (r"-(提示词超过(\d+)字符)$", "prompt_exceeds_limit", False),
    (r"-(提示词达上限(\d+)字符)$", "prompt_at_limit", True),
    # ── 参考图数量 ──
    (r"-(参考图超过(\d+)张)$", "reference_count_exceeds", False),
    (r"-(参考图达上限(\d+)张)$", "reference_count_at_limit", True),
    # ── 参考图大小 ──
    (r"-(参考图单张超过(\d+)(MB?|mb?))$", "reference_size_exceeds", False),
    # ── 参考图格式 ──
    (r"-(参考图不支持格式)$", "reference_unsupported_format", False),
    # ── 参考图比例/像素 ──
    (r"-(参考图比例/像素越界)$", "reference_aspect_ratio_violation", False),
    # ── 自定义尺寸 ──
    (r"-(自定义尺寸越界)$", "custom_dimension_out_of_bounds", False),
    # ── 尺寸选择（成功路径） ──
    (r"-(预置尺寸选择与生成)$", "preset_size_generation", True),
    (r"-(图像尺寸选择与生成)$", "image_size_generation", True),
    # ── 联网搜索 ──
    (r"-(联网搜索-支持模型开关验证)$", "search_switch_verify", True),
    (r"-(联网搜索-不支持模型无开关)$", "search_switch_hidden", True),
]

# 通用 UI 用例（无模型前缀，直接匹配标题）
GENERAL_RULES: list[tuple[str, str, bool]] = [
    ("图片生成-未输入提示词触发生成", "empty_prompt", False),
    ("图片生成-未选择模型触发生成", "no_model_selected", False),
    ("图片生成-未选择项目分类触发生成", "no_project_category", False),
    ("图片生成-提示词仅空格/无意义字符", "whitespace_prompt", False),
    ("图片生成-积分不足时生成", "insufficient_credits", False),
    ("图片生成-积分不足时生成", "insufficient_credits", False),
    # 成功路径
    ("图片生成-文生图-必填参数齐全生成成功", "basic_smoke", True),
    ("图片生成-文生图-切换不同模型分别生成", "switch_models_generation", True),
    ("图片生成-图生图-本地上传参考图生成", "upload_reference_generation", True),
]

# 无法 API 自动化的标题关键词 → 原因
UI_ONLY_KEYWORDS: dict[str, str] = {
    "从项目选择素材": "需要浏览项目素材库 UI",
    "从项目移动选择素材": "需要拖拽/移动 UI 交互",
    "删除已有参考图": "需要鼠标悬停+点击删除按钮",
    "替换已有参考图": "需要点击替换按钮+选择来源",
    "放大已有参考图": "需要弹窗/大图展示",
    "调整已有参考图位置": "需要拖拽排序",
    "AI优化": "AI 优化按钮交互，提示词转换逻辑",
    "模板库": "UI 模板选择+表单回填",
    "画质/数量/温度等模型特有控件": "UI 控件渲染验证",
    "生成结果-查看详情": "弹窗/抽屉 UI 展示",
    "生成结果-多条件筛选": "UI 筛选/分页/刷新",
    "积分-生成后正确扣减": "UI 积分余额同步显示",
    "重置参数": "表单重置 UI 行为",
    "模型调用失败的处理": "需要 mock 模型故障",
    "生成过程中网络异常": "需要模拟网络中断",
    "尺寸/比例/数量经提示词控制": "提示词语义控制，非结构化参数",
    "@参考图": "需要在提示词输入框中 @ 选中参考图",
}

# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def _try_remove_prefix(s: str, prefix: str) -> str:
    """移除 s 开头的 prefix，找不到时返回 None。"""
    return s[len(prefix):] if s.startswith(prefix) else None


def parse_title(title: str) -> dict[str, Any]:
    """
    解析一条用例标题，返回分类结果。
    返回字典字段：
        test_type, model_display, auto_applicable, expected_success,
        params (从中提取数字), notes
    """
    result: dict[str, Any] = {
        "auto_applicable": True,
        "test_type": "unknown",
        "model_display": None,
        "expected_success": None,
        "params": {},
        "notes": "",
    }

    # ── 1. 先匹配模型相关规则 ──
    for pattern, test_type, expected_success in MODEL_SPECIFIC_RULES:
        m = re.search(pattern, title)
        if m:
            result["test_type"] = test_type
            result["expected_success"] = expected_success
            # 模型名 = 匹配位置之前的部分
            model_display = title[: m.start()]
            result["model_display"] = model_display.strip()
            # 提取数字参数
            groups = m.groups()
            for g in groups:
                try:
                    result["params"]["limit"] = int(g)
                except (ValueError, TypeError):
                    # 可能是大小单位 "10MB"
                    if isinstance(g, str):
                        size_match = re.match(r"(\d+)\s*(MB?)?", g, re.IGNORECASE)
                        if size_match:
                            result["params"]["size_mb"] = int(size_match.group(1))
            break
    else:
        # ── 2. 匹配通用规则 ──
        matched_general = False
        for keyword, test_type, expected_success in GENERAL_RULES:
            if title == keyword or title.startswith(keyword):
                result["test_type"] = test_type
                result["expected_success"] = expected_success
                matched_general = True
                break

        # ── 3. 匹配 UI 不可自动化模式 ──
        if not matched_general:
            for keyword, reason in UI_ONLY_KEYWORDS.items():
                if keyword in title:
                    result["test_type"] = "ui_only"
                    result["auto_applicable"] = False
                    result["notes"] = reason
                    matched_general = True
                    break

    return result


def build_payload_changes(test_type: str, params: dict[str, Any]) -> dict[str, Any]:
    """根据 test_type 构造 payload_changes。"""
    changes: dict[str, Any] = {}

    if test_type == "prompt_exceeds_limit":
        limit = params.get("limit", 2000)
        changes["prompt"] = f"<需构造{limit + 10}个字符的提示词>"

    elif test_type == "prompt_at_limit":
        limit = params.get("limit", 2000)
        changes["prompt"] = f"<需构造恰好{limit}个字符的提示词>"

    elif test_type == "reference_count_exceeds":
        limit = params.get("limit", 10)
        changes["inputFile"] = f"<需提供{limit + 1}张参考图URL>"
        changes["_note"] = "确认 API 是否接受多张参考图的字段名（inputFile 数组？）"

    elif test_type == "reference_count_at_limit":
        limit = params.get("limit", 10)
        changes["inputFile"] = f"<需提供恰好{limit}张参考图URL>"
        changes["_note"] = "确认 API 是否接受多张参考图的字段名"

    elif test_type == "reference_size_exceeds":
        size_mb = params.get("size_mb", 10)
        changes["inputFile"] = f"<需提供>{size_mb}MB 的参考图URL>"
        changes["_note"] = "需准备超大参考图 URL"

    elif test_type == "reference_unsupported_format":
        changes["inputFile"] = "<需提供非JPEG/PNG/WEBP格式图片URL>"

    elif test_type == "reference_aspect_ratio_violation":
        changes["inputFile"] = "<需提供违反比例/像素约束的参考图URL>"
        changes["_note"] = "需确认该模型的比例约束规则"

    elif test_type == "custom_dimension_out_of_bounds":
        changes["imageSize"] = "<需填入越界尺寸>"
        changes["_note"] = "需确认该模型的自定义尺寸约束规则"

    elif test_type in ("preset_size_generation", "image_size_generation"):
        # 成功路径 — 不需要修改
        pass

    elif test_type == "empty_prompt":
        changes["prompt"] = ""

    elif test_type == "no_model_selected":
        changes["model"] = ""

    elif test_type == "no_project_category":
        changes["projectId"] = ""
        changes["categoryId"] = ""

    elif test_type == "whitespace_prompt":
        changes["prompt"] = "   "

    elif test_type == "insufficient_credits":
        changes["_note"] = "需使用积分不足的测试账号"

    elif test_type == "basic_smoke":
        pass  # 已由现有冒烟测试覆盖

    elif test_type == "switch_models_generation":
        changes["_note"] = "需遍历所有可用模型分别生成"

    elif test_type == "upload_reference_generation":
        changes["genType"] = 2
        changes["inputFile"] = "<需提供本地上传的参考图URL>"

    elif test_type in ("search_switch_verify", "search_switch_hidden"):
        changes["_note"] = "需确认联网搜索对应的 API 字段名"

    return changes


def generate_help_string(case: dict[str, Any]) -> str:
    """为每个可自动化用例生成描述性帮助文本（供后续编写测试代码参考）。"""
    test_type = case["test_type"]
    params = case.get("params", {})
    model = case.get("model_display", "")

    tips: dict[str, str] = {
        "prompt_exceeds_limit": (
            f"构造 {params.get('limit', 2000) + 10} 字符的 prompt，"
            "发送请求，预期被拦截（code != 200 或异步失败）"
        ),
        "prompt_at_limit": (
            f"构造恰好 {params.get('limit', 2000)} 字符的 prompt，"
            "预期提交成功并正常生成"
        ),
        "reference_count_exceeds": (
            f"提供 {params.get('limit', 10) + 1} 张参考图 URL，"
            "预期被拦截"
        ),
        "reference_count_at_limit": (
            f"提供恰好 {params.get('limit', 10)} 张参考图 URL，"
            "预期提交成功"
        ),
        "reference_size_exceeds": (
            f"提供 >{params.get('size_mb', 10)}MB 的参考图 URL，"
            "预期被拦截"
        ),
        "reference_unsupported_format": (
            "提供 BMP/TIFF/GIF 等非支持格式图片 URL，预期被拦截"
        ),
        "reference_aspect_ratio_violation": (
            "提供违反宽高比/像素约束的参考图，预期被拦截"
        ),
        "custom_dimension_out_of_bounds": (
            "填入超过模型允许范围的自定义宽高，预期被拦截"
        ),
        "preset_size_generation": (
            f"选择预置尺寸，{model}，预期生成成功且尺寸与所选一致"
        ),
        "image_size_generation": (
            f"选择图像尺寸，{model}，预期生成成功且尺寸与所选一致"
        ),
        "empty_prompt": (
            "prompt 置空，预期被拦截（按钮置灰或提交被拒）"
        ),
        "no_model_selected": (
            "model 置空，预期使用默认模型或被拦截"
        ),
        "no_project_category": (
            "projectId/categoryId 置空，预期提示必选"
        ),
        "whitespace_prompt": (
            "prompt 仅填空格，预期被校验拦截"
        ),
        "insufficient_credits": (
            "用积分不足的账号发起生成，预期提示积分不足，不扣费"
        ),
        "basic_smoke": "基础冒烟，已由现有 test_generate_image_success 覆盖",
        "switch_models_generation": "遍历所有可用模型各生成一次，验证均可成功",
        "upload_reference_generation": "上传本地参考图生成，验证图生图流程",
        "search_switch_verify": (
            "对支持联网搜索的模型验证开关可用"
        ),
        "search_switch_hidden": (
            "对不支持联网搜索的模型验证开关不出现"
        ),
    }
    return tips.get(test_type, "")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. 读取 CSV
    with CSV_PATH.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        raw_cases = list(reader)

    print(f"读取 CSV：{len(raw_cases)} 条用例\n")

    # 2. 逐条分类
    extracted: list[dict[str, Any]] = []
    stats: dict[str, int] = {"auto": 0, "ui_only": 0, "already_covered": 0}

    for idx, row in enumerate(raw_cases):
        title = row["标题"].strip()
        parsed = parse_title(title)

        payload_changes = build_payload_changes(
            parsed["test_type"], parsed["params"]
        )

        case = {
            "case_name": title,
            "source_csv_row": idx + 2,   # +2 = 1-indexed + header
            "csv_status": row.get("用例状态", ""),
            "test_type": parsed["test_type"],
            "model_display": parsed["model_display"],
            "model_internal": None,       # 待手动映射
            "auto_applicable": parsed["auto_applicable"],
            "expected_success": parsed["expected_success"],
            "payload_changes": payload_changes,
            "need_special_account": parsed["test_type"] == "insufficient_credits",
            "notes": parsed["notes"] or payload_changes.pop("_note", ""),
            "help": generate_help_string(
                {**parsed, "params": parsed["params"]}
            ),
        }
        extracted.append(case)

        # 统计
        if not parsed["auto_applicable"]:
            stats["ui_only"] += 1
        elif parsed["test_type"] == "basic_smoke":
            stats["already_covered"] += 1
        else:
            stats["auto"] += 1

    # 3. 写入完整分类结果
    with OUT_FULL.open("w", encoding="utf-8") as f:
        json.dump(extracted, f, ensure_ascii=False, indent=2)
    print(f"[1/3] 完整分类       → {OUT_FULL}")

    # 4. 写入仅可自动化用例
    auto_cases = [
        c for c in extracted
        if c["auto_applicable"] and c["test_type"] != "basic_smoke"
    ]
    with OUT_AUTO.open("w", encoding="utf-8") as f:
        json.dump(auto_cases, f, ensure_ascii=False, indent=2)
    print(f"[2/3] 可自动化用例  → {OUT_AUTO} ({len(auto_cases)} 条)")

    # 5. 生成模型映射模板
    model_names = sorted({
        c["model_display"]
        for c in extracted
        if c["model_display"] is not None and c["model_display"] != "图片生成"
    })
    model_map = {name: "TODO" for name in model_names}
    with OUT_MODEL_MAP.open("w", encoding="utf-8") as f:
        json.dump(model_map, f, ensure_ascii=False, indent=2)
    print(f"[3/3] 模型映射模板  → {OUT_MODEL_MAP} ({len(model_map)} 个待映射)\n")

    # 6. 打印摘要
    print("=" * 60)
    print("                    分 类 摘 要")
    print("=" * 60)
    print(f"  总用例数        : {len(raw_cases)}")
    print(f"  可 API 自动化   : {stats['auto']}")
    print(f"  纯 UI 无法自动化 : {stats['ui_only']}")
    print(f"  已由现有用例覆盖 : {stats['already_covered']}")
    print(f"  待映射模型       : {len(model_map)}")
    print("-" * 60)
    print("  按 test_type 分布：")
    type_dist: dict[str, int] = {}
    for c in extracted:
        type_dist[c["test_type"]] = type_dist.get(c["test_type"], 0) + 1
    for t, n in sorted(type_dist.items()):
        label = t
        if t == "ui_only":
            label = "ui_only (不可自动化)"
        print(f"    {label:<38} {n:>4} 条")
    print("-" * 60)
    print("\n待映射的模型名：")
    for name in model_names:
        print(f"  - {name}")
    print(
        f"\n👉 请编辑 {OUT_MODEL_MAP.name} ，"
        "将 \"TODO\" 替换为 API 实际使用的模型名。"
    )
    print("👉 参考图相关用例需先确认 API 是否支持多张参考图及字段格式。")
    print("👉 部分用例的 payload_changes 为占位文本，需根据实际规则填入合法/非法值。")


if __name__ == "__main__":
    main()
