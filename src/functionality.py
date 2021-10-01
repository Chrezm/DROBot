# -*- coding: utf-8 -*-
import discord
import time
import csv
from discord.ext import commands, tasks

from typing import Dict, List

from src import bans
from src import roles
from src import roleplays

class Functionality:
    def __init__(self, bot: commands.Bot = None, guild_details: Dict = None):
        @bot.event
        async def on_ready():
            # This is to start the checks and if said file does not exist, will create one.
            bans.ban_id_check()
            roleplays.rp_id_check()

            # This is to begin the task loop.
            second_passing.start()
            print('Logged in as {0.user}'.format(bot))

        # This is a task loop, where it will self-update every 10 minutes.
        @tasks.loop(seconds=600.0)
        async def second_passing():
            roleplays.update_rp_list()
            await bans.inform_update_list(bot)

        # This will execute before the function <second_passing> will run.
        @second_passing.before_loop
        async def inform_check():
            print('The Ten-Minute Self-Update is now Running.')

        @bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                await ctx.send('`Unrecognized command.`')

            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send("`Please input the required arguments.`")

            raise error

        @bot.event
        async def on_message(message):
            # Looks through the ban_id.csv
            ban_id_ = bans.ban_id_check()

            if message.author == bot.user:
                return

            if message.channel.name in guild_details.relaying_channels:
                # Right here, it will delete the message and notify the user who tried using the
                # bot that they are banned.
                for user in ban_id_:
                    if message.author.id == user["discord_id"] and not int(user["ended"]):
                        await message.delete(message)
                        return await message.author.send("**You cannot use the bot due to your "
                                                         "ban.**")

                await _relay_message(
                    message,
                    prefix=guild_details.relaying_prefix,
                    suffix=guild_details.relaying_suffix)

            await bot.process_commands(message)

        # -- Functions Area -- #

        def _get_channel(name):
            channel = discord.utils.get(bot.get_all_channels(), name=name)
            if not channel:
                raise ValueError(f'Target channel {name} not found.')
            return channel

        def _validate_command(ctx: commands.Context) -> bool:
            if ctx.author == bot.user:
                return False

            if ctx.channel.name in guild_details.command_channels:
                return True

            for role in ctx.author.roles:
                if role.id == guild_details.bot_maintainer_role_id:
                    return True
                if role.id in guild_details.command_always_accept_from_roles:
                    return True

            return False

        async def _relay_message(message, prefix='', suffix=''):
            for role in message.author.roles:
                if role.id in guild_details.relaying_ignore_roles:
                    return

            to_channel_name = guild_details.relaying_channels[message.channel.name]
            to_channel = _get_channel(to_channel_name)

            user = f'{message.author.name}#{message.author.discriminator} (<@{message.author.id}>)'

            final_message = (
                f'**RELAYED MESSAGE**\r\n'
                f'**User**: {user}\r\n'
                f'**Channel**: <#{message.channel.id}>\r\n'
                f'**Time**: {message.created_at}\r\n'
                f'**Message**: {message.content}\r\n'
            )
            if prefix:
                final_message = f'{prefix}\r\n{final_message}'
            if suffix:
                final_message += f'{suffix}'

            await message.delete()
            await to_channel.send(final_message)

        # Checks Admin Status
        def _check_bot_admin(ctx) -> bool:
            # Bot Maintainer always gets privilege
            for role in ctx.author.roles:
                if role == guild_details.bot_maintainer_role_id:
                    return True

            # Otherwise, check if user has admin privilges
            admin_roles = [role for role in ctx.guild.roles if role.permissions.administrator]
            for admin_role in admin_roles:
                if admin_role in ctx.author.roles:
                    return True

            return False

        def timezone_time_check(hour_change: int, inc_time: int):
            hour_change = hour_change + inc_time

            if hour_change > 23:
                hour_change = hour_change - 24
                if len(str(hour_change)) < 2:
                    hour_change = f"0{hour_change}"

            elif hour_change < 0:
                hour_change = hour_change + 24
                if len(str(hour_change)) < 2:
                    hour_change = f"0{hour_change}"

            if len(str(hour_change)) < 2:
                hour_change = f"0{hour_change}"

            return hour_change

        # -- Commands Area -- #

        @bot.command(
            name='ban_id',
            brief='Bans a Discord User from using the Bot.',
            help=('Bans a Discord User from using the Bot. There are multiple arguments needed to be '
                  'filled.'
                  '\nArguments: $ban_id <user_id> <ban_length : seconds> <reason> '
                  '\nExample: $ban_id 332456386946531328 259200 "There must be a open and close '
                  'quotes for reason."')
        )
        async def ban_id(ctx: commands.Context, user_id: int, ban_length: int = 259200,
                         reason="Unstated Reason"):
            if not _validate_command(ctx):
                return

            if not _check_bot_admin(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            await bans.command_ban_id(bot, guild_details, ctx, user_id, ban_length=ban_length,
                                      reason=reason)

        @bot.command(
            name='unban',
            brief='Unbans a Discord User from using the Bot.',
            help=('Unbans a Discord User from using the Bot. There is only a single argument needed '
                  'to be filled.'
                  '\nArguments: $unban <discord_id>'
                  '\nExample: $unban 332456386946531328'),
        )
        async def unban(ctx: commands.Context, _id: int):
            if not _validate_command(ctx):
                return

            if not _check_bot_admin(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            await bans.unban(bot, guild_details, ctx, _id)

        @bot.command(
            name='ban_profile',
            brief='Returns a profile of the banned user.',
            help=('Returns a profile of the banned user. There is only a single mandatory argument '
                  'needed to be filled.'
                  '\nArguments: $ban_profile <discord_id> <_all>'
                  '\nExample: $ban_profile 332456386946531328 False'
                  "\n\n<_all> is optional, but it must be a boolean of either True or False. "
                  "\nFalse only returns the user's recent ban."
                  "\nTrue returns all of the user's bans."),
        )
        async def ban_profile(ctx: commands.Context, _id: int, _all=False):
            if not _validate_command(ctx):
                return

            if not _check_bot_admin(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            await bans.command_ban_profile(bot, guild_details, _id, _all=_all)

        @bot.command(
            name='ban_profile_all',
            brief='Returns all ban profiles from all banned or previously banned users.',
            help=('Returns all ban profiles from all banned or previously banned users. An argument '
                  'is not necessary.'
                  '\nArguments: $ban_profile_all'
                  '\nExample: $ban_profile_all')
        )
        async def ban_profile_all(ctx: commands.Context):
            if not _validate_command(ctx):
                return

            if not _check_bot_admin(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            await bans.command_ban_profile_all(bot, guild_details, ctx)

        @bot.command(
            name='ban_list_update',
            brief='Forces the ban_list to update.',
            help=('Forces the ban_list to update. You do not need any arguments to proceed.'
                  '\nArguments: $ban_list_update'
                  '\nExample: $ban_list_update'),
        )
        async def ban_list_update(ctx: commands.Context):
            if not _validate_command(ctx):
                return

            if not _check_bot_admin(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            await bans.command_ban_list_update(bot, guild_details, ctx)

        @bot.command(
            name='add_roleplay',
            brief='Adds a roleplay into the Database.',
            help=('Adds a roleplay into the Database. There are a lot of arguments needed to be '
                  'filled; ensure you do "open and close" quotes IF they are not integers.'
                  '\nArguments: $add_roleplay <rp_name> <main_host_id> <rp_start_date> '
                  '<rp_duration> <doc> '
                  '<serial_code: optional> <local: optional> <sign_up: optional> '
                  '<ongoing: optional> <ended: optional>'
                  '\nExample: $add_roleplay "Helvetica Neue" 332456386946531328 42069 5 '
                  '"https://www.epochconverter.com"'
                  '"HN" 1 0 0'
                  "\n\n<main_host_id> is the Main Host's Discord ID."
                  "\n<rp_start_date> is an epoch number. Use https://www.epochconverter.com"
                  "\n<rp_duration> is an integer. In hours, how long the Roleplay is."
                  "\n<serial_code> is an optional field, but can be customized. It is used to find "
                  "your RP in [rp_profile] and store in the database."
                  "\n<local> is an optional field, can only be 0 or 1. --0: False "
                  "(Hosted outside ODROS) | 1: True (Hosted within ODROS)--"
                  "\n<sign_up> is an optional field, can only be 0 or 1. --0: False "
                  "(Sign ups are closed) | 1: True (Sign ups are open)--"
                  "\n<ongoing> is an optional field, can only be 0 or 1. --0: False "
                  "(RP is not ongoing) | 1: True (RP is ongoing)--"
                  "\n<ended> is an optional field, can only be 0 or 1. --0: False "
                  "(RP has not ended) | 1: True (RP ended)--"),
        )
        async def add_roleplay(ctx: commands.Context, rp_name, main_host_id: int,
                               rp_start_date: int, rp_duration: int, doc, serial_code=None,
                               local: int = 1, sign_up: int = 1, ongoing: int = 0, ended: int = 0):
            if not _validate_command(ctx):
                return

            if not _check_bot_admin(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            await roleplays.command_add_roleplay(
                bot, guild_details, ctx, rp_name, main_host_id, rp_start_date, rp_duration, doc,
                serial_code=serial_code, local=local, sign_up=sign_up, ongoing=ongoing, ended=ended,
                )

        @bot.command(
            name='rp_profile',
            brief='Returns a profile of an RP.',
            help=('Returns a profile of an RP. There is only one required argument.'
                  '\nArguments: $rp_profile <_id>'
                  '\nExample: $rp_profile HN'
                  '\n\n<_id> is the Serial Code of said RP. It is case sensitive, so make sure it is '
                  'correct.')
        )
        async def rp_profile(ctx: commands.Context, _id: str):
            if not _validate_command(ctx):
                return

            await roleplays.command_rp_profile(bot, guild_details, ctx, _id)

        @bot.command(
            name='rp_profile_filter',
            brief='Returns a list of RP profiles that are filtered.',
            help=('Returns a list of RP profiles that are filtered based on value of 0-3'
                  '\nArguments: $rp_profile_filter <value>'
                  '\nExample: $rp_profile_filter 0'
                  '\n\n<value> is the code for filter action.'
                  '\n0 - Filters RP profiles whose Sign Ups are Open.'
                  '\n1 - Filters RP profiles which are currently Ongoing.'
                  '\n2 - Filters RP Profiles which have ended.'
                  '\n3 - Does not filter and returns all RP profiles.')
        )
        async def rp_profile_filter(ctx: commands.Context, value="0"):
            if not _validate_command(ctx):
                return

            await roleplays.command_rp_profile_filter(bot, guild_details, ctx, value=value)

        @bot.command(
            name='rp_change_status',
            brief='Changes RP status.',
            help=('Changes RP status based on the value of 0-3'
                  '\nArguments: $rp_change_status <_id> <value>'
                  '\nExample: $rp_change_status HN 0'
                  '\n\n<_id> is the Serial Code for the RP; the one you are planning to change.'
                  '\n<value> is the code for status change action.'
                  '\n0 - Closes Sign Ups.'
                  '\n1 - Opens Sign Ups.'
                  '\n2 - Labels the RP as Ongoing.'
                  '\n3 - Ending the RP.')
        )
        async def rp_change_status(ctx: commands.Context, _id, value="0"):
            if not _validate_command(ctx):
                return

            if not _check_bot_admin(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            await roleplays.command_rp_change_status(bot, guild_details, ctx, _id, value=value)

        @bot.command(
            name='ping',
            brief='Returns Pong. Used to check if the bot is up and running',
            help=('Returns Pong. If the bot does not respond, it means it is down or something '
                  'terrible has happened.'
                  '\nArguments: $ping'
                  '\nExample: $ping'),
        )
        async def ping(ctx: commands.Context):
            if not _validate_command(ctx):
                return

            await ctx.channel.send('Pong.')

        @bot.command(
            name='rpactive',
            brief='Changes your RP Active status',
            help=('If you did not have the RP Active role, the bot will give it to you. If you '
                  'already had it, the bot will take it away from you.'
                  '\nArguments: $rpactive'
                  '\nExample: $rpactive'),
        )
        async def rpactive(ctx: commands.Context):
            if not _validate_command(ctx):
                return

            await roles.command_rpactive(bot, guild_details, ctx)

        @bot.command(
            name='devtester',
            brief='Changes your Dev Tester status',
            help=('If you did not have the Dev Tester role, the bot will give it to you. If you '
                  'already had it, the bot will take it away from you.'
                  '\nArguments: $devtester'
                  '\nExample: $devtester'),
        )
        async def devtester(ctx: commands.Context):
            if not _validate_command(ctx):
                return

            await roles.command_devtester(bot, guild_details, ctx)

        @bot.command(
            name='timezone',
            brief='Lists the time based on <important> timezones.',
            help=('Lists the time based on <important> timezones. Date format: YYYY-MM-DD.'
                  '\nArguments: $timezone <seconds>'
                  '\nExample: $timezone HN'
                  '\n\n<seconds> is an optional field; it is an epoch/unix second argument. It can also be an RP Serial Code.'
                  "\nInputting <seconds> as an RP Serial Code will return you said RP's First Session Date."
                  )
        )
        async def timezone(ctx: commands.Context, seconds=None):
            if not _validate_command(ctx):
                return

            irl_time = None
            title_embed = None

            if not seconds:
                seconds = round(time.time())

            try:
                seconds = int(seconds)
                try:
                    irl_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(seconds))
                except OSError:
                    return await ctx.send("`Integer cannot be over 2,147,483,647`")

                title_embed = f'It is {irl_time} UTC'
            except ValueError:
                rp_list = roleplays.rp_id_check()
                for rp in rp_list:
                    if seconds == rp["serial_code"]:
                        irl_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(rp["rp_start_date"])))
                        title_embed = f'RP Hosted at {irl_time} UTC'

                if not irl_time:
                    return await ctx.send("`Invalid RP Serial Code`")

            other_timezones = str(irl_time)
            other_timezones = other_timezones.split(" ")
            hour_split = other_timezones[1].split(":")
            hour_change = int(hour_split[0])
            text_ = [
                "**-- Standard Time --**",
                f"**EST**: {timezone_time_check(hour_change, -5)}:{hour_split[1]}:{hour_split[2]}",
                f"**CST**: {timezone_time_check(hour_change, -6)}:{hour_split[1]}:{hour_split[2]}",
                f"**MST**: {timezone_time_check(hour_change, -7)}:{hour_split[1]}:{hour_split[2]}",
                f"**PST**: {timezone_time_check(hour_change, -8)}:{hour_split[1]}:{hour_split[2]}",
                "**-- Daylight Time --**",
                f"**EDT**: {timezone_time_check(hour_change, -4)}:{hour_split[1]}:{hour_split[2]}",
                f"**CDT**: {timezone_time_check(hour_change, -5)}:{hour_split[1]}:{hour_split[2]}",
                f"**MDT**: {timezone_time_check(hour_change, -6)}:{hour_split[1]}:{hour_split[2]}",
                f"**PDT**: {timezone_time_check(hour_change, -7)}:{hour_split[1]}:{hour_split[2]}",
                "**-- Europe Time --**",
                f"**UTC-1**: {timezone_time_check(hour_change, -1)}:{hour_split[1]}:{hour_split[2]}",
                f"**UTC**: {timezone_time_check(hour_change, 0)}:{hour_split[1]}:{hour_split[2]}",
                f"**UTC+1**: {timezone_time_check(hour_change, 1)}:{hour_split[1]}:{hour_split[2]}",
                f"**UTC+2**: {timezone_time_check(hour_change, 2)}:{hour_split[1]}:{hour_split[2]}",
                f"**UTC+3**: {timezone_time_check(hour_change, 3)}:{hour_split[1]}:{hour_split[2]}",
            ]

            text_ = "\n".join(text_)

            embed = discord.Embed(title=title_embed,
                                  description=f'{text_}',
                                  colour=discord.Color.dark_gold())
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.set_footer(text=ctx.author)

            await ctx.send(embed=embed)

        @bot.command(
            name='utc',
            brief='Lists the time for UTC timezones',
            help=('Lists the time for UTC timezones. There is an optional argument; if you input an '
                  'epoch/unix time after the command, '
                  'you will get said time instead. Date format: YYYY-MM-DD.'
                  '\nArguments: $utc <seconds>'
                  '\nExample: $utc 1'
                  '\n\n<seconds> is an optional field; it is an epoch/unix second argument and MUST '
                  'be an integer.')
        )
        async def utc(ctx: commands.Context, seconds=None):
            if not _validate_command(ctx):
                return

            if not seconds:
                seconds = round(time.time())

            try:
                seconds = int(seconds)
                try:
                    irl_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(seconds))
                except OSError:
                    return await ctx.send("`Integer cannot be over 2,147,483,647`")
            except ValueError:
                return await ctx.send("`You can only input integers as an argument.`")

            other_timezones = str(irl_time)
            other_timezones = other_timezones.split(" ")
            hour_split = other_timezones[1].split(":")
            text_ = []

            for i in range(1, 13):
                hour_change = int(hour_split[0]) + i
                hour_change_negative = hour_change - (i * 2)

                if hour_change > 23:
                    hour_change = (int(hour_split[0]) + i) - 24
                    if len(str(hour_change)) < 2:
                        hour_change = f"0{hour_change}"

                if len(str(hour_change)) < 2:
                    hour_change = f"0{hour_change}"

                if hour_change_negative < 0:
                    hour_change_negative = hour_change_negative + 24
                    if len(str(hour_change_negative)) < 2:
                        hour_change_negative = f"0{hour_change_negative}"

                if len(str(hour_change_negative)) < 2:
                    hour_change_negative = f"0{hour_change_negative}"

                other_tz = f"**UTC+{i} | -{i}**: {hour_change}:{hour_split[1]}:{hour_split[2]} | {hour_change_negative}:{hour_split[1]}:{hour_split[2]}"
                text_.append(other_tz)

            text_ = "\n".join(text_)

            embed = discord.Embed(title=f'It is {irl_time} UTC',
                                  description=f'{text_}',
                                  colour=discord.Color.dark_blue())
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.set_footer(text=ctx.author)

            await ctx.send(embed=embed)

        # -- Command Error Area -- #

        @ban_profile.error
        async def ban_profile_error(ctx: commands.Context, error):
            if isinstance(error, commands.BadBoolArgument):
                return await ctx.send("`Please input <_all> as either 0, 1 or False, True "
                                      "respectively.`")

            if isinstance(error, commands.BadArgument):
                return await ctx.send("`Please input <_id> as an integer, their Discord ID.`")

        @add_roleplay.error
        async def add_roleplay_error(ctx: commands.Context, error):
            if isinstance(error, commands.BadArgument):
                return await ctx.send("`Please input <main_host_id>, <rp_start_date>, <rp_duration>, "
                                      "<local>, <sign_up>, <ongoing>, and <ended> as integers.`")

        @ban_id.error
        async def ban_id_error(ctx: commands.Context, error):
            if isinstance(error, commands.BadArgument):
                return await ctx.send("`Please input <user_id> <ban_length> as integers.`")

        @unban.error
        async def unban_error(ctx: commands.Context, error):
            if isinstance(error, commands.BadArgument):
                return await ctx.send("`Please input <user_id> as integers.`")
