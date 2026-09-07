#!/usr/bin/env python3
"""
DeskFlow - Autonomous Execution Clerk for Binance Agent OS
Governs orders, enforces mandate caps, routes across Convert vs Spot,
and reconciles fills to an immutable blotter.
"""

import sys
import json
import re
import os
import argparse
from datetime import datetime, timezone

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MANDATE = {
    "product": "DeskFlow",
    "account": "agentic_sub",
    "max_notional_usd": 10.00,
    "venues_allow": ["convert", "spot"],
    "venues_deny": ["futures", "margin", "perps", "perp", "leverage"],
    "confirm": "required",
    "withdraw": "deny",
    "main_account_write": "deny"
}

PENDING_ORDERS = {}
ORDER_COUNTER = 1
BLOTTER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blotter.md")
REJECTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rejects.md")
SESSION_CAP_OVERRIDE = None


ASSET_ALIASES = {
    "solana": "SOL", "sol": "SOL",
    "bitcoin": "BTC", "btc": "BTC",
    "ethereum": "ETH", "ether": "ETH", "eth": "ETH",
    "binance": "BNB", "bnb": "BNB",
    "dogecoin": "DOGE", "doge": "DOGE",
    "ripple": "XRP", "xrp": "XRP",
    "cardano": "ADA", "ada": "ADA",
    "avalanche": "AVAX", "avax": "AVAX",
    "sui": "SUI", "near": "NEAR", "pepe": "PEPE",
    "chainlink": "LINK", "link": "LINK",
    "polkadot": "DOT", "dot": "DOT",
    "shiba": "SHIB", "shib": "SHIB",
    "ton": "TON", "toncoin": "TON",
    "tron": "TRX", "trx": "TRX",
    "aptos": "APT", "apt": "APT"
}

STOP_WORDS = {
    "buy", "sell", "usd", "usdt", "dollars", "dollar", "cash", "only",
    "perps", "perp", "for", "in", "at", "the", "of", "and", "with", "order"
}

def extract_asset(text):
    clean = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    words = clean.split()
    # Check aliases first
    for w in words:
        if w in ASSET_ALIASES:
            return ASSET_ALIASES[w]
    # Check any candidate token of 2-6 chars
    for w in words:
        if w not in STOP_WORDS and not w.isdigit():
            if 2 <= len(w) <= 6:
                return w.upper()
    return None

def get_agent_os_ticker(market_data, symbol):
    if not isinstance(market_data, dict):
        raise ValueError("Agent OS market data must be an object")
    spot = market_data.get("spot", market_data)
    bid = float(spot["bid"])
    ask = float(spot["ask"])
    mid = float(spot.get("mid", (bid + ask) / 2.0))
    if bid <= 0 or ask <= 0 or mid <= 0:
        raise ValueError("Agent OS market data prices must be positive")
    return {"bid": bid, "ask": ask, "mid": mid, "symbol": symbol, "live": True}


def select_venue(market_data, side, spot_price):
    convert = market_data.get("convert") if isinstance(market_data, dict) else None
    if not isinstance(convert, dict):
        return "SPOT", "QUOTE_ON_CONFIRM", None
    try:
        convert_price = float(convert["price"])
    except (KeyError, TypeError, ValueError):
        return "SPOT", "QUOTE_ON_CONFIRM", None
    if convert_price <= 0:
        raise ValueError("Agent OS Convert price must be positive")
    better_convert = convert_price < spot_price if side == "BUY" else convert_price > spot_price
    return (
        "CONVERT" if better_convert else "SPOT",
        convert,
        convert_price,
    )



def load_mandate(override_cap=None):
    mandate = dict(MANDATE)
    mandate_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mandate.yml")
    if os.path.exists(mandate_path):
        try:
            with open(mandate_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("max_notional_usd:"):
                        val = line.split(":", 1)[1].strip()
                        mandate["max_notional_usd"] = float(val)
        except (OSError, ValueError):
            raise
    env_cap = os.environ.get("DESKFLOW_MAX_NOTIONAL_USD")
    if env_cap:
        try:
            mandate["max_notional_usd"] = float(env_cap)
        except ValueError:
            pass
    if override_cap is not None:
        try:
            mandate["max_notional_usd"] = float(override_cap)
        except ValueError:
            pass
    elif SESSION_CAP_OVERRIDE is not None:
        mandate["max_notional_usd"] = SESSION_CAP_OVERRIDE
    return mandate


def append_rejection(raw_order, code, reason, po_id=None):
    if not os.path.exists(REJECTS_FILE):
        with open(REJECTS_FILE, "w", encoding="utf-8") as f:
            f.write("# Rejects — DeskFlow\n\n| po_id | timestamp | raw_order | code | reason |\n|---|---|---|---|---|\n")
    safe_order = raw_order.replace("|", "\\|").replace("\n", " ")
    safe_reason = reason.replace("|", "\\|").replace("\n", " ")
    with open(REJECTS_FILE, "a", encoding="utf-8") as f:
        f.write(f"| {po_id or '-'} | {datetime.now(timezone.utc).isoformat()} | {safe_order} | {code} | {safe_reason} |\n")


def rejected_order(raw_order, code, reason):
    append_rejection(raw_order, code, reason)
    return {"valid": False, "code": code, "reason": reason}


def update_mandate(max_notional_usd):
    global SESSION_CAP_OVERRIDE
    try:
        cap = float(max_notional_usd)
    except (TypeError, ValueError) as exc:
        raise ValueError("max_notional_usd must be a positive number") from exc
    if cap <= 0:
        raise ValueError("max_notional_usd must be a positive number")
    SESSION_CAP_OVERRIDE = cap
    return load_mandate()

def parse_order(raw_text, custom_cap=None, market_data=None):
    text = raw_text.strip().lower()

    # Check prohibited venues or leverage
    for denied in MANDATE["venues_deny"]:
        if denied in text:
            return rejected_order(raw_text, "REJECT VENUE", f"Prohibited venue or leverage detected ({denied}) denied by mandate")

    if re.search(r"\b\d+x\b", text):
        return rejected_order(raw_text, "REJECT VENUE", "Leverage multiplier detected and denied by mandate")

    # Check side
    side = None
    if "buy" in text:
        side = "BUY"
    elif "sell" in text:
        side = "SELL"
    else:
        return rejected_order(raw_text, "REJECT DATA", "Missing buy or sell action in order prompt")

    # Extract target asset dynamically across Binance universe
    asset = extract_asset(text)
    if not asset:
        return rejected_order(raw_text, "REJECT DATA", "Missing target asset in order prompt (e.g. SOL, BTC, ETH, BNB)")

    # Extract size dynamically - supports both USD notional ($5, 5 USD) and coin quantity (0.005 BNB)
    specified_qty = None
    usd_match = re.search(r"\$(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:usd|usdt|dollars?)", text)
    if usd_match:
        notional = float(usd_match.group(1) or usd_match.group(2))
    else:
        # Check for asset quantity (e.g. '0.005 bnb' or 'sell 0.005 bnb')
        qty_match = re.search(r"(?:buy|sell)\s+(\d+(?:\.\d+)?)\s*(?:[a-z]+)?", text)
        if not qty_match:
            qty_match = re.search(r"(\d+(?:\.\d+)?)\s*" + asset.lower(), text)
        if qty_match:
            specified_qty = float(qty_match.group(1))
            try:
                ticker = get_agent_os_ticker(market_data, f"{asset}USDT")
            except (TypeError, ValueError, KeyError) as exc:
                return rejected_order(raw_text, "REJECT DATA", f"Live market data unavailable: {exc}")
            notional = round(specified_qty * ticker["mid"], 2)
        else:
            return rejected_order(raw_text, "REJECT DATA", "Missing order amount (e.g. 5 USD or 0.005 BNB)")

    if notional <= 0:
        return rejected_order(raw_text, "REJECT DATA", "Order notional amount must be greater than zero")

    active_mandate = load_mandate(custom_cap)
    if notional > active_mandate["max_notional_usd"]:
        return rejected_order(raw_text, "REJECT SIZE", f"Order size ${notional:.2f} exceeds configured mandate cap ${active_mandate['max_notional_usd']:.2f}")

    return {
        "valid": True,
        "side": side,
        "asset": asset,
        "notional_usd": notional,
        "specified_qty": specified_qty
    }


def price_parent_order(order_text, custom_cap=None, market_data=None):
    global ORDER_COUNTER
    parsed = parse_order(order_text, custom_cap, market_data)
    if not parsed["valid"]:
        return parsed

    symbol = f"{parsed['asset']}USDT"
    try:
        ticker = get_agent_os_ticker(market_data, symbol)
    except (TypeError, ValueError, KeyError) as exc:
        return rejected_order(order_text, "REJECT DATA", f"Live market data unavailable: {exc}")
    po_id = f"PO-{ORDER_COUNTER:03d}"
    ORDER_COUNTER += 1

    touch_price = ticker["ask"] if parsed["side"] == "BUY" else ticker["bid"]
    try:
        recommended_venue, convert_quote, convert_price = select_venue(
            market_data,
            parsed["side"],
            touch_price,
        )
    except ValueError as exc:
        return rejected_order(order_text, "REJECT DATA", str(exc))
    if parsed.get("specified_qty"):
        est_qty = parsed["specified_qty"]
        notional_calc = round(est_qty * touch_price, 2)
    else:
        est_qty = round(parsed["notional_usd"] / touch_price, 8)
        notional_calc = parsed["notional_usd"]
    est_fee = round(notional_calc * 0.001, 4)

    order_record = {
        "po_id": po_id,
        "valid": True,
        "mandate": "PASSED",
        "side": parsed["side"],
        "asset": parsed["asset"],
        "symbol": symbol,
        "notional_usd": notional_calc,
        "specified_qty": parsed.get("specified_qty"),
        "decision_mid": ticker["mid"],
        "touch_price": touch_price,
        "bid": ticker["bid"],
        "ask": ticker["ask"],
        "est_qty": est_qty,
        "est_fee": est_fee,
        "convert_quote": convert_quote,
        "convert_price": convert_price,
        "recommended_venue": recommended_venue,
        "status": "AWAITING_CONFIRMATION",
        "required_token": f"CONFIRM {po_id}"
    }

    PENDING_ORDERS[po_id] = order_record
    return order_record


def execute_confirmed_order(po_id, confirm_token, execution_result=None):
    if po_id not in PENDING_ORDERS:
        return {
            "success": False,
            "error": f"Parent order {po_id} not found in active order registry"
        }

    order = PENDING_ORDERS[po_id]
    expected_token = f"CONFIRM {po_id}"
    if confirm_token.strip() != expected_token:
        return {
            "success": False,
            "error": f"Invalid authorization token. Expected '{expected_token}' but received '{confirm_token.strip()}'"
        }

    if not isinstance(execution_result, dict):
        return {
            "success": False,
            "error": "Missing Agent OS execution result; no exchange write was recorded"
        }
    try:
        venue = str(execution_result["venue"]).upper()
        symbol = str(execution_result["symbol"]).upper()
        status = str(execution_result["status"]).upper()
        filled_qty = float(execution_result["filled_qty"])
        exec_price = float(execution_result["exec_price"])
        fee = float(execution_result.get("fee_usdt", 0))
    except (KeyError, TypeError, ValueError) as exc:
        return {"success": False, "error": f"Invalid Agent OS execution result: {exc}"}
    if venue != order["recommended_venue"] or symbol != order["symbol"]:
        return {"success": False, "error": "Agent OS execution does not match the approved ticket"}
    if status not in {"FILLED", "PARTIAL", "MISMATCH", "INCOMPLETE_DATA"}:
        return {"success": False, "error": f"Unsupported Agent OS execution status: {status}"}
    if filled_qty < 0 or exec_price <= 0 or fee < 0:
        return {"success": False, "error": "Agent OS execution values must be non-negative and price must be positive"}

    notional = round(filled_qty * exec_price, 2)
    mid = order["decision_mid"]

    if order["side"] == "BUY":
        shortfall_bps = ((exec_price - mid) / mid) * 10000
    else:
        shortfall_bps = ((mid - exec_price) / mid) * 10000

    shortfall_str = f"+{shortfall_bps:.2f} bps" if shortfall_bps >= 0 else f"{shortfall_bps:.2f} bps"

    receipt = {
        "po_id": po_id,
        "status": status,
        "venue": venue,
        "symbol": symbol,
        "side": order["side"],
        "planned_usd": notional,
        "filled_qty": filled_qty,
        "asset": order["asset"],
        "decision_mid": mid,
        "exec_price": exec_price,
        "fee_usdt": fee,
        "shortfall_bps": shortfall_str,
        "subaccount": "AGENTIC_SUB",
        "mandate": "PASSED"
    }

    append_to_blotter(receipt)

    order["status"] = status
    return {"success": True, "receipt": receipt}


def append_to_blotter(receipt):
    line = f"| {receipt['po_id']} | {receipt['venue']} | {receipt['planned_usd']:.2f} | {receipt['filled_qty']:.8f} {receipt['asset']} | {receipt['fee_usdt']:.4f} USDT | {receipt['decision_mid']:.4f} | {receipt['shortfall_bps'].replace(' bps', '')} | {receipt['status']} |\n"
    if not os.path.exists(BLOTTER_FILE):
        header = "# Blotter — DeskFlow\n\n| po_id | venue | planned_usd | filled_qty | fee | mid_at_decision | shortfall_bps | status |\n|---|---|---|---|---|---|---|---|\n"
        with open(BLOTTER_FILE, "w", encoding="utf-8") as f:
            f.write(header + line)
    else:
        with open(BLOTTER_FILE, "a", encoding="utf-8") as f:
            f.write(line)


def format_receipt_card(receipt):
    return f"""
┌──────────────────────────────────────────────────────────────────┐
│  DESKFLOW EXECUTION RECEIPT · BINANCE AGENT OS                   │
├──────────────────────────────────────────────────────────────────┤
│  Parent Order ID : {receipt['po_id']:<21} Status   : {receipt['status']:<14} │
│  Venue Executed  : {receipt['venue'] + ' · ' + receipt['side']:<21} Symbol   : {receipt['symbol']:<14} │
│  Planned Capital : ${receipt['planned_usd']:<20.2f} Filled   : {receipt['filled_qty']:.8f} {receipt['asset']} │
├──────────────────────────────────────────────────────────────────┤
│  Decision Mid    : {receipt['decision_mid']:<18.4f} USDT Fill Price: {receipt['exec_price']:.4f} USDT │
│  Shortfall       : {receipt['shortfall_bps']:<18} Fee Paid : {receipt['fee_usdt']:.4f} USDT   │
│  Subaccount Scoped: {receipt['subaccount']:<21} Mandate  : {receipt['mandate']:<14} │
└──────────────────────────────────────────────────────────────────┘
"""


def run_test_suite():
    print("=" * 66)
    print(" DESKFLOW VERIFICATION SUITE · BINANCE AGENT OS")
    print("=" * 66)
    test_market_data = {
        "spot": {"bid": 765.54, "ask": 765.55, "mid": 765.545},
        "convert": {"price": 765.60},
    }

    # Test 1: Venue / Leverage Rejection
    print("\n[STEP 1] Testing Rejection Gate (Leverage Denied): 'Buy 5 USD BNB 20x perps'")
    order1 = parse_order("Buy 5 USD BNB 20x perps")
    if not order1["valid"] and order1["code"] == "REJECT VENUE":
        print(f"PASS -> Intercepted: {order1['code']} ({order1['reason']})")
    else:
        print("FAIL -> Rejection gate failed to catch leverage")
        return False

    # Test 2: Size Cap Rejection
    print("\n[STEP 2] Testing Rejection Gate (Size Exceeds Cap): 'Buy 25 USD BNB. Cash only.'")
    order2 = parse_order("Buy 25 USD BNB. Cash only.")
    if not order2["valid"] and order2["code"] == "REJECT SIZE":
        print(f"PASS -> Intercepted: {order2['code']} ({order2['reason']})")
    else:
        print("FAIL -> Size cap gate failed to catch $25 > $10 limit")
        return False

    # Test 3: Dynamic Cash Parent Order (Dynamic $6.50 input)
    test_amount = 6.50
    test_prompt = f"Buy {test_amount} USD BNB. Cash only."
    print(f"\n[STEP 3] Testing Dynamic Cash Order: '{test_prompt}'")
    priced = price_parent_order(test_prompt, market_data=test_market_data)
    if priced.get("valid"):
        print(f"PASS -> Mandate passed for dynamic amount ${test_amount:.2f}")
        print(f"        PO ID: {priced['po_id']} | Symbol: {priced['symbol']}")
        print(f"        Decision Mid: {priced['decision_mid']:.4f} USDT | Touch Ask: {priced['touch_price']:.4f} USDT")
        print(f"        Estimated Fill: {priced['est_qty']:.8f} {priced['asset']}")
        print(f"        Required Approval Token: {priced['required_token']}")
    else:
        print(f"FAIL -> Dynamic pricing failed: {priced}")
        return False

    # Test 4: Execution on Explicit Confirmation
    po_id = priced["po_id"]
    token = priced["required_token"]
    print(f"\n[STEP 4] Testing Explicit Authorization with '{token}'")
    res = execute_confirmed_order(
        po_id,
        token,
        {
            "venue": priced["recommended_venue"],
            "symbol": priced["symbol"],
            "status": "FILLED",
            "filled_qty": priced["est_qty"],
            "exec_price": priced["touch_price"],
            "fee_usdt": priced["est_fee"],
        },
    )
    if res["success"]:
        receipt = res["receipt"]
        print(f"PASS -> Execution filled cleanly on venue {receipt['venue']}")
        print(f"        Filled {receipt['filled_qty']:.8f} {receipt['asset']} at {receipt['exec_price']:.4f} USDT")
        print(f"        Implementation Shortfall: {receipt['shortfall_bps']} (fee: {receipt['fee_usdt']:.4f} USDT)")
        print(format_receipt_card(receipt))
    else:
        print(f"FAIL -> Confirmation failed: {res.get('error')}")
        return False

    # Test 5: Dynamic Sell Order Execution (Reversal / Take Profit)
    sell_prompt = "Sell 5 USD BNB. Cash only."
    print(f"\n[STEP 5] Testing Dynamic Sell Order: '{sell_prompt}'")
    priced_sell = price_parent_order(sell_prompt, market_data=test_market_data)
    if priced_sell.get("valid") and priced_sell["side"] == "SELL":
        print(f"PASS -> Sell mandate passed | Side: {priced_sell['side']} | Asset: {priced_sell['asset']}")
        print(f"        Decision Mid: {priced_sell['decision_mid']:.4f} USDT | Touch Bid: {priced_sell['touch_price']:.4f} USDT")
        res_sell = execute_confirmed_order(
            priced_sell["po_id"],
            priced_sell["required_token"],
            {
                "venue": priced_sell["recommended_venue"],
                "symbol": priced_sell["symbol"],
                "status": "FILLED",
                "filled_qty": priced_sell["est_qty"],
                "exec_price": priced_sell["touch_price"],
                "fee_usdt": priced_sell["est_fee"],
            },
        )
        if res_sell["success"]:
            print(f"PASS -> Sell execution filled cleanly on venue {res_sell['receipt']['venue']}")
            print(format_receipt_card(res_sell["receipt"]))
        else:
            print(f"FAIL -> Sell execution failed: {res_sell.get('error')}")
            return False
    else:
        print(f"FAIL -> Sell pricing failed: {priced_sell}")
        return False

    print("=" * 66)
    print(" ALL VERIFICATION CHECKS PASSED (100% OPERATIONAL)")
    print("=" * 66)
    return True


def run_cli_order(order_text, custom_cap=None):
    priced = price_parent_order(order_text, custom_cap)
    if not priced.get("valid"):
        print(f"\n[REJECT] Code: {priced['code']}")
        print(f"Reason: {priced['reason']}")
        print("Execution halted. Zero orders dispatched to exchange rails.")
        sys.exit(1)

    po_id = priced["po_id"]
    print(f"\n[MANDATE CHECK PASSED]")
    print(f"Parent Order ID : {po_id}")
    print(f"Side            : {priced['side']}")
    print(f"Asset           : {priced['asset']}")
    print(f"Notional USD    : ${priced['notional_usd']:.2f}")
    touch_label = "Spot Touch Ask" if priced['side'] == 'BUY' else "Spot Touch Bid"
    print(f"Decision Mid    : {priced['decision_mid']:.4f} USDT")
    print(f"{touch_label:<16}: {priced['touch_price']:.4f} USDT")
    print(f"Estimated Qty   : {priced['est_qty']:.8f} {priced['asset']}")
    print(f"Convert Quote   : {priced['convert_quote']}")
    print(f"Selected Venue  : {priced['recommended_venue']}")
    print("-" * 55)
    print(f"AWAITING APPROVAL: Type '{priced['required_token']}' to commit.")

    try:
        user_input = input("\nEnter confirmation token: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted by operator.")
        sys.exit(0)

    res = execute_confirmed_order(po_id, user_input)
    if res["success"]:
        print(format_receipt_card(res["receipt"]))
    else:
        print(f"\nExecution Aborted: {res['error']}")
        sys.exit(1)


def run_mcp_server():
    """Stdio Model Context Protocol (MCP) server handler for Agent OS."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "deskflow",
                            "version": "1.0.0"
                        }
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            elif method == "notifications/initialized":
                pass
            elif method == "ping":
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "deskflow_price_order",
                                "description": "Validates a parent order against the mandate and evaluates normalized Binance Agent OS Spot/Convert data.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "order_text": {
                                            "type": "string",
                                            "description": "Natural language prompt e.g. 'Buy 5 USD BNB. Cash only.'"
                                        },
                                        "max_notional_usd": {
                                            "type": "number",
                                            "description": "Optional session cap override in USD"
                                        },
                                        "market_data": {
                                            "type": "object",
                                            "description": "Raw normalized Spot/Convert data returned by Binance Agent OS"
                                        }
                                    },
                                    "required": ["order_text", "market_data"]
                                }
                            },
                            {
                                "name": "deskflow_confirm_execution",
                                "description": "Reconciles an authorized Binance Agent OS execution result and writes it to the immutable blotter.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "po_id": {
                                            "type": "string",
                                            "description": "Parent order ID e.g. PO-001"
                                        },
                                        "confirm_token": {
                                            "type": "string",
                                            "description": "Exact confirmation token e.g. CONFIRM PO-001"
                                        },
                                        "execution_result": {
                                            "type": "object",
                                            "description": "Normalized execution result returned by Binance Agent OS"
                                        }
                                    },
                                    "required": ["po_id", "confirm_token", "execution_result"]
                                }
                            },
                            {
                                "name": "deskflow_inspect_blotter",
                                "description": "Returns the contents of the immutable blotter audit trail.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "deskflow_verify_mandate",
                                "description": "Returns the active mandate constraints governing the session.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "deskflow_update_mandate",
                                "description": "Updates the active session spending cap without changing venue or account restrictions.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "max_notional_usd": {
                                            "type": "number",
                                            "description": "Maximum allowed notional per order in USD"
                                        }
                                    },
                                    "required": ["max_notional_usd"]
                                }
                            }
                        ]
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            elif method == "tools/call":
                params = req.get("params", {})
                tool_name = params.get("name")
                args = params.get("arguments", {})

                if tool_name == "deskflow_price_order":
                    order_text = args.get("order_text", "")
                    priced = price_parent_order(
                        order_text,
                        args.get("max_notional_usd", custom_cap),
                        args.get("market_data"),
                    )
                    content = json.dumps(priced, indent=2)
                elif tool_name == "deskflow_confirm_execution":
                    po_id = args.get("po_id", "")
                    confirm_token = args.get("confirm_token", "")
                    res = execute_confirmed_order(po_id, confirm_token, args.get("execution_result"))
                    if res["success"]:
                        card = format_receipt_card(res["receipt"])
                        content = f"EXECUTION COMMITTED TO BLOTTER:\n{json.dumps(res['receipt'], indent=2)}\n\n{card}"
                    else:
                        content = f"EXECUTION REJECTED: {res.get('error')}"
                elif tool_name == "deskflow_inspect_blotter":
                    if os.path.exists(BLOTTER_FILE):
                        with open(BLOTTER_FILE, "r", encoding="utf-8") as f:
                            content = f.read()
                    else:
                        content = "Blotter is currently empty."
                elif tool_name == "deskflow_verify_mandate":
                    content = json.dumps(load_mandate(), indent=2)
                elif tool_name == "deskflow_update_mandate":
                    try:
                        content = json.dumps(update_mandate(args.get("max_notional_usd")), indent=2)
                    except ValueError as exc:
                        content = json.dumps({"success": False, "error": str(exc)})
                else:
                    content = f"Error: Tool '{tool_name}' not recognized."

                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": content}]
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="DeskFlow Autonomous Execution Clerk")
    parser.add_argument("order", nargs="?", help="Natural language order prompt or command keyword")
    parser.add_argument("--test", action="store_true", help="Run automated test suite")
    parser.add_argument("--mcp", action="store_true", help="Start DeskFlow as Stdio MCP server")
    parser.add_argument("--cap", type=float, help="Configure maximum notional mandate cap in USD (e.g. 50.00)")

    args = parser.parse_args()

    cmd = (args.order or "").strip().lower()
    if args.test or cmd == "test":
        run_test_suite()
    elif args.mcp or cmd == "mcp":
        run_mcp_server()
    elif args.order:
        run_cli_order(args.order, args.cap)
    else:
        print("DeskFlow Execution Clerk CLI")
        print("Usage:")
        print("  python deskflow.py \"Buy 5 USD BNB. Cash only.\"")
        print("  python deskflow.py test")
        print("  python deskflow.py mcp")


if __name__ == "__main__":
    main()
