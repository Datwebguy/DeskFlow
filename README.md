# DeskFlow Execution Clerk

`#F0B90B` **Binance Agent OS Native** &nbsp; | &nbsp; `#0ECB81` **Mandate Governed** &nbsp; | &nbsp; `#F6465D` **Subaccount Isolated** &nbsp; | &nbsp; `#1E2329` **Model Context Protocol**

Live Interactive Terminal: https://datwebguy.github.io/DeskFlow/

## Executive Summary

DeskFlow is an institutional execution clerk engineered for the Binance Agent OS ecosystem. Modern autonomous agents are proficient at analyzing sentiment and proposing trades, yet they often lack financial discipline, execution boundaries, and posttrade accountability. DeskFlow resolves this vulnerability by placing a deterministic verification layer between natural language agent prompts and live exchange routing. 

Every single interaction submitted to DeskFlow must pass through a strict mandate, acquire comparative pricing across spot and convert facilities, demand explicit human authorization, and record audited execution details to an immutable blotter.

> [!NOTE]
> DeskFlow operates exclusively against the official Binance Agent OS endpoint. It interacts solely with the dedicated agentic subaccount, guaranteeing that master account balances, external withdrawal functions, and unapproved financial instruments remain completely inaccessible.

## The Core Philosophy of Governed Execution

Trading with autonomous artificial intelligence introduces critical risks, including prompt injection, hallucinated quotes, uncontrolled position sizing, and accidental exposure to high risk derivative instruments. DeskFlow addresses these operational hazards through strict pretrade verification. 

The mandate document acts as an immutable boundary. The agent cannot override its boundaries regardless of user phrasing. Every incoming request is parsed for asset identity, side, notional value, and venue requirements. Any order violating size limits, attempting leverage, or failing authentication is rejected immediately before any trade execution endpoint is reached.

> [!IMPORTANT]
> The mandate establishes non negotiable safeguards. The maximum order size is capped at ten United States dollars notional value. Futures, perpetual contracts, margin borrows, and capital withdrawals are denied unconditionally.

## Comparative Venue Evaluation

Once an incoming parent order passes all mandate filters, DeskFlow queries live exchange conditions through the official Model Context Protocol interface. The clerk evaluates two distinct venues for settlement, comparing the live spot order book against convert facilities.

For the spot venue, DeskFlow retrieves live book depth to determine the touch ask and computes the decision mid price. For the convert venue, DeskFlow requests a guaranteed quote when available or designates the quote to be secured at the confirmation instant without inventing artificial numbers. The clerk evaluates price impact and immediate liquidity, recommending the venue offering the best execution quality.

> [!TIP]
> The generated pretrade ticket gives the user total visibility into decision mid pricing, comparative venue expectations, and routing rationale. Capital is never committed until the exact confirmation string is received.

## Human in the Loop Authorization

DeskFlow rejects implicit or conversational confirmations. To prevent accidental trade submissions, the clerk pauses and demands an exact syntax match containing the allocated parent order identifier.

When the user enters the designated confirmation command, DeskFlow validates the token, locks the selected venue, and sends the execution payload to the exchange. If the user enters any alternate text, conversational replies, or questions, the clerk treats the action as unconfirmed and refuses to dispatch orders.

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

Upon fill confirmation, DeskFlow prints an institutional trade execution card giving users and auditing systems a standardized snapshot of the settled position.

```text
┌──────────────────────────────────────────────────────────────────┐
│  DESKFLOW EXECUTION RECEIPT · BINANCE AGENT OS                   │
├──────────────────────────────────────────────────────────────────┤
│  Parent Order ID : PO_001               Status   : FILLED        │
│  Venue Executed  : SPOT                 Symbol   : BNBUSDT       │
│  Planned Capital : $8.00 USD            Filled   : 0.01031260 BNB│
├──────────────────────────────────────────────────────────────────┤
│  Decision Mid    : 775.7450 USDT        Fill Price: 775.7500 USDT│
│  Shortfall       : +0.06 bps            Fee Paid : 0.0080 USDT   │
│  Subaccount Scoped: AGENTIC_SUB         Mandate  : PASSED        │
└──────────────────────────────────────────────────────────────────┘
```

> [!CAUTION]

> If market data feeds drop, if balances fail to confirm token arrival, or if exchange reports return incomplete payloads, DeskFlow flags the fill status as incomplete data rather than fabricating synthetic confirmations.

## Verification Scenarios and Operational Proof

The repository demonstrates total compliance across both positive and negative execution paths using authentic exchange telemetry.

In the negative validation scenario, an incoming request demands twenty times leveraged perpetual contracts on BNB. DeskFlow intercepts the intent during pretrade parsing, triggers an immediate venue rejection code, logs the violation to the rejects registry, and terminates the operation without making any order calls.

In the positive validation scenario, a cash parent order for eight United States dollars of BNB is parsed under the mandate cap. DeskFlow pulls live book depth, calculates the decision mid price at 775.7450 USDT, prints the pretrade ticket, awaits explicit confirmation, dispatches the spot execution at 775.7500 USDT, isolates the 0.0080 USDT fee, computes the exact positive 0.06 basis points shortfall, and writes the reconciled entry to the blotter.

## Integration Guide

Deployment requires adding the official Binance Model Context Protocol server inside your client environment. The server connects using streamable transport to the official agentic gateway.

Authentication takes place through secure authorization, binding the session directly to your dedicated subaccount. Once authenticated, DeskFlow reads the mandate file, connects to the exposed tool registry, and stands ready to govern your autonomous execution flow.

## Operational Execution

DeskFlow functions both as an autonomous terminal command and as an installable Model Context Protocol server.

### Command Execution

Operators can dispatch natural language parent orders directly from the terminal. The clerk evaluates the mandate, pulls live exchange depth, issues the pretrade ticket, and awaits confirmation.

```bash
python deskflow.py "Buy 8 USD BNB. Cash only."
```

### Automated Verification Suite

To verify mandate enforcement, venue arbitrage, live telemetry pulls, fee isolation, and execution receipt card formatting in one command:

```bash
python deskflow.py test
```

### Model Context Protocol Server

DeskFlow exposes native tool endpoints over standard input and output. Any compatible agent client can attach DeskFlow as a local tool provider:

```bash
python deskflow.py mcp
```

