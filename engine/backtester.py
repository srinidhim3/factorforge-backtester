"""Vectorized backtester utilities.

Implements a simple deterministic backtester that accepts price DataFrame and
target weights DataFrame and computes portfolio returns, positions, turnover,
and basic metrics.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from pathlib import Path

import matplotlib.pyplot as plt


def backtest_from_weights(
    price_df: pd.DataFrame,
    weights: pd.DataFrame,
    execution: str = "next_close",
    transaction_cost_bps: float = 0.001,
    *,
    plot: bool = False,
    plot_outdir: Optional[str] = None,
    initial_capital: float = 100000.0,
) -> Tuple[pd.Series, pd.DataFrame, Dict[str, float]]:
    """Run a vectorized backtest from per-date target weights.

    Args:
        price_df: prices (dates x tickers)
        weights: targets (dates x tickers), indexed with same or subset of price_df.index
        execution: 'next_close' (default) or 'same_close'
        transaction_cost_bps: cost applied to turnover (decimal fraction)

    Returns:
        returns: Series of net portfolio returns aligned to price return index
        positions: DataFrame of realized position weights used each period
        metrics: dict with cumulative_return, annualized_return (approx), volatility, max_drawdown, total_turnover
    """
    if execution not in ("next_close", "same_close"):
        raise ValueError("execution must be 'next_close' or 'same_close'")

    # compute simple returns
    price_returns = price_df.pct_change()

    # Determine which return periods weights apply to
    if execution == "next_close":
        # weights at t apply to returns at t+1 -> shift returns up
        aligned_returns = price_returns.shift(-1)
    else:
        # same_close: weights at t apply to returns at t
        aligned_returns = price_returns

    # Align weights to the full return index (fill missing weight rows with zeros)
    full_weights = pd.DataFrame(
        0.0, index=aligned_returns.index, columns=price_df.columns
    )
    # Reindex provided weights into full index (assume columns match)
    w = weights.reindex(index=full_weights.index, columns=full_weights.columns).fillna(
        0.0
    )
    full_weights.update(w)

    # For turnover we need previous period weights (start with zeros)
    prev_w = full_weights.shift(1).fillna(0.0)

    # Compute turnover L1 norm per period
    turnover = (full_weights.subtract(prev_w)).abs().sum(axis=1)

    # Compute gross returns: dot product of weights and returns (mask NaNs)
    # Replace NaN returns with 0 in the dot product; treat missing prices as zero contribution
    masked_returns = aligned_returns.fillna(0.0)
    gross = (full_weights * masked_returns).sum(axis=1)

    # Transaction cost is turnover * bps
    tx_cost = turnover * float(transaction_cost_bps)

    net = gross - tx_cost

    # Compute basic metrics
    cumulative = (1.0 + net).cumprod().ffill()
    total_return = cumulative.iloc[-1] - 1.0 if len(cumulative) > 0 else 0.0
    # approximate annualization using 252 trading days
    ann_return = (1.0 + total_return) ** (252.0 / max(len(net.dropna()), 1)) - 1.0
    vol = net.std() * np.sqrt(252.0)
    # max drawdown
    peak = cumulative.cummax()
    dd = (cumulative - peak) / peak
    max_dd = float(dd.min()) if not dd.empty else 0.0

    metrics = {
        "cumulative_return": float(total_return),
        "annualized_return": float(ann_return),
        "annualized_volatility": float(vol),
        "max_drawdown": float(max_dd),
        "total_turnover": float(turnover.sum()),
    }

    # Optionally produce plots: aggregate instrument price vs portfolio net worth
    if plot:
        try:
            _plot_aggregate_and_wealth(
                price_df=price_df,
                returns=net,
                weights=full_weights,
                initial_capital=float(initial_capital),
                outdir=Path(plot_outdir) if plot_outdir is not None else None,
            )
        except (
            Exception
        ) as exc:  # keep plotting optional but fail loudly if user requested it
            raise RuntimeError("Error while plotting backtest results") from exc

    return net, full_weights, metrics


def _plot_aggregate_and_wealth(
    *,
    price_df: pd.DataFrame,
    returns: pd.Series,
    weights: pd.DataFrame,
    initial_capital: float = 100000.0,
    outdir: Optional[Path] = None,
) -> None:
    """Create and save (or show) a figure with aggregate price and portfolio net worth.

    The aggregate price is the sum of instrument close prices (no scaling). The
    portfolio net worth is computed from periodic net returns produced by the
    backtester and scaled by `initial_capital`.
    """
    # Align returns to price index and fill gaps with 0 for plotting
    returns_aligned = returns.reindex(price_df.index).fillna(0.0)

    aggregate_price = price_df.sum(axis=1)
    portfolio_wealth = (1.0 + returns_aligned).cumprod() * float(initial_capital)

    n_instruments = len(price_df.columns)
    nrows = n_instruments + 1
    fig, axes = plt.subplots(nrows, 1, figsize=(12, 3 * nrows), sharex=True)
    if nrows == 1:
        axes = [axes]

    ax_top = axes[0]
    ax_top.plot(
        aggregate_price.index,
        aggregate_price.values,
        label="Aggregate Price (sum)",
        color="tab:blue",
    )
    ax_wealth = ax_top.twinx()
    ax_wealth.plot(
        portfolio_wealth.index,
        portfolio_wealth.values,
        label="Portfolio Net Worth",
        color="tab:purple",
        alpha=0.8,
    )
    ax_top.set_title("Aggregate Price vs Portfolio Net Worth")
    ax_top.set_ylabel("Aggregate Price (sum of closes)")
    ax_wealth.set_ylabel(f"Portfolio Net Worth (initial ${initial_capital:,.0f})")
    ax_top.legend(loc="upper left")
    ax_wealth.legend(loc="upper right")

    # Per-instrument panels with simple buy/sell markers derived from weights
    for idx, col in enumerate(price_df.columns, start=1):
        ax = axes[idx]
        ax.plot(price_df.index, price_df[col], label=f"{col} Close")
        # weight transitions -> buy/sell
        if col in weights.columns:
            wcol = weights[col].reindex(price_df.index).fillna(0.0)
            prev = wcol.shift(1).fillna(0.0)
            buys = (wcol > 0) & (prev == 0)
            sells = (wcol == 0) & (prev > 0)
            if buys.any():
                bx = price_df.index[buys.values]
                by = price_df.loc[bx, col]
                ax.scatter(bx, by, marker="^", color="green", s=40, label="Buy")
            if sells.any():
                sx = price_df.index[sells.values]
                sy = price_df.loc[sx, col]
                ax.scatter(sx, sy, marker="v", color="red", s=40, label="Sell")
        ax.set_title(col)
        ax.legend(loc="upper left")

    fig.tight_layout()
    if outdir is None:
        plt.show()
    else:
        outdir.mkdir(parents=True, exist_ok=True)
        out_file = outdir / "backtest_prices_and_wealth.png"
        fig.savefig(out_file)
        plt.close(fig)


def plot_weights_stack(weights: pd.DataFrame, outdir: Optional[Path] = None) -> None:
    """Save or show a stacked area plot of weights.

    This mirrors the previous helper in the scripts module but centralizes
    plotting with the backtester so callers only rely on one implementation.
    """
    fig, ax = plt.subplots(figsize=(12, 4))
    weights_plot = weights.fillna(0.0)
    weights_plot.plot.area(ax=ax)
    ax.set_title("Weights (stacked)")
    fig.tight_layout()
    if outdir is None:
        plt.show()
    else:
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        out_file = outdir / "weights_stack.png"
        fig.savefig(out_file)
        plt.close(fig)


def plot_equity_curve(returns: pd.Series, outdir: Optional[Path] = None) -> None:
    """Save or show an equity curve (cumulative returns) plot."""
    eq = (1 + returns).cumprod()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(eq.index, eq.values, label="Equity")
    ax.set_title("Equity Curve")
    ax.set_ylabel("Cumulative Return")
    ax.legend()
    fig.tight_layout()
    if outdir is None:
        plt.show()
    else:
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        out_file = outdir / "equity_curve.png"
        fig.savefig(out_file)
        plt.close(fig)
