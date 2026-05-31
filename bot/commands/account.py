# Account commands — /link (connect Discord to a platform account)
import interactions
from interactions import Extension, slash_command, SlashContext, Embed

import api_client
from ._shared import call, error_message, BLUE


class Account(Extension):

    @slash_command(name="link", description="Link your Discord to your trading account")
    async def link(self, ctx: SlashContext):
        resp = await call(api_client.post, "/api/auth/discord/link-token",
                          json={"discord_id": str(ctx.author.id)})
        if not resp.ok:
            await ctx.send(error_message(resp), ephemeral=True)
            return
        url = resp.json().get("url")

        embed = Embed(
            title="Link your account",
            description=(f"[Click here to link your Discord]({url})\n\n"
                        "Log in on the website and your account will be connected. "
                        "The link expires in 15 minutes."),
            color=BLUE,
        )
        await ctx.send(embed=embed, ephemeral=True)
