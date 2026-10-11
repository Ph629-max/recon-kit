"""子域名枚举：证书透明度日志（被动） + 字典解析（主动）。"""

import concurrent.futures
import json
import urllib.parse

from . import netutil

CRTSH_URL = "https://crt.sh/?q=%25.{domain}&output=json"


def parse_crtsh(payload):
    """解析 crt.sh 返回内容，提取其中的域名。

    入参可以是 JSON 字符串或已解析的 list；格式异常时返回空集合而不抛错。
    """
    if isinstance(payload, str):
        try:
            payload = json.loads(payload or "[]")
        except ValueError:
            return set()
    if not isinstance(payload, list):
        return set()

    names = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        for field in ("name_value", "common_name"):
            value = item.get(field) or ""
            for line in str(value).splitlines():
                line = line.strip().lower()
                if line:
                    names.add(line)
    return names


def clean_names(domain, names):
    """只保留目标域的子域，去掉通配符、根域与无关域名。"""
    domain = (domain or "").lower().lstrip(".")
    result = set()
    for name in names:
        name = name.strip().lower().lstrip("*.").strip(".")
        if not name or name == domain:
            continue
        if name.endswith("." + domain):
            result.add(name)
    return result


def from_crtsh(domain, timeout=30):
    """查询证书透明度日志（crt.sh）。"""
    url = CRTSH_URL.format(domain=urllib.parse.quote(domain))
    status, _headers, body, _final, error = netutil.http_get(
        url, timeout=timeout, max_bytes=4 * 1024 * 1024
    )
    if error or status != 200:
        return set()
    return clean_names(domain, parse_crtsh(body))


def load_wordlist(path):
    """读取字典文件，忽略空行与 # 注释。"""
    words = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#"):
                words.append(line)
    return words


def brute(domain, words, threads=20, timeout=3):
    """按字典并发解析子域，返回 {子域名: [ip, ...]}。"""
    results = {}

    def check(word):
        host = "{0}.{1}".format(word, domain)
        return host, netutil.resolve_host(host, timeout=timeout)

    if not words:
        return results

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, threads)) as pool:
        for host, ips in pool.map(check, words):
            if ips:
                results[host] = ips
    return results


def enumerate_domain(domain, wordlist=None, passive=True, threads=20, timeout=3):
    """综合枚举：被动日志 + 可选字典，返回按名称排序的记录列表。"""
    domain = netutil.normalize_domain(domain)
    found = {}

    def bucket(name):
        if name not in found:
            found[name] = {"name": name, "sources": set(), "ips": []}
        return found[name]

    if passive:
        for name in from_crtsh(domain):
            bucket(name)["sources"].add("crt.sh")

    if wordlist:
        for host, ips in brute(domain, load_wordlist(wordlist), threads=threads, timeout=timeout).items():
            record = bucket(host)
            record["sources"].add("brute")
            record["ips"] = ips

    records = []
    for record in found.values():
        if not record["ips"]:
            record["ips"] = netutil.resolve_host(record["name"], timeout=timeout)
        records.append({
            "name": record["name"],
            "ips": record["ips"],
            "sources": sorted(record["sources"]),
        })
    return sorted(records, key=lambda item: item["name"])
