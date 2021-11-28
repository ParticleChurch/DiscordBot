'''
    https://github.com/Rapptz/discord.py/issues/5209#issuecomment-778118150
'''
import platform, asyncio
if platform.system() == 'Windows':
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

'''
    IMPORTS
'''
import os, time, pathlib
import discord
from discord.ext import commands
from discord.ext import tasks

LOCAL_DIRECTORY = pathlib.Path(__file__).parent
ACTIVITY_FILE = LOCAL_DIRECTORY / "active.txt"
API_TOKEN_FILE = LOCAL_DIRECTORY / "api_token.pkey"

'''
    ENSURE THAT THE BOT ISN'T ALREADY RUNNING
'''
try:
    with open(ACTIVITY_FILE, "r") as f:
        contents = f.read()
    if time.time() - float(contents) < 30:
        print("Bot is already running elsewhere.")
        quit()
except (OSError, ValueError) as e:
    pass # file doesn't exist or is invalid (bot isn't running)

'''
    THE BOT
'''
#
# TODO: get this from environ
with open(API_TOKEN_FILE, "r") as file:
    DISCORD_API_TOKEN = file.read()
CMD_PREFIX = ";"
bot = commands.Bot(command_prefix = CMD_PREFIX)

'''
    COMMAND UTILS
'''
def color(r, g, b):
    return r << 16 | g << 8 | b

def get_cmds_embed():
    embed = discord.Embed(color = color(0, 0, 0))
    embed.add_field(name = f"{CMD_PREFIX}cmds", value = "@everyone\nSend this message.", inline = False)
    embed.add_field(name = f"{CMD_PREFIX}ping", value = "@everyone\nReply \"Pong!\".", inline = False)
    embed.add_field(name = f"{CMD_PREFIX}purge `count`", value = "<@&794044623353937951>\nDelete the most recent `count` messages in this channel.", inline = False)
    embed.add_field(name = f"{CMD_PREFIX}reboot", value = "<@&794044623353937951>\nReboots the bot. Will take up to a minute to start back up.", inline = False)
    return embed

'''
    COMMANDS
'''
@bot.command()
async def cmds(ctx):
    await ctx.reply(embed = get_cmds_embed(), mention_author = False)

@bot.command()
async def ping(ctx):
    await ctx.reply("Pong!", mention_author = False)

@bot.command()
@commands.has_role("Moderator")
async def purge(ctx, message_count: int):
    await ctx.channel.purge(limit = message_count + 1)
    await ctx.channel.send(
        f"{message_count} {'message was' if message_count == 1 else 'messages were'} just purged by {ctx.author.mention}.",
        allowed_mentions = discord.AllowedMentions(users = [])
    )

@bot.command()
@commands.has_role("Moderator")
async def reboot(ctx):
    await ctx.reply("Goodbye! I should be back shortly...", mention_author = False)
    await bot.close()

'''
    EVENTS
'''
@bot.event
async def on_message(message):
    if message.channel.id in (794035889171857438, 794035546291961896):
        await message.add_reaction("\N{Thumbs Up Sign}")
        await message.add_reaction("\N{Thumbs Down Sign}")
        return

    if bot.user in message.mentions:
        await message.channel.send(
            f"Hi {message.author.mention}! My prefix is `{CMD_PREFIX}`, try sending `{CMD_PREFIX}cmds` to see what I can do.",
            reference = message,
            mention_author = True
        )
    
    await bot.process_commands(message)

'''
    LOGGING/TASKS
'''
class ChannelGetter:
    def __init__(self, id_):
        self.id_ = id_
        self.channel = None
    
    def __get__(self, obj, objtype = None):
        self.channel = self.channel or bot.get_channel(self.id_)
        return self.channel

class Channels:
    log = ChannelGetter(914522904690049084)

# write the current time to file, and ensure that no instance of the bot is currently running
last_logged_active_value = None
@tasks.loop(seconds = 1)
async def activity_logger():
    global last_logged_active_value
    
    try:
        if last_logged_active_value is not None:
            with open(ACTIVITY_FILE, "r") as f:
                assert last_logged_active_value == f.read(), "Another bot has overwritten the activity file."
            
        with open(ACTIVITY_FILE, "w") as f:
            last_logged_active_value = str(time.time())
            f.write(last_logged_active_value)
        
    except Exception as e:
        # just log out and allow another instance to start up
        # that's a better solution than allowing multiple instances to exist
        await bot.close()

# this will be used for something eventually...
@tasks.loop(seconds = 10)
async def message_logger():
    if not Channels.log: return

    # await Channels.log.send("I'm logging something")

'''
    RUN
'''
activity_logger.start()
message_logger.start()
bot.run(DISCORD_API_TOKEN)
