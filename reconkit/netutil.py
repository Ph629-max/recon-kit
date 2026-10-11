"""网络与 HTTP 基础工具。"""

import ipaddress
import socket
import urllib.error
import urllib.request
from urllib.parse import urlparse

DEFAULT_UA = "reconkit/0.1 (+https://github.com/Ph629-max/recon-kit)"
DEFAULT_TIMEOUT = 10


def normalize_domain(value):
    """把用户输入统一成裸域名：去掉协议、路径、端口、尾部点。"""
    if not value:
        return ""
    text = value.strip()
    if "://" in text:
        text = urlparse(text).netloc
    if "/" in text:
        text = text.split("/", 1)[0]
    if "@" in text:
        text = text.split("@", 1)[1]
    if ":" in text and not text.startswith("["):
        text = text.split(":", 1)[0]
    return text.strip().strip(".").lower()


def is_ip(value):
    """判断字符串是否为合法 IP。"""
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def resolve_host(host, timeout=3):
    """解析主机名，返回去重排序后的 IP 列表；失败返回空列表。"""
    previous = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError, OSError):
        return []
    finally:
        socket.setdefaulttimeout(previous)
    return sorted({info[4][0] for info in infos})


def http_get(url, timeout=DEFAULT_TIMEOUT, ua=DEFAULT_UA, max_bytes=262144):
    """发起 GET 请求。

    返回 (status, headers, body, final_url, error)。
    批量扫描场景下不抛异常，失败信息统一走 error 返回。
    """
    request = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(max_bytes)
            charset = response.headers.get_content_charset() or "utf-8"
            body = raw.decode(charset, errors="replace")
            headers = {key.lower(): value for key, value in response.headers.items()}
            return response.status, headers, body, response.geturl(), None
    except urllib.error.HTTPError as exc:
        raw = b""
        try:
            raw = exc.read(max_bytes)
        except Exception:
            raw = b""
        body = raw.decode("utf-8", errors="replace") if raw else ""
        headers = {}
        if exc.headers:
            headers = {key.lower(): value for key, value in exc.headers.items()}
        return exc.code, headers, body, url, None
    except Exception as exc:  # noqa: BLE001 - 批量场景需要吞掉所有网络异常
        return None, {}, "", url, str(exc)


def extract_title(html):
    """从 HTML 中粗略提取 title 文本。"""
    if not html:
        return ""
    lowered = html.lower()
    start = lowered.find("<title")
    if start < 0:
        return ""
    start = lowered.find(">", start)
    end = lowered.find("</title>", start)
    if start < 0 or end < 0:
        return ""
    return html[start + 1:end].strip()[:200]
