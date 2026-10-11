"""reconkit 单元测试（全部离线，不发起真实网络请求）。"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reconkit import fingerprint, netutil, report, subdomain


def test_normalize_domain():
    assert netutil.normalize_domain("https://Sub.Example.com:8443/a/b?x=1") == "sub.example.com"
    assert netutil.normalize_domain("example.com.") == "example.com"
    assert netutil.normalize_domain("  EXAMPLE.COM  ") == "example.com"
    assert netutil.normalize_domain("") == ""
    assert netutil.normalize_domain("user@Example.com") == "example.com"


def test_is_ip():
    assert netutil.is_ip("192.168.1.1") is True
    assert netutil.is_ip("::1") is True
    assert netutil.is_ip("example.com") is False
    assert netutil.is_ip("") is False


def test_extract_title():
    assert netutil.extract_title("<html><head><title> Hello </title></head></html>") == "Hello"
    assert netutil.extract_title("<html>no title here</html>") == ""
    assert netutil.extract_title("") == ""
    assert netutil.extract_title("<TITLE>Upper</TITLE>") == "Upper"


def test_parse_crtsh_json_string():
    payload = json.dumps([
        {"name_value": "a.example.com\nb.example.com"},
        {"common_name": "*.example.com"},
        {"name_value": "other.org"},
    ])
    parsed = subdomain.parse_crtsh(payload)
    assert "a.example.com" in parsed
    assert "b.example.com" in parsed
    assert "other.org" in parsed


def test_parse_crtsh_invalid_input():
    assert subdomain.parse_crtsh("not json") == set()
    assert subdomain.parse_crtsh("{}") == set()
    assert subdomain.parse_crtsh("[]") == set()
    assert subdomain.parse_crtsh([{"name_value": None}]) == set()


def test_clean_names():
    names = {"a.example.com", "*.example.com", "example.com", "evil.com", "b.example.com"}
    assert subdomain.clean_names("example.com", names) == {"a.example.com", "b.example.com"}


def test_match_rules_hits():
    rules = [
        {"name": "Nginx", "category": "web-server", "headers": {"Server": "nginx(/[0-9.]+)?"}},
        {"name": "ThinkPHP", "category": "framework", "body": ["thinkphp"], "cookies": ["think_lang"]},
    ]
    response = {
        "status": 200,
        "headers": {"server": "nginx/1.24.0"},
        "body": "<p>Powered by ThinkPHP</p>",
        "cookies": "think_lang=zh-cn",
        "title": "",
    }
    hits = {hit["name"] for hit in fingerprint.match_rules(response, rules)}
    assert hits == {"Nginx", "ThinkPHP"}


def test_match_rules_empty():
    rules = [{"name": "Jenkins", "category": "ci", "headers": {"x-jenkins": "[0-9.]+"}}]
    response = {"status": 200, "headers": {}, "body": "", "cookies": "", "title": ""}
    assert fingerprint.match_rules(response, rules) == []


def test_match_rules_evidence_present():
    rules = [{"name": "Nginx", "category": "web-server", "headers": {"Server": "nginx"}}]
    response = {"status": 200, "headers": {"server": "nginx"}, "body": "", "cookies": "", "title": ""}
    hits = fingerprint.match_rules(response, rules)
    assert hits and hits[0]["evidence"]


def test_default_rules_loadable():
    rules = fingerprint.load_rules()
    assert len(rules) > 20
    for rule in rules:
        assert "name" in rule and "category" in rule


def test_report_table_alignment():
    rows = [{"a": "中文", "b": "x"}]
    table = report.render_table(rows, ["a", "b"])
    lines = table.splitlines()
    assert len(lines) == 3  # 表头 + 分隔线 + 1 行数据
    assert "中文" in lines[2]


def test_report_markdown_table():
    rows = [{"name": "Nginx", "category": "web-server"}]
    md = report.render_markdown_table(rows, ["name", "category"])
    assert md.splitlines()[0] == "| name | category |"
    assert "Nginx" in md


def test_report_json_keeps_chinese():
    payload = report.to_json({"k": "值"})
    assert json.loads(payload) == {"k": "值"}
    assert "值" in payload


def test_render_fingerprint_error_branch():
    text = report.render_fingerprint({"url": "http://x/", "error": "timeout"})
    assert "无法访问" in text


def test_render_subdomains_empty():
    assert report.render_subdomains([]) == "未发现子域名"


def test_enumerate_domain_shape_without_sources():
    """不启用任何数据源时，应返回结构化结果而不是空列表。"""
    result = subdomain.enumerate_domain("example.com", passive=False, wordlist=None)
    assert result["target"] == "example.com"
    assert result["records"] == []
    assert result["warnings"] == []


def test_enumerate_domain_reports_passive_failure():
    """被动源故障必须体现在 warnings 里，不能被当成"没有子域"。"""
    original = subdomain.from_crtsh
    subdomain.from_crtsh = lambda domain, timeout=30: {
        "names": set(),
        "error": "crt.sh 返回 HTTP 502，结果不可用",
    }
    try:
        result = subdomain.enumerate_domain("example.com", passive=True, timeout=1)
        assert len(result["warnings"]) == 1
        assert "502" in result["warnings"][0]
        assert result["records"] == []
    finally:
        subdomain.from_crtsh = original


def test_enumerate_domain_keeps_records_from_passive_source():
    """被动源正常时应把命中的子域带出来。"""
    original = subdomain.from_crtsh
    subdomain.from_crtsh = lambda domain, timeout=30: {"names": {"a.example.com"}, "error": None}
    original_resolve = netutil.resolve_host
    netutil.resolve_host = lambda host, timeout=3: ["203.0.113.9"]
    try:
        result = subdomain.enumerate_domain("example.com", passive=True, timeout=1)
        assert result["warnings"] == []
        assert [item["name"] for item in result["records"]] == ["a.example.com"]
        assert result["records"][0]["sources"] == ["crt.sh"]
    finally:
        subdomain.from_crtsh = original
        netutil.resolve_host = original_resolve
