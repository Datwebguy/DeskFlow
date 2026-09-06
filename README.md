# DeskFlow Execution Clerk

`#F0B90B` **Binance Agent OS Native** &nbsp; | &nbsp; `#0ECB81` **Mandate Governed** &nbsp; | &nbsp; `#F6465D` **Subaccount Isolated** &nbsp; | &nbsp; `#1E2329` **Model Context Protocol**

Live Interactive Terminal: https://datwebguy.github.io/DeskFlow/

## Why You Need DeskFlow

When trading cryptocurrency with autonomous artificial intelligence assistants such as Claude, Cursor, ChatGPT, or Binance Agent OS, language models can easily make critical mistakes. An artificial intelligence agent might misread pricing, hallucinate order parameters, repeat duplicate fills, borrow unauthorized margin, or exhaust your balance on an uncontrolled prompt.

DeskFlow is your personal financial safety guard. It acts as an execution clerk positioned between your conversational agent and the Binance exchange. DeskFlow strictly enforces your spending ceiling, inspects live order book depth from Binance, routes across Spot and Convert for optimal liquidity, and requires your explicit manual approval (`CONFIRM PO_001`) before any order can ever be dispatched.

> [!NOTE]
> DeskFlow operates directly alongside the official Binance Agent OS endpoint. It interacts solely with the dedicated agentic subaccount, guaranteeing that master account balances, external withdrawal functions, and unapproved financial instruments remain completely inaccessible.

## How You Chat With Your Assistant

DeskFlow is designed for natural conversation. You chat with your artificial intelligence assistant just like speaking to an execution clerk on a trading desk:

1. **You make a natural request**: You prompt your agent naturally: `"Buy 5 USD BNB. Cash only."`
2. **DeskFlow quotes and verifies**: DeskFlow intercepts the command, checks your spending limits, fetches live Binance order book depth, compares Spot against Convert liquidity, and creates ticket `PO_001`.
3. **Your agent requests approval**: Your assistant reports live pricing and asks for confirmation: `"DeskFlow quoted BNB at 765.55 USDT on Spot. Spending: $5.00 USD. Reply CONFIRM PO_001 to execute."`
4. **You provide exact confirmation**: You reply: `"CONFIRM PO_001"`
5. **DeskFlow executes and audits**: DeskFlow dispatches the fill to Binance, isolates fees, calculates slippage in basis points, logs the fill to an immutable blotter, and returns a verified execution receipt card.

> [!IMPORTANT]
> DeskFlow rejects conversational approvals. If you reply with `"Yes"`, `"Go ahead"`, or `"Looks good"`, DeskFlow refuses execution. Only the exact approval token `CONFIRM PO_001` unlocks order placement. Your capital is never risked on an ambiguous chat message.

```diff
+ AUTHORIZED COMMAND: CONFIRM PO_001
! RESULT: Dispatches execution to selected venue
! REJECTED INPUT: Yes go ahead, Execute now, Looks good
! OUTCOME: Zero exchange orders dispatched
```

## User Quickstart Guide

Choose the path that fits your setup to begin trading safely in under sixty seconds:

### Path One · Instant Web Assistant (Zero Setup)

The fastest way to experience DeskFlow without installing software:

1. Open the live web portal at https://datwebguy.github.io/DeskFlow/
2. Click any preset chip or type your own custom prompt such as `"Buy 5 USD BNB. Cash only."` or `"Buy 3 USD SOLANA. Cash only."`
3. Watch DeskFlow check your spending mandate, stream live Binance order book depth, and request confirmation.
4. Click **Confirm Order** to simulate execution and inspect the resulting audited receipt card.

### Path Two · AI Assistant Chat (Claude Code and Cursor)

Attach DeskFlow to your artificial intelligence assistant so every trade suggested in chat is protected by an execution mandate:

1. Open PowerShell or terminal from any folder on your computer and install DeskFlow globally:

```bash
pip install git+https://github.com/Datwebguy/DeskFlow.git
```

2. Connect the official Binance Agent OS gateway and DeskFlow clerk to Claude Code:

```bash
# Connect official Binance Agent OS gateway
claude mcp add --scope user binance-mcp-server --transport http https://agent.binance.com/mcp/agentic

# Attach DeskFlow execution clerk globally
claude mcp add --scope user deskflow -- deskflow mcp
```

3. Launch your assistant and chat naturally from any directory:

```bash
claude
```

Prompt your assistant: `"Buy 5 USD BNB. Cash only."` DeskFlow intercepts the request, presents ticket `PO_001`, and awaits your reply: `"CONFIRM PO_001"`.

### Path Three · Direct Terminal Command

If you prefer using the command prompt directly without an artificial intelligence chatbot:

1. Install DeskFlow globally:

```bash
pip install git+https://github.com/Datwebguy/DeskFlow.git
```

2. Run protected natural language orders directly from any directory:

```bash
deskflow "Buy 5 USD BNB. Cash only."
```

3. Run the automated verification suite to verify all mandate protections and receipt rendering in one second:

```bash
deskflow test
```

## How You Control Your Spending Ceiling

You always maintain complete control over your capital. Your artificial intelligence assistant can never exceed the budget you set:

1. **Default Capital Cap**: Every fresh DeskFlow session starts with a conservative spending ceiling of ten United States dollars ($10.00 USD) notional per order.
2. **Increase Cap in Chat**: Tell your assistant: `"DeskFlow, update my spending cap to 50 USD."` Your assistant invokes `deskflow_update_mandate`, immediately raising your session limit to fifty dollars.
3. **Increase Cap in Terminal**: Pass the cap parameter when dispatching orders:

```bash
deskflow "Buy 50 USD SOL. Cash only." --cap 50
```

4. **Permanent Configuration**: Edit `mandate.yml` to set `max_notional_usd: 50.0` or configure the `DESKFLOW_MAX_NOTIONAL_USD` environment variable.

Any order exceeding your active spending ceiling is rejected immediately before reaching Binance.

## The Four Sovereign Safeguards Protecting You

DeskFlow guarantees four layers of protection between your prompts and live liquidity:

1. **Zero Leverage Guarantee**: Futures contracts, perpetual swaps, margin borrowing, and leverage multipliers are blocked permanently. Cash spot and convert trades only.
2. **Subaccount Isolation**: DeskFlow operates strictly within a dedicated agentic subaccount. Your primary Binance account balances and cryptocurrency withdrawal functions remain completely unreachable.
3. **Dual Venue Arbitrage**: Real time evaluation compares Spot order book depth against Convert pricing without fabricating synthetic quotes, guaranteeing true exchange liquidity selection.
4. **Implementation Shortfall Audit**: Calculates true slippage in basis points relative to the decision mid price, isolates exchange fees, and appends every fill record to an immutable blotter.

```
Price Difference = Execution Price minus Decision Mid Price
Shortfall Basis Points = (Price Difference / Decision Mid Price) * 10000
```

## Visual Execution Receipt

Upon fill confirmation, DeskFlow prints an institutional trade execution card giving operators a clear, audited snapshot of the settled position.

```text
┌──────────────────────────────────────────────────────────────────┐
│  DESKFLOW EXECUTION RECEIPT · BINANCE AGENT OS                   │
├──────────────────────────────────────────────────────────────────┤
│  Parent Order ID : PO_001                Status   : FILLED        │
│  Venue Executed  : SPOT                  Symbol   : BNBUSDT       │
│  Planned Capital : $5.00 USD             Filled   : 0.00653130 BNB│
├──────────────────────────────────────────────────────────────────┤
│  Decision Mid    : 765.5450 USDT         Fill Price: 765.5500 USDT│
│  Shortfall       : +0.07 bps             Fee Paid : 0.0050 USDT   │
│  Subaccount Scoped: AGENTIC_SUB          Mandate  : PASSED        │
└──────────────────────────────────────────────────────────────────┘
```

> [!CAUTION]
> If market data feeds drop, if balances fail to confirm token arrival, or if exchange reports return incomplete payloads, DeskFlow flags the fill status as incomplete data rather than fabricating synthetic confirmations.

## Model Context Protocol Tool Registry

DeskFlow exposes five standardized tools over standard input and output, allowing any Model Context Protocol compliant client to govern its execution:

| Tool Name | Input Arguments | Operation and Output |
|---|---|---|
| `deskflow_price_order` | `{"order_text": string, "max_notional_usd"?: number}` | Parses dynamic prompt, validates mandate, queries live Binance liquidity, emits pretrade ticket |
| `deskflow_confirm_execution` | `{"po_id": string, "confirm_token": string}` | Verifies authorization token, executes order on selected venue, computes shortfall, appends blotter |
| `deskflow_update_mandate` | `{"max_notional_usd": number}` | Adjusts the active session capital ceiling (for example raising cap from ten to fifty dollars) |
| `deskflow_inspect_blotter` | `{}` | Returns complete markdown blotter audit trail with historical execution shortfall metrics |
| `deskflow_verify_mandate` | `{}` | Returns active governing constraints including size caps, permitted venues, and confirmation mandates |

## Immutable Posttrade Blotter

Every executed fill is preserved inside `blotter.md`. The ledger contains exact timestamps, parent order identifiers, executed venues, planned notional amounts, filled quantities, isolated fees, decision mid quotes, and implementation shortfall basis points for transparent auditing.
