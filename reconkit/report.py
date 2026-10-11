"""输出渲染：等宽表格 / Markdown / JSON。"""

import json


def _width(value):
    """按终端显示宽度计算（CJK 字符占 2 列）。"""
    total = 0
    for char in str(value):
        total += 2 if ord(char) > 0x2E80 else 1
    return total


def _pad(value, width):
    text = str(value)
    return text + " " * max(0, width - _width(text))


def render_table(rows, columns):
    """把 dict 列表渲染成对齐的等宽文本表格。"""
    matrix = [[str(row.get(col, "")) for col in columns] for row in rows]
    widths = []
    for index, col in enumerate(columns):
        widths.append(max([_width(col)] + [_width(line[index]) for line in matrix]))

    lines = ["  ".join(_pad(col, widths[i]) for i, col in enumerate(columns))]
    lines.append("  ".join("-" * widths[i] for i in range(len(columns))))
    for line in matrix:
        lines.append("  ".join(_pad(line[i], widths[i]) for i in range(len(columns))))
    return "\n".join(lines)


def render_markdown_table(rows, columns):
    """渲染 Markdown 表格（便于直接贴进报告）。"""
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def render_subdomains(records):
    """渲染子域名枚举结果。"""
    rows = [
        {
            "subdomain": record.get("name", ""),
            "ips": ", ".join(record.get("ips") or []) or "-",
            "source": ",".join(record.get("sources") or []),
        }
        for record in records
    ]
    if not rows:
        return "未发现子域名"
    return render_table(rows, ["subdomain", "ips", "source"])


def render_fingerprint(result):
    """渲染单个 URL 的指纹识别结果。"""
    if result.get("error"):
        return "无法访问 {0}  ({1})".format(result.get("url", ""), result["error"])

    header = "URL      : {0}\n状态码   : {1}\nServer   : {2}\n页面标题 : {3}".format(
        result.get("url", ""),
        result.get("status", "-"),
        result.get("server") or "-",
        result.get("title") or "-",
    )
    matched = result.get("matched") or []
    if not matched:
        return header + "\n指纹     : 未匹配到已知指纹"

    rows = [
        {"tech": item.get("name", ""), "category": item.get("category", ""), "evidence": "; ".join(item.get("evidence") or [])}
        for item in matched
    ]
    return header + "\n指纹     :\n" + render_table(rows, ["tech", "category", "evidence"])


def to_json(data):
    """统一 JSON 输出（保留中文）。"""
    return json.dumps(data, ensure_ascii=False, indent=2)
