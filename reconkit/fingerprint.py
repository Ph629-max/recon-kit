"""基于响应特征的技术栈指纹识别。"""

import json
import os
import re

from . import netutil

DEFAULT_RULES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules", "fingerprints.json")


def load_rules(path=None):
    """加载指纹规则文件。"""
    with open(path or DEFAULT_RULES, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _search(pattern, text):
    """在文本中查找正则，命中则返回匹配片段（用于举证）。"""
    if not pattern or not text:
        return None
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0)[:120] if match else None


def match_rules(response, rules):
    """按规则匹配响应，返回命中列表。

    response 需包含 status/headers/body/cookies/title 字段。
    """
    headers = response.get("headers") or {}
    body = response.get("body") or ""
    cookies = response.get("cookies") or ""
    title = response.get("title") or ""

    hits = []
    for rule in rules:
        evidence = []

        for header, pattern in (rule.get("headers") or {}).items():
            found = _search(pattern, headers.get(header.lower()))
            if found:
                evidence.append("header {0} ~ {1}".format(header, found))

        for pattern in rule.get("body") or []:
            found = _search(pattern, body)
            if found:
                evidence.append("body ~ {0}".format(found))

        for pattern in rule.get("cookies") or []:
            found = _search(pattern, cookies)
            if found:
                evidence.append("cookie ~ {0}".format(found))

        for pattern in rule.get("title") or []:
            found = _search(pattern, title)
            if found:
                evidence.append("title ~ {0}".format(found))

        if evidence:
            hits.append({
                "name": rule.get("name", "unknown"),
                "category": rule.get("category", "unknown"),
                "evidence": evidence,
            })
    return hits


def fingerprint_url(url, rules=None, timeout=10, max_bytes=262144):
    """抓取 URL 并做指纹识别。失败时返回带 error 字段的结果而不抛异常。"""
    rules = rules if rules is not None else load_rules()
    status, headers, body, final_url, error = netutil.http_get(url, timeout=timeout, max_bytes=max_bytes)

    if error:
        return {"url": url, "status": None, "error": error, "matched": []}

    title = netutil.extract_title(body)
    response = {
        "status": status,
        "headers": headers,
        "body": body,
        "cookies": headers.get("set-cookie", ""),
        "title": title,
    }
    return {
        "url": url,
        "status": status,
        "final_url": final_url,
        "server": headers.get("server", ""),
        "title": title,
        "matched": match_rules(response, rules),
        "error": None,
    }
