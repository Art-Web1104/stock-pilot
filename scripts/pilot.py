#!/usr/bin/env python3
"""stock-pilot core engine.

세션(Claude)이 웹에서 가져온 시세를 넘겨주면, 이 스크립트가 결정적(deterministic)인
상태 관리를 담당한다: 가격 기록, 모의매매 손익 계산, 2주 검증 판정, 신호 생성,
대시보드 데이터 빌드.

사용법:
  python3 scripts/pilot.py record-prices   < prices.json
  python3 scripts/pilot.py open-trade      < trade.json
  python3 scripts/pilot.py evaluate
  python3 scripts/pilot.py process-control
  python3 scripts/pilot.py dashboard
  python3 scripts/pilot.py status
모든 명령은 저장소 루트에서 실행한다. 결과 요약을 JSON으로 stdout에 출력한다.
"""
import json
import sys
import os
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = timezone(timedelta(hours=9))


def now_kst():
    return datetime.now(KST)


def today():
    return now_kst().strftime("%Y-%m-%d")


def load(path, default):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(path, obj):
    p = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def config():
    return load("config.json", {})


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- prices

def record_prices():
    """stdin: [{"code","name","open","high","low","close","date"?}]  (date 생략 시 오늘)"""
    rows = json.load(sys.stdin)
    recorded = []
    for r in rows:
        code = str(r["code"]).zfill(6)
        date = r.get("date") or today()
        hist = load(f"data/price_history/{code}.json", {"code": code, "name": r.get("name", code), "rows": []})
        hist["name"] = r.get("name", hist.get("name", code))
        hist["rows"] = [x for x in hist["rows"] if x["date"] != date]
        hist["rows"].append({
            "date": date,
            "open": r.get("open"), "high": r.get("high"),
            "low": r.get("low"), "close": r["close"],
        })
        hist["rows"].sort(key=lambda x: x["date"])
        hist["rows"] = hist["rows"][-260:]  # 최근 1년치만 유지
        save(f"data/price_history/{code}.json", hist)
        recorded.append(code)

    # 보유 중인 모의매매에 최신 가격 반영
    pt = load("data/paper_trades.json", {"trades": []})
    price_map = {str(r["code"]).zfill(6): r for r in rows}
    updated = []
    for t in pt["trades"]:
        if t["status"] != "open":
            continue
        r = price_map.get(t["code"])
        if not r:
            continue
        date = r.get("date") or today()
        ret = round((r["close"] - t["entry_price"]) / t["entry_price"] * 100, 2)
        t["history"] = [h for h in t.get("history", []) if h["date"] != date]
        t["history"].append({"date": date, "close": r["close"], "return_pct": ret})
        t["history"].sort(key=lambda x: x["date"])
        t["last_price"] = r["close"]
        t["return_pct"] = ret
        t["days_held"] = len(t["history"])
        t["max_return_pct"] = max(t.get("max_return_pct", ret), ret)
        t["min_return_pct"] = min(t.get("min_return_pct", ret), ret)
        # 장중 고가/저가로 목표/손절 터치 여부 추정
        if r.get("high") is not None:
            hi = round((r["high"] - t["entry_price"]) / t["entry_price"] * 100, 2)
            t["max_return_pct"] = max(t["max_return_pct"], hi)
        if r.get("low") is not None:
            lo = round((r["low"] - t["entry_price"]) / t["entry_price"] * 100, 2)
            t["min_return_pct"] = min(t["min_return_pct"], lo)
        updated.append(t["code"])
    pt["updated"] = now_kst().isoformat()
    save("data/paper_trades.json", pt)
    out({"recorded": recorded, "trades_updated": updated})


# ---------------------------------------------------------------- trades

def open_trade():
    """stdin: {"code","name","entry_price","thesis","sector"?,"analyses"?:{...}}"""
    cfg = config()
    v = cfg.get("verification", {})
    lim = cfg.get("limits", {})
    req = json.load(sys.stdin)
    code = str(req["code"]).zfill(6)
    pt = load("data/paper_trades.json", {"trades": []})

    open_trades = [t for t in pt["trades"] if t["status"] == "open"]
    if any(t["code"] == code for t in open_trades):
        out({"ok": False, "reason": f"{code} 이미 검증 진행 중"})
        return
    if len(open_trades) >= lim.get("max_open_trades", 10):
        out({"ok": False, "reason": "최대 동시 검증 종목 수 초과"})
        return
    opened_today = [t for t in pt["trades"] if t.get("opened") == today()]
    if len(opened_today) >= lim.get("max_new_entries_per_day", 2):
        out({"ok": False, "reason": "오늘 신규 편입 한도 초과"})
        return
    if code in cfg.get("universe", {}).get("exclude_codes", []):
        out({"ok": False, "reason": f"{code} 사용자 제외 종목"})
        return

    entry = req["entry_price"]
    t = {
        "id": f"{code}-{today()}",
        "code": code,
        "name": req["name"],
        "sector": req.get("sector"),
        "opened": today(),
        "entry_price": entry,
        "target_pct": v.get("target_pct", 7.0),
        "stop_pct": v.get("stop_pct", -5.0),
        "status": "open",
        "days_held": 1,
        "last_price": entry,
        "return_pct": 0.0,
        "max_return_pct": 0.0,
        "min_return_pct": 0.0,
        "closed": None,
        "close_reason": None,
        "history": [{"date": today(), "close": entry, "return_pct": 0.0}],
        "thesis": req.get("thesis", ""),
        "analyses": req.get("analyses", {}),
    }
    pt["trades"].append(t)
    pt["updated"] = now_kst().isoformat()
    save("data/paper_trades.json", pt)
    out({"ok": True, "opened": t["id"], "entry_price": entry})


def evaluate():
    """2주(거래일 기준) 검증 판정. 목표 도달→조기 통과, 손절 터치→조기 탈락,
    기간 만료 시 pass_threshold 이상이면 통과."""
    cfg = config()
    v = cfg.get("verification", {})
    days = v.get("trading_days", 10)
    target = v.get("target_pct", 7.0)
    stop = v.get("stop_pct", -5.0)
    threshold = v.get("pass_threshold_pct", 3.0)

    pt = load("data/paper_trades.json", {"trades": []})
    sig = load("data/signals.json", {"signals": []})
    verdicts = []

    for t in pt["trades"]:
        if t["status"] != "open":
            continue
        verdict = None
        if t.get("max_return_pct", 0) >= target:
            verdict = ("passed", f"목표 수익률 {target}% 도달 (최고 {t['max_return_pct']}%)")
        elif t.get("min_return_pct", 0) <= stop:
            verdict = ("failed", f"손절선 {stop}% 터치 (최저 {t['min_return_pct']}%)")
        elif t["days_held"] >= days:
            if t["return_pct"] >= threshold:
                verdict = ("passed", f"{days}거래일 경과, 수익률 {t['return_pct']}% ≥ 기준 {threshold}%")
            else:
                verdict = ("failed", f"{days}거래일 경과, 수익률 {t['return_pct']}% < 기준 {threshold}%")
        if not verdict:
            continue
        status, reason = verdict
        t["status"] = status
        t["closed"] = today()
        t["close_reason"] = reason
        verdicts.append({"code": t["code"], "name": t["name"], "verdict": status,
                         "reason": reason, "return_pct": t["return_pct"]})
        if status == "passed":
            sig["signals"] = [s for s in sig["signals"]
                              if not (s["code"] == t["code"] and s["status"] == "active")]
            sig["signals"].append({
                "id": f"sig-{t['code']}-{today()}",
                "date": today(),
                "type": "buy",
                "code": t["code"],
                "name": t["name"],
                "ref_price": t["last_price"],
                "verification": {
                    "entry_price": t["entry_price"],
                    "days_held": t["days_held"],
                    "return_pct": t["return_pct"],
                    "max_return_pct": t["max_return_pct"],
                    "min_return_pct": t["min_return_pct"],
                    "reason": reason,
                },
                "thesis": t.get("thesis", ""),
                "status": "active",
            })

    pt["updated"] = now_kst().isoformat()
    sig["updated"] = now_kst().isoformat()
    save("data/paper_trades.json", pt)
    save("data/signals.json", sig)
    out({"verdicts": verdicts,
         "open_count": len([t for t in pt["trades"] if t["status"] == "open"]),
         "active_signals": len([s for s in sig["signals"] if s["status"] == "active"])})


# ---------------------------------------------------------------- control

def process_control():
    """대시보드/사용자 명령 처리.
    exclude: 종목 영구 제외(진행 중 검증도 중단), dismiss: 신호 무시, approve: 신호 완료 처리"""
    cfg = config()
    ctl = load("data/control.json", {"commands": []})
    pt = load("data/paper_trades.json", {"trades": []})
    sig = load("data/signals.json", {"signals": []})
    processed = []

    for c in ctl["commands"]:
        if c.get("processed"):
            continue
        action = c.get("action")
        code = str(c.get("code", "")).zfill(6) if c.get("code") else None
        if action == "exclude" and code:
            ex = cfg.setdefault("universe", {}).setdefault("exclude_codes", [])
            if code not in ex:
                ex.append(code)
            for t in pt["trades"]:
                if t["code"] == code and t["status"] == "open":
                    t["status"] = "excluded"
                    t["closed"] = today()
                    t["close_reason"] = "사용자 제외"
            for s in sig["signals"]:
                if s["code"] == code and s["status"] == "active":
                    s["status"] = "dismissed"
        elif action == "dismiss" and code:
            for s in sig["signals"]:
                if s["code"] == code and s["status"] == "active":
                    s["status"] = "dismissed"
        elif action == "approve" and code:
            for s in sig["signals"]:
                if s["code"] == code and s["status"] == "active":
                    s["status"] = "done"
                    s["approved"] = today()
        c["processed"] = True
        c["processed_at"] = now_kst().isoformat()
        processed.append({"action": action, "code": code})

    save("config.json", cfg)
    save("data/control.json", ctl)
    save("data/paper_trades.json", pt)
    save("data/signals.json", sig)
    out({"processed": processed})


# ---------------------------------------------------------------- dashboard

def latest_analysis(kind):
    d = os.path.join(ROOT, "data", kind)
    if not os.path.isdir(d):
        return None
    files = sorted(f for f in os.listdir(d) if f.endswith(".json"))
    if not files:
        return None
    return load(f"data/{kind}/{files[-1]}", None)


def dashboard():
    pt = load("data/paper_trades.json", {"trades": []})
    sig = load("data/signals.json", {"signals": []})
    closed = [t for t in pt["trades"] if t["status"] in ("passed", "failed")]
    wins = [t for t in closed if t["status"] == "passed"]
    payload = {
        "generated": now_kst().isoformat(),
        "market": latest_analysis("market_analysis"),
        "company": latest_analysis("company_analysis"),
        "chart": latest_analysis("chart_analysis"),
        "open_trades": [t for t in pt["trades"] if t["status"] == "open"],
        "signals": [s for s in sig["signals"] if s["status"] == "active"],
        "recent_closed": sorted(closed, key=lambda t: t.get("closed") or "", reverse=True)[:15],
        "stats": {
            "total_verified": len(closed),
            "passed": len(wins),
            "win_rate": round(len(wins) / len(closed) * 100, 1) if closed else None,
            "avg_return_passed": round(sum(t["return_pct"] for t in wins) / len(wins), 2) if wins else None,
        },
    }
    save("docs/data.json", payload)
    out({"ok": True, "open": len(payload["open_trades"]), "signals": len(payload["signals"])})


def status():
    pt = load("data/paper_trades.json", {"trades": []})
    sig = load("data/signals.json", {"signals": []})
    out({
        "open_trades": [{"code": t["code"], "name": t["name"], "days": t["days_held"],
                         "return_pct": t["return_pct"]} for t in pt["trades"] if t["status"] == "open"],
        "active_signals": [{"code": s["code"], "name": s["name"], "date": s["date"]}
                           for s in sig["signals"] if s["status"] == "active"],
        "tracked_codes": sorted(set(
            [t["code"] for t in pt["trades"] if t["status"] == "open"] +
            [s["code"] for s in sig["signals"] if s["status"] == "active"])),
    })


COMMANDS = {
    "record-prices": record_prices,
    "open-trade": open_trade,
    "evaluate": evaluate,
    "process-control": process_control,
    "dashboard": dashboard,
    "status": status,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"usage: pilot.py [{'|'.join(COMMANDS)}]", file=sys.stderr)
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
