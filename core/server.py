# -*- coding: utf-8 -*-
"""
雙音符電商平台 — 統計中心 API
提供勞大專用的簡單買賣表：網站名稱 / 品名 / 價格 / 賣出數量
不處理付款，只統計。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from flask import Flask, jsonify, request
import tracker

app = Flask(__name__)


@app.route("/healthz", methods=["GET"])
def health():
    return jsonify({"services": "DragonCommerce stats running", "stores": tracker.list_stores()}), 200


@app.route("/admin/report", methods=["GET"])
def report():
    """平台總表（JSON）。"""
    rep = tracker.platform_report()
    return jsonify(rep), 200


@app.route("/admin/report/text", methods=["GET"])
def report_text():
    """平台總表（純文字，方便推播/印出）。"""
    return tracker.print_platform_table(), 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/sdk.js", methods=["GET"])
def serve_sdk():
    """提供 DragonCommerce SDK 給合作方前端嵌入。"""
    with open(os.path.join(os.path.dirname(__file__), "sdk.js"), "r", encoding="utf-8") as f:
        return f.read(), 200, {"Content-Type": "application/javascript; charset=utf-8"}


@app.route("/track/sale", methods=["POST"])
def track_sale():
    """記錄一筆賣出。合作方前台結帳後呼叫。"""
    data = request.get_json(silent=True) or {}
    sid = data.get("store")
    pid = str(data.get("id", ""))
    qty = int(data.get("qty", 1))
    method = data.get("method", "unknown")
    api_key = data.get("api_key", "")

    if not sid or not pid or qty <= 0:
        return jsonify({"error": "missing store/id/qty"}), 400

    # api_key 認證
    cfg = tracker.get_store_config(sid)
    if not cfg or cfg.get("api_key") != api_key:
        return jsonify({"error": "invalid api_key"}), 403

    res = tracker.record_sale(sid, pid, qty, method)
    if res is None:
        return jsonify({"error": "product not found or stock insufficient"}), 404
    return jsonify({"ok": True, "store": sid, "stock": res["stock"], "sold": qty}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8082"))
    app.run(host="0.0.0.0", port=port)
