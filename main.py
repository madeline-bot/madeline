import os

from dotenv import load_dotenv
from naff import Activity, ActivityType, Intents, Status
from naff.ext.debug_extension import DebugExtension

from core.base import CustomClient
from core.extensions_loader import load_extensions
from core.logging import init_logging

if __name__ == "__main__":
    # load the environmental vars from the .env file
    load_dotenv()

    # initialise logging
    init_logging()

    # create our bot instance
    bot = CustomClient(
        intents=Intents.DEFAULT,  # intents are what events we want to receive from discord, `DEFAULT` is usually fine
        # auto_defer=True,  # automatically deferring interactions
        status=Status.IDLE,
        #activity=Activity(
        #    name=f"(loading) servers | /about", type=ActivityType.COMPETING
        #),  # the status message of the bot
        sync_interactions=True,  # sync application commands with discord
        delete_unused_application_cmds=True,  # Delete commands that arent listed here
    )

    # load the debug extension if that is wanted
    if os.getenv("LOAD_DEBUG_COMMANDS") == "true":
        DebugExtension(bot=bot)

    # load all extensions in the ./extensions folder
    load_extensions(bot=bot)

    # start the bot
    bot.start(os.getenv("DISCORD_TOKEN"))
