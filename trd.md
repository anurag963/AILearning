# Algorithmic Trading Strategy Specification: Trend-Following Supply/Demand Price Action

## 1. Strategy Overview
This is a pure price action strategy that operates without standard technical indicators. It determines the macro trend using a strict market structure definition, identifies high-probability entry zones based on institutional consolidation, and filters trades using a mandatory risk-to-reward (R:R) ratio.

---

## 2. Core Logic & Rules

### Phase 1: Market Structure & Trend Identification
The algorithm must establish the current trend bias (Bullish, Bearish, or Neutral) before identifying trade setups.

* **Uptrend (Bullish Bias):** Defined by a sequence of Higher Highs (HH) and Higher Lows (HL).
    * *Validation Rule:* A low point is ONLY validated as a structural **Higher Low (HL)** if the subsequent price action breaks and closes above the previous **Higher High (HH)**. 
    * *Trend Persistence:* The market remains structurally bullish even during deep retracements, provided the price does not close below the last validated HL.
* **Downtrend (Bearish Bias):** Defined by a sequence of Lower Lows (LL) and Lower Highs (LH).
    * *Validation Rule:* A high point is ONLY validated as a structural **Lower High (LH)** if the subsequent price action breaks and closes below the previous **Lower Low (LL)**.
    * *Trend Persistence:* The market remains structurally bearish unless the price breaks and closes above the last validated LH.

### Phase 2: Zone Identification (Supply & Demand)
Once a trend is validated, the algorithm must dynamically map horizontal zones based on specific candlestick behavior.

* **Demand Zone (Long Entry Source):**
    * *Condition:* Look for an area of tight price consolidation (sideways movement) that immediately precedes a sharp, high-volume, impulsive move upward.
    * *Mapping:* Draw a horizontal rectangle from the **absolute low to the absolute high** of the final candlestick (or tight cluster) right before the large bullish breakout candle.
* **Supply Zone (Short Entry Source):**
    * *Condition:* Look for an area of tight price consolidation that immediately precedes a sharp, high-volume, impulsive move downward.
    * *Mapping:* Draw a horizontal rectangle from the **absolute high to the absolute low** of the final candlestick (or tight cluster) right before the large bearish breakdown candle.

### Phase 3: Trade Execution & Entry Triggers
* **Long Setup:**
    * *Pre-requisite:* Market Structure is Bullish.
    * *Trigger:* Price retraces back down and touches the upper boundary or enters inside the defined **Demand Zone**.
* **Short Setup:**
    * *Pre-requisite:* Market Structure is Bearish.
    * *Trigger:* Price retraces back up and touches the lower boundary or enters inside the defined **Supply Zone**.

---

## 3. Risk Management & Order Parameters

Every automated order must strictly comply with the following algorithmic mathematical filters. If a setup violates these filters, the order must be canceled or ignored.

### Long Order Constraints:
* **Execution Price (Entry):** Limit or Market order upon touching/entering the Demand Zone.
* **Stop-Loss (SL):** Placed exactly 1–2 pips/ticks **below the lowest point** of the Demand Zone rectangle.
* **Take-Profit (TP):** Target the absolute peak of the **most recent structural Higher High (HH)**.
* **Mathematical Filter:** Calculate $(\text{TP} - \text{Entry}) / (\text{Entry} - \text{SL})$. If this ratio is **less than 2.5**, the trade must be discarded.

### Short Order Constraints:
* **Execution Price (Entry):** Limit or Market order upon touching/entering the Supply Zone.
* **Stop-Loss (SL):** Placed exactly 1–2 pips/ticks **above the highest point** of the Supply Zone rectangle.
* **Take-Profit (TP):** Target the absolute trough of the **most recent structural Lower Low (LL)**.
* **Mathematical Filter:** Calculate $(\text{Entry} - \text{TP}) / (\text{SL} - \text{Entry})$. If this ratio is **less than 2.5**, the trade must be discarded.

---

## 4. Pseudo-Code / Logic Flow For Automation