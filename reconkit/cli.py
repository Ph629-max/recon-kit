"""命令行入口。"""

import argparse
import sys

from . import __version__
from . import fingerprint as fp
from . import report
from . import subdomain

NOTICE = (
    "reconkit {0} - 轻量级资产侦察与指纹识别\n"
    "仅限用于自有资产或已获得书面授权的目标。使用前请确认授权范围。\n"
).format(__version__)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="reconkit",
        description="轻量级资产侦察与指纹识别工具（子域名枚举 / 技术栈识别）",
    )
    parser.add_argument("--version", action="version", version="reconkit " + __version__)
    sub = parser.add_subparsers(dest="command")

    p_sub = sub.add_parser("subdomains", help="子域名枚举（被动日志 + 可选字典）")
    p_sub.add_argument("domain", help="目标域名，如 example.com")
    p_sub.add_argument("--wordlist", help="字典文件路径")
    p_sub.add_argument("--no-passive", action="store_true", help="跳过证书透明度日志查询")
    p_sub.add_argument("--threads", type=int, default=20, help="并发线程数（默认 20）")
    p_sub.add_argument("--timeout", type=int, default=5, help="解析超时秒数（默认 5）")
    p_sub.add_argument("--json", action="store_true", help="以 JSON 输出")

    p_fp = sub.add_parser("fingerprint", help="识别目标技术栈")
    p_fp.add_argument("url", nargs="+", help="一个或多个 URL")
    p_fp.add_argument("--rules", help="自定义规则文件（JSON）")
    p_fp.add_argument("--timeout", type=int, default=10, help="请求超时秒数（默认 10）")
    p_fp.add_argument("--json", action="store_true", help="以 JSON 输出")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        print(NOTICE)
        parser.print_help()
        return 0

    if args.command == "subdomains":
        result = subdomain.enumerate_domain(
            args.domain,
            wordlist=args.wordlist,
            passive=not args.no_passive,
            threads=args.threads,
            timeout=args.timeout,
        )
        if args.json:
            print(report.to_json(result))
        else:
            for warning in result["warnings"]:
                print("[!] " + warning)
            print("目标: {0}    发现子域: {1}".format(result["target"], len(result["records"])))
            print(report.render_subdomains(result["records"]))
        return 0

    if args.command == "fingerprint":
        rules = fp.load_rules(args.rules) if args.rules else None
        results = [fp.fingerprint_url(url, rules=rules, timeout=args.timeout) for url in args.url]
        if args.json:
            print(report.to_json(results))
        else:
            for result in results:
                print(report.render_fingerprint(result))
                print("")
        return 0

    parser.print_help()
    return 1
