"""Portfolio slash commands: /portfolio, /balance, /history, /drip.

Read-only views of the caller's account plus the per-position DRIP toggle. Like the market commands,
these only format requests/responses — all the math happens in the Flask API.
"""
import interactions
from interactions import (
    Extension, slash_command, slash_option, SlashContext,
    OptionType, SlashCommandChoice, Embed,
)

import api_client
from ._shared import call, error_message, money, GREEN, RED, BLUE, GREY

ONOFF_CHOICES = [
    SlashCommandChoice(name="on", value="on"),
    SlashCommandChoice(name="off", value="off"),
]


class Portfolio(Extension):
    """Slash commands for viewing the account and toggling DRIP."""

    @slash_command(name="portfolio", description="View your holdings and unrealized P&L")
    async def portfolio(self, ctx: SlashContext):
        """Show equity/cash plus each position's price, ACB, and unrealized P&L."""
        resp = await call(api_client.get, "/api/portfolio", discord_id=ctx.author.id)
        if not resp.ok:
            await ctx.send(error_message(resp), ephemeral=True)
            return
        p = resp.json()
        positions = p.get("positions", [])

        unrealized = float(p.get("total_unrealized", 0))
        embed = Embed(
            title="Your Portfolio",
            description=(f"**Equity:** {money(p.get('total_equity'))}  •  "
                        f"**Cash:** {money(p.get('cash_balance'))}"),
            color=GREEN if unrealized >= 0 else RED,
        )
        if not positions:
            embed.add_field("Holdings", "No open positions.", inline=False)
        for pos in positions[:20]:
            pnl = float(pos.get("unrealized_pnl", 0))
            arrow = "🟢" if pnl >= 0 else "🔴"
            drip = " · DRIP" if pos.get("drip_enabled") else ""
            embed.add_field(
                f"{pos['ticker']} ({pos['shares']} sh){drip}",
                f"{money(pos.get('current_price'))} · ACB {money(pos.get('acb'))} · "
                f"{arrow} {money(pos.get('unrealized_pnl'))}",
                inline=False,
            )
        embed.set_footer(f"Total unrealized P&L: {money(p.get('total_unrealized'))}")
        await ctx.send(embed=embed)

    @slash_command(name="balance", description="View your cash balance")
    async def balance(self, ctx: SlashContext):
        """Show the caller's current cash and starting balance."""
        resp = await call(api_client.get, "/api/user/me", discord_id=ctx.author.id)
        if not resp.ok:
            await ctx.send(error_message(resp), ephemeral=True)
            return
        u = resp.json()
        embed = Embed(title=f"{u.get('display_name')}'s Balance", color=BLUE)
        embed.add_field("Cash", money(u.get("balance")), inline=True)
        embed.add_field("Starting Balance", money(u.get("starting_balance")), inline=True)
        await ctx.send(embed=embed)

    @slash_command(name="history", description="View your recent transactions")
    async def history(self, ctx: SlashContext):
        """Show the caller's most recent transactions (up to 15)."""
        resp = await call(api_client.get, "/api/portfolio/history", discord_id=ctx.author.id)
        if not resp.ok:
            await ctx.send(error_message(resp), ephemeral=True)
            return
        data = resp.json()
        txns = data.get("transactions", [])
        if not txns:
            await ctx.send("No transactions yet.", ephemeral=True)
            return

        embed = Embed(title="Recent Transactions", color=GREY)
        for t in txns[:15]:
            line = f"{t['type']}"
            if t.get("ticker"):
                line += f" {t['ticker']}"
            if t.get("quantity"):
                line += f" ×{t['quantity']}"
            line += f" — {money(t.get('total_value'))}"
            embed.add_field(t.get("executed_at", "")[:10], line, inline=False)
        await ctx.send(embed=embed)

    @slash_command(name="drip", description="Toggle dividend reinvestment for a position")
    @slash_option(name="ticker", description="Ticker symbol", required=True, opt_type=OptionType.STRING)
    @slash_option(name="state", description="Turn DRIP on or off", required=True,
                  opt_type=OptionType.STRING, choices=ONOFF_CHOICES)
    async def drip(self, ctx: SlashContext, ticker: str, state: str):
        """Turn DRIP on or off for a single position."""
        resp = await call(api_client.patch, f"/api/portfolio/{ticker.upper()}/drip",
                          discord_id=ctx.author.id, json={"drip_enabled": state == "on"})
        if not resp.ok:
            await ctx.send(error_message(resp), ephemeral=True)
            return
        await ctx.send(f"DRIP turned **{state}** for {ticker.upper()}.", ephemeral=True)
