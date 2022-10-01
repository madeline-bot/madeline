import datetime
import logging
import os

import sentry_sdk
from dotenv import load_dotenv
from naff import Client, Embed, InteractionContext, listen, logger_name, Task, IntervalTrigger
from naff.client.errors import CommandCheckFailure, CommandOnCooldown
from pymongo import MongoClient

load_dotenv()

cluster = MongoClient(os.getenv("MONGODB_URL"))

context = cluster["madeline"]["context"]
error_logs = cluster["madeline"]["error"]


class CustomClient(Client):
    """Subclass of naff.Client with our own customized methods"""

    # you can use that logger in all your extensions
    logger = logging.getLogger(logger_name)

    # sentry sdk init
    sentry_sdk.init(
        os.getenv("SENTRY_DSN"),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
    )

    async def on_command_error(self, ctx, error):
        """Gets triggered on a command error"""
        if isinstance(error, CommandCheckFailure):
            errs = {
                "time": datetime.datetime.utcnow(),
                "guild_id": ctx.guild_id,
                "author_id": ctx.author.id,
                "error": f"{error}",
            }
            error_logs.insert_one(errs)

            if isinstance(ctx, InteractionContext):
                symbol = "/"

            await ctx.send(
                embeds=Embed(
                    description="<:cross:839158779815657512> I'm afraid I can't let you use that",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            self.logger.warning(
                f"Check failed on Command: [{symbol}{ctx.invoke_target}]"
            )

        elif isinstance(error, CommandOnCooldown):
            errs = {
                "time": datetime.datetime.utcnow(),
                "guild_id": ctx.guild_id,
                "author_id": ctx.author.id,
                "error": f"{error}",
            }
            error_logs.insert_one(errs)

            if isinstance(ctx, InteractionContext):
                symbol = "/"

            await ctx.send(
                embeds=Embed(
                    description=f"<:cross:839158779815657512> Cooldown is active for this command. You'll be able to use it in {int(error.cooldown.get_cooldown_time())} seconds",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            self.logger.warning(
                f"Cooldown Error on Command: [{symbol}{ctx.invoke_target}] for {int(error.cooldown.get_cooldown_time())} seconds"
            )

    async def on_command(self, ctx):
        """Gets triggered on a command"""
        if isinstance(ctx, InteractionContext):
            symbol = "/"

        errs = {
            "time": datetime.datetime.utcnow(),
            "guild_id": ctx.guild_id,
            "author_id": ctx.author.id,
            "cmd_name": f"{symbol}{ctx.invoke_target}",
            "cmd_args": f"{ctx.args}",
            "cmd_kwargs": f"{ctx.kwargs}",
        }
        context.insert_one(errs)

        self.logger.info(
            f"Command: [{symbol}{ctx.invoke_target}] was executed with {ctx.args = } | {ctx.kwargs = }"
        )

    async def on_startup(self):
        """Gets triggered on startup"""

        self.presence_changes.start()
        
        self.logger.info(f"{os.getenv('PROJECT_NAME')} - Startup Finished!")
        self.logger.info(
            "Note: Discord needs up to an hour to load global commands / context menus. They may not appear immediately\n"
        )

    @Task.create(IntervalTrigger(seconds=30))
    async def presence_changes(self):
        await self.bot.change_presence(
            status=Status.ONLINE,
            activity=Activity(
                name=f"{len(self.bot.guilds)} servers | /help",
                type=ActivityType.COMPETING,
            ),
        )