# DeskFlow Execution Clerk

`#F0B90B` **Binance Agent OS Native** &nbsp; | &nbsp; `#0ECB81` **Mandate Governed** &nbsp; | &nbsp; `#F6465D` **Subaccount Isolated** &nbsp; | &nbsp; `#1E2329` **Model Context Protocol**

Live Interactive Terminal: https://datwebguy.github.io/DeskFlow/

## First Time Operator Guide

Choose the path that fits your workflow to start in under sixty seconds:

### Path One · Instant Browser Test (Zero Setup)

Visit the live interactive terminal at https://datwebguy.github.io/DeskFlow/

Click any preset chip or type an order prompt like `"Buy 5 USD BNB. Cash only."` to observe real time pricing, mandate checks, and confirmation gates directly in your browser.

### Path Two · Local Machine Execution

Clone the repository, enter the directory, and run directly with Python:

```bash
# Clone and enter directory
git clone https://github.com/Datwebguy/DeskFlow.git
cd DeskFlow

# Run automated verification suite
python deskflow.py test

# Execute dynamic order
python deskflow.py "Buy 3 USD SOLANA. Cash only."
```

Alternatively install globally to run from any terminal directory:

```bash
pip install git+https://github.com/Datwebguy/DeskFlow.git
deskflow test
```

### Path Three · AI Agent Integration (Claude Code and Cursor)

Attach DeskFlow as a Model Context Protocol tool provider:

```bash
# Step 1: Connect official Binance Agent OS gateway
claude mcp add binance-mcp-server --transport http https://agent.binance.com/mcp/agentic

# Step 2: Attach DeskFlow execution clerk
claude mcp add deskflow -- python deskflow.py mcp
```

Once attached, prompt your agent naturally: `"Buy 5 USD BNB. Cash only."` DeskFlow will intercept, price against live depth, issue ticket `PO_001`, and refuse execution until you reply: `CONFIRM PO_001`.


## Executive Summary

DeskFlow is an institutional execution clerk engineered for the Binance Agent OS ecosystem. Modern autonomous agents are proficient at analyzing sentiment and proposing trades, yet they often lack financial discipline, execution boundaries, and posttrade accountability. DeskFlow resolves this vulnerability by placing a deterministic verification layer between natural language agent prompts and live exchange routing.

Every interaction submitted to DeskFlow dynamically parses order parameters, validates them against a strict mandate, acquires comparative pricing across spot and convert facilities, demands explicit human authorization, and records audited execution details to an immutable blotter.

> [!NOTE]
> DeskFlow operates directly alongside the official Binance Agent OS endpoint. It interacts solely with the dedicated agentic subaccount, guaranteeing that master account balances, external withdrawal functions, and unapproved financial instruments remain completely inaccessible.

## The Core Philosophy of Governed Execution

Trading with autonomous artificial intelligence introduces critical risks, including prompt injection, hallucinated quotes, uncontrolled position sizing, and accidental exposure to high risk derivative instruments. DeskFlow addresses these operational hazards through strict pretrade verification.

The mandate document acts as an immutable boundary. The agent cannot override its boundaries regardless of user phrasing. Every incoming request is parsed dynamically for asset identity, side, notional value, and venue requirements. Any order violating size limits, attempting leverage, or failing authentication is rejected immediately before any trade execution endpoint is reached.

> [!IMPORTANT]
> The mandate establishes non negotiable safeguards. The default maximum order size is capped at ten United States dollars notional value. Operators can adjust this capital ceiling to fifty dollars or any institutional threshold by editing mandate.yml, setting the DESKFLOW_MAX_NOTIONAL_USD environment variable, or passing the cap argument. Futures, perpetual contracts, margin borrows, and capital withdrawals remain denied unconditionally.

## Four Stage Execution Lifecycle

DeskFlow implements an institutional four stage pipeline before any order touches exchange liquidity:

1. **Parse and Govern**: Natural language parsing dynamically extracts side, asset, and notional capital. The clerk validates the parameters against the mandate, immediately rejecting leverage or size violations.
2. **Price and Route**: Connects to the live Binance public order book to compute decision mid pricing and evaluate touch liquidity against Convert facilities without fabricating synthetic quotes.
3. **Require Confirmation**: Issues an unconfirmed pretrade ticket with a unique parent order identifier. Execution is strictly blocked until an operator inputs the exact approval token.
4. **Reconcile and Audit**: Executes the order on the recommended venue, isolates exchange fees, computes implementation shortfall in basis points, and appends the fill record to an immutable blotter.

## Model Context Protocol Tool Registry

DeskFlow exposes four standardized tools over standard input and output, allowing any Model Context Protocol compliant client to govern its execution:

| Tool Name | Input Arguments | Operation and Output |
|---|---|---|
| `deskflow_price_order` | `{"order_text": string, "max_notional_usd"?: number}` | Parses dynamic prompt, validates mandate, queries live Binance liquidity, emits pretrade ticket |
| `deskflow_confirm_execution` | `{"po_id": string, "confirm_token": string}` | Verifies authorization token, executes order on selected venue, computes shortfall, appends blotter |
| `deskflow_update_mandate` | `{"max_notional_usd": number}` | Adjusts the active session capital ceiling (for example raising cap from ten to fifty dollars) |
| `deskflow_inspect_blotter` | `{}` | Returns complete markdown blotter audit trail with historical execution shortfall metrics |
| `deskflow_verify_mandate` | `{}` | Returns active governing constraints including size caps, permitted venues, and confirmation mandates |

## Human in the Loop Authorization

DeskFlow rejects implicit or conversational confirmations. To prevent accidental trade submissions, the clerk pauses and demands an exact syntax match containing the allocated parent order identifier.

When the operator enters the designated confirmation command, DeskFlow validates the token, locks the selected venue, and sends the execution payload to the exchange. If the operator enters any alternate text, conversational replies, or questions, the clerk treats the action as unconfirmed and refuses to dispatch orders.

```diff
+ AUTHORIZED COMMAND: CONFIRM PO_001
! RESULT: Dispatches execution to selected venue
! REJECTED INPUT: Yes go ahead, Execute now, Looks good
! OUTCOME: Zero exchange orders dispatched
```

## Posttrade Blotter and Mathematical Reconciliation

Immediately following order fill confirmation, DeskFlow initiates a complete reconciliation sequence. It queries live account balances and trade records directly from the exchange to verify actual token receipts and fee deductions against original order parameters.

The clerk calculates execution shortfall measured in basis points relative to the original decision mid price. The shortfall metric reveals true slippage and market impact. All exchange fees are preserved in an isolated column to prevent artificial distortion of execution performance.

```
Price Difference = Execution Price minus Decision Mid Price
Shortfall Basis Points = (Price Difference / Decision Mid Price) * 10000
```

Every reconciled execution appends a structured record to the permanent blotter ledger, noting parent order identification, venue, planned capital, filled quantity, exact fees, decision mid price, basis points shortfall, and overall execution status.

### Visual Execution Receipt

Upon fill confirmation, DeskFlow prints an institutional trade execution card giving operators and auditing systems a standardized snapshot of the settled position.

```text
┌──────────────────────────────────────────────────────────────────┐
│  DESKFLOW EXECUTION RECEIPT · BINANCE AGENT OS                   │
├──────────────────────────────────────────────────────────────────┤
│  Parent Order ID : PO_001                Status   : FILLED        │
│  Venue Executed  : SPOT                  Symbol   : BNBUSDT       │
│  Planned Capital : $6.50 USD             Filled   : 0.00849063 BNB│
├──────────────────────────────────────────────────────────────────┤
│  Decision Mid    : 765.5450 USDT         Fill Price: 765.5500 USDT│
│  Shortfall       : +0.07 bps             Fee Paid : 0.0065 USDT   │
│  Subaccount Scoped: AGENTIC_SUB          Mandate  : PASSED        │
└──────────────────────────────────────────────────────────────────┘
```

> [!CAUTION]
> If market data feeds drop, if balances fail to confirm token arrival, or if exchange reports return incomplete payloads, DeskFlow flags the fill status as incomplete data rather than fabricating synthetic confirmations.

## How to Use DeskFlow

DeskFlow provides three distinct access methods depending on operator workflow:

### 1. Model Context Protocol Integration (Claude Code and Agent OS)

Attach DeskFlow directly alongside the official Binance Agent OS server:

```bash
# Step 1: Attach official Binance Agent OS gateway
claude mcp add binance-mcp-server --transport http https://agent.binance.com/mcp/agentic

# Step 2: Attach DeskFlow execution clerk
claude mcp add deskflow -- python deskflow.py mcp
```

**Agent Interaction Flow**:
1. Operator prompts: `"Buy 5 USD BNB. Cash only."`
2. Agent calls `deskflow_price_order` with the prompt.
3. DeskFlow parses amount dynamically, checks mandate limits, queries live Binance order book, and returns pretrade ticket `PO_001`.
4. Agent prompts operator: `"DeskFlow issued ticket PO_001. Please reply CONFIRM PO_001 to execute."`
5. Operator replies: `"CONFIRM PO_001"`
6. Agent calls `deskflow_confirm_execution` with the confirmation token.
7. DeskFlow commits execution, isolates fees, calculates basis point shortfall, writes to blotter, and outputs the receipt card.

### 2. Standalone Command Line Execution

Operators can dispatch natural language parent orders with any dynamic amount directly from the terminal:

```bash
# Execute dynamic cash parent order
python deskflow.py "Buy 6.50 USD BNB. Cash only."
```

### 3. Automated Verification Suite

To verify mandate enforcement, venue arbitrage, live telemetry pulls, fee isolation, and execution receipt card formatting in one command:

```bash
python deskflow.py test
```

### 4. Interactive Live Showcase

Visit the live showcase at https://datwebguy.github.io/DeskFlow/ to inspect the live Binance ticker tape, test dynamic natural language prompts, view real time pretrade tickets, and simulate operator authorization.
