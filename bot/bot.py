# Bot entry point — loads command extensions and connects to Discord. Run with `python bot.py` on the Pi / home server.
import os

import interactions
from dotenv import load_dotenv

load_dotenv()

bot = interactions.Client(token=os.environ["DISCORD_BOT_TOKEN"])

EXTENSIONS = [
    "commands.market",
    "commands.portfolio",
    "commands.account",
]


@interactions.listen()
async def on_startup():
    print(f"Logged in as {bot.user}")


if __name__ == "__main__":
    for ext in EXTENSIONS:
        bot.load_extension(ext)
    bot.start()
