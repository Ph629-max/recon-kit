"""端到端冒烟测试：本地起 HTTP 服务，验证指纹识别链路（不访问外网）。"""

import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from reconkit import fingerprint, report

BODY = (
    "<html><head><title>Demo Console</title></head><body>"
    "<script src='/static/js/vue.min.js'></script>"
    "<p>Powered by ThinkPHP</p></body></html>"
).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Server", "nginx/1.24.0")
        self.send_header("X-Powered-By", "PHP/8.1.2")
        self.send_header("Set-Cookie", "think_lang=zh-cn; path=/")
        self.end_headers()
        self.wfile.write(BODY)

    def log_message(self, *args):
        pass


server = HTTPServer(("127.0.0.1", 0), Handler)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()

try:
    result = fingerprint.fingerprint_url("http://127.0.0.1:{0}/".format(port))
    print(report.render_fingerprint(result))
    print("")
    print("MATCHED = " + ", ".join(item["name"] for item in result["matched"]))
    print("REPORT_JSON_BYTES = {0}".format(len(report.to_json(result))))
finally:
    server.shutdown()
