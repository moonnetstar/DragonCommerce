# -*- coding: utf-8 -*-
"""
雙音符電商平台 — 多店買賣數量追蹤核心
不碰錢、不接支付。只記錄「哪個店、哪個商品、賣出幾件」。
平台內部表單（勞大看）：網站名稱 / 品名 / 價格 / 賣出數量
"""
from __future__ import annotations
import os
import json
import threading
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
# stores/ 與 core/ 同級；用 __file__ 往上一層再進 stores，跨平台/Render 都穩
STORES_DIR = os.path.normpath(os.path.join(BASE, "..", "stores"))
LOCK = threading.Lock()


def _now() -> str:
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


# ── 店鋪管理 ──────────────────────────────────────────

def list_stores() -> list[str]:
    if not os.path.exists(STORES_DIR):
        return []
    return [
        d for d in os.listdir(STORES_DIR)
        if os.path.isdir(os.path.join(STORES_DIR, d))
    ]


def get_store_config(store_id: str) -> dict:
    path = os.path.join(STORES_DIR, store_id, "store.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_products(store_id: str) -> list[dict]:
    path = os.path.join(STORES_DIR, store_id, "products.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_products(store_id: str, products: list[dict]):
    path = os.path.join(STORES_DIR, store_id, "products.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


def _sales_log_path(store_id: str) -> str:
    return os.path.join(STORES_DIR, store_id, "sales_log.json")


def load_sales_log(store_id: str) -> list[dict]:
    path = _sales_log_path(store_id)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 核心：記錄一筆賣出 ───────────────────────────────

def record_sale(store_id: str, product_id: str, qty: int = 1, method: str = "unknown") -> dict | None:
    """
    記錄某店某商品賣出 qty 件（不含付款處理）。
    回傳最新商品狀態，或 None（找不到/庫存不足）。
    method: 'linepay' | 'qrcode' | 'cod' | 'manual' | 'unknown'
    """
    with LOCK:
        products = load_products(store_id)
        for p in products:
            if str(p["id"]) == str(product_id):
                stock = p.get("stock", 0)
                if stock < qty:
                    return None
                p["stock"] = stock - qty
                _save_products(store_id, products)
                log = load_sales_log(store_id)
                for _ in range(qty):
                    log.append({
                        "store": store_id,
                        "id": product_id,
                        "name": p["name"],
                        "price": p["price"],
                        "method": method,
                        "time": _now(),
                    })
                with open(_sales_log_path(store_id), "w", encoding="utf-8") as f:
                    json.dump(log, f, ensure_ascii=False, indent=2)
                return p
        return None


# ── 平台總表（勞大專用）──────────────────────────────

def platform_report() -> dict:
    """
    彙總全平台：每店賣出數量 / 營收 / 商品明細。
    內部表單欄位：網站名稱 | 品名 | 價格 | 賣出數量
    """
    rows = []
    store_summ = {}
    for sid in list_stores():
        cfg = get_store_config(sid)
        store_name = cfg.get("name", sid)
        products = load_products(sid)
        sales = load_sales_log(sid)
        # 每件商品累計賣出
        sold_map = {}
        revenue_map = {}
        for s in sales:
            pid = s["id"]
            sold_map[pid] = sold_map.get(pid, 0) + 1
            revenue_map[pid] = revenue_map.get(pid, 0) + s.get("price", 0)
        store_total_sold = 0
        store_total_rev = 0
        for p in products:
            sold = sold_map.get(str(p["id"]), 0)
            rev = revenue_map.get(str(p["id"]), 0)
            store_total_sold += sold
            store_total_rev += rev
            rows.append({
                "store_id": sid,
                "store_name": store_name,
                "product_name": p["name"],
                "price": p["price"],
                "sold": sold,
                "revenue": rev,
            })
        store_summ[sid] = {
            "name": store_name,
            "total_sold": store_total_sold,
            "total_revenue": store_total_rev,
        }
    return {
        "rows": rows,
        "stores": store_summ,
        "generated_at": _now(),
    }


def print_platform_table() -> str:
    """純文字表格，方便直接看 / 推播。"""
    rep = platform_report()
    lines = ["📊 雙音符電商平台 — 買賣數量總表", f"生成時間：{rep['generated_at']}", ""]
    lines.append(f"{'網站名稱':<10}{'品名':<14}{'價格':>8}{'賣出':>6}")
    lines.append("-" * 40)
    for r in rep["rows"]:
        lines.append(f"{r['store_name']:<10}{r['product_name']:<14}{r['price']:>8}{r['sold']:>6}")
    lines.append("")
    lines.append("— 各店合計 —")
    for sid, s in rep["stores"].items():
        lines.append(f"{s['name']}: 賣出 {s['total_sold']} 件 / 營收 NT${s['total_revenue']:,}")
    return "\n".join(lines)
