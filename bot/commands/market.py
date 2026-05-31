# Market commands — /price, /buy, /sell, /orders, /cancel
import interactions
from interactions import (
    Extension, slash_command, slash_option, SlashContext,
    OptionType, SlashCommandChoice, Embed,
)

import api_client
from ._shared import call, error_message, money, GREEN, RED, BLUE

ORDER_TYPE_CHOICES = [
    SlashCommandChoice(name="Market", value="MARKET"),
    SlashCommandChoice(name="Limit", value="LIMIT"),
    SlashCommandChoice(name="Stop", value="STOP"),
    SlashCommandChoice(name="Stop-Limit", value="STOP_LIMIT"),
]


class Market(Extension):

    @slash_command(name="price", description="Get a stock quote")
    @slash_option(name="ticker", description="Ticker symbol (e.g. AAPL)",
                  required=True, opt_type=OptionType.STRING)
    async def price(self, ctx: SlashContext, ticker: str):
        resp = await call(api_client.get, f"/api/stocks/{ticker.upper()}", discord_id=ctx.author.id)
        if not resp.ok:
            await ctx.send(error_message(resp), ephemeral=True)
            return
        s = resp.json()

        change = s.get("change_amount")
        color = GREEN if (change is not None and float(change) >= 0) else RED
        embed = Embed(title=f"{s['ticker']} — {s.get('company_name') or ''}".strip(" —"), color=color)
        embed.add_field("Price", money(s.get("last_price")), inline=True)
        embed.add_field("Change", f"{money(s.get('change_amount'))} ({s.get('change_percent') or '—'}%)", inline=True)
        embed.add_field("Bid / Ask", f"{money(s.get('bid'))} / {money(s.get('ask'))}", inline=True)
        embed.add_field("Day Range", f"{money(s.get('day_low'))} – {money(s.get('day_high'))}", inline=True)
        embed.add_field("52wk Range", f"{money(s.get('week_52_low'))} – {money(s.get('week_52_high'))}", inline=True)
        if s.get("after_hours_price"):
            embed.add_field("After Hours", money(s.get("after_hours_price")), inline=True)
        await ctx.send(embed=embed)

    @slash_command(name="buy", description="Place a buy order")
    @slash_option(name="ticker", description="Ticker symbol", required=True, opt_type=OptionType.STRING)
    @slash_option(name="quantity", description="Number of shares (fractional allowed)",
                  required=True, opt_type=OptionType.NUMBER)
    @slash_option(name="order_type", description="Order type", required=True,
                  opt_type=OptionType.STRING, choices=ORDER_TYPE_CHOICES)
    @slash_option(name="limit_price", description="Limit price (for LIMIT / STOP_LIMIT)",
                  required=False, opt_type=OptionType.NUMBER)
    @slash_option(name="stop_price", description="Stop price (for STOP / STOP_LIMIT)",
                  required=False, opt_type=OptionType.NUMBER)
    async def buy(self, ctx: SlashContext, ticker: str, quantity: float, order_type: str,
                  limit_price: float = None, stop_price: float = None):
        await self._place(ctx, "BUY", ticker, quantity, order_type, limit_price, stop_price)

    @slash_command(name="sell", description="Place a sell order")
    @slash_option(name="ticker", description="Ticker symbol", required=True, opt_type=OptionType.STRING)
    @slash_option(name="quantity", description="Number of shares (fractional allowed)",
                  required=True, opt_type=OptionType.NUMBER)
    @slash_option(name="order_type", description="Order type", required=True,
                  opt_type=OptionType.STRING, choices=ORDER_TYPE_CHOICES)
    @slash_option(name="limit_price", description="Limit price (for LIMIT / STOP_LIMIT)",
                  required=False, opt_type=OptionType.NUMBER)
    @slash_option(name="stop_price", description="Stop price (for STOP / STOP_LIMIT)",
                  required=False, opt_type=OptionType.NUMBER)
    async def sell(self, ctx: SlashContext, ticker: str, quantity: float, order_type: str,
                   limit_price: float = None, stop_price: float = None):
        await self._place(ctx, "SELL", ticker, quantity, order_type, limit_price, stop_price)

    async def _place(self, ctx, direction, ticker, quantity, order_type, limit_price, stop_price):
        body = {
            "ticker": ticker.upper(),
            "direction": direction,
            "order_type": order_type,
            "quantity": quantity,
        }
        if limit_price is not None:
            body["limit_price"] = limit_price
        if stop_price is not None:
            body["stop_price"] = stop_price

        resp = await call(api_client.post, "/api/orders", discord_id=ctx.author.id, json=body)
        if not resp.ok:
            await ctx.send(error_message(resp), ephemeral=True)
            return
        o = resp.json()

        filled = o.get("status") == "FILLED"
        embed = Embed(
            title=f"{direction} {o.get('quantity')} {o.get('ticker')}",
            description="✅ Filled" if filled else "🕒 Queued (pending)",
            color=GREEN if filled else BLUE,
        )
        embed.add_field("Type", o.get("order_type"), inline=True)
        if filled:
            embed.add_field("Fill Price", money(o.get("fill_price")), inline=True)
        else:
            if o.get("limit_price"):
                embed.add_field("Limit", money(o.get("limit_price")), inline=True)
            if o.get("stop_price"):
                embed.add_field("Stop", money(o.get("stop_price")), inline=True)
        await ctx.send(embed=embed)

    @slash_command(name="orders", description="List your pending and recent orders")
    async def orders(self, ctx: SlashContext):
        resp = await call(api_client.get, "/api/orders", discord_id=ctx.author.id)
        if not resp.ok:
            await ctx.send(error_message(resp), ephemeral=True)
            return
        rows = resp.json()
        if not rows:
            await ctx.send("You have no orders.", ephemeral=True)
            return

        embed = Embed(title="Your Orders", color=BLUE)
        for o in rows[:15]:
            detail = f"{o['direction']} {o['quantity']} {o['ticker']} ({o['order_type']}) — {o['status']}"
            if o.get("fill_price"):
                detail += f" @ {money(o['fill_price'])}"
            embed.add_field(f"#{o['id']}", detail, inline=False)
        await ctx.send(embed=embed)

    @slash_command(name="cancel", description="Cancel a pending order")
    @slash_option(name="order_id", description="The order ID (from /orders)",
                  required=True, opt_type=OptionType.INTEGER)
    async def cancel(self, ctx: SlashContext, order_id: int):
        resp = await call(api_client.delete, f"/api/orders/{order_id}", discord_id=ctx.author.id)
        if not resp.ok:
            await ctx.send(error_message(resp), ephemeral=True)
            return
        await ctx.send(f"Order #{order_id} cancelled.", ephemeral=True)
