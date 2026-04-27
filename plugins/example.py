"""Hot-reload command example.

Edit this file while the bot is running, then send "ping" again.
The bot reloads this plugin without logging in again.
"""


def handle(ctx):
    if ctx.cmd == "ping":
        ctx.reply("pong")
        return True
    return False
