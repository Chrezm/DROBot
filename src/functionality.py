# -*- coding: utf-8 -*-
import os
import tempfile
import discord
import time
import calendar
import datetime
import csv
import string
import random
import asyncio
import re
import requests
import subprocess

from collections import Counter
from discord.ext import commands, tasks

from typing import Dict, Any, List, Union, Tuple

from src.guild import Guild
from src.timezone_list import timezone_list

ban_ids_type = List[Dict[Union[str, Any], Union[str, Any]]]

# This is a string generator for RP Serial Codes. But it can be used for something more in the future.
def create_code():
    lowercase_letter, uppercase_letter, digits = string.ascii_lowercase, string.ascii_uppercase, str(string.digits)
    code = ''.join(random.sample(lowercase_letter + uppercase_letter + digits, 12))
    return code


# Checking Value for Command Hammertime
def check_value(list_):
    proceed = list()
    new_list = list()
    note_ = str()
    progress = True

    for _ in list_:
        try:
            _ = _.strip()
            new_ = int(_)
            new_list.append(new_)
        except Exception as e:
            progress, note_ = False, e

    proceed.append([progress, note_])
    return proceed, new_list


# This is the initial check for ban_ids.csv and obtaining its data.
def ban_id_check() -> ban_ids_type:
    ban_list = None
    try:
        with open("ban_ids.csv", "r+", newline="") as file:
            reader = csv.DictReader(file)
            ban_list = []
            for x in reader:
                ban_list.append(x)

            return ban_list

    except FileNotFoundError:
        with open("ban_ids.csv", "w") as file:
            print("ban_ids.csv does not exist; the bot will now create one...")
            fieldnames = ["discord_id", "discord_name", "ban_timestamp", "ban_length", "reason", "ended"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

    return ban_list

# This is the initial check for msg_list.csv and obtaining its data.
def msg_check():
    msg_list = None
    try:
        with open("msg_list.csv", "r+", newline="") as file:
            reader = csv.DictReader(file)
            msg_list = []
            for x in reader:
                msg_list.append(x)

            return msg_list

    except FileNotFoundError:
        with open("msg_list.csv", "w") as file:
            print("msg_list.csv does not exist; the bot will now create one...")
            fieldnames = ["discord_id", "discord_name", "link", "message"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

    return msg_list

# This is the initial check for rp_collection.csv and obtaining its data.
def rp_id_check():
    rp_list = None
    try:
        with open("rp_collection.csv", "r+", newline="") as file:
            reader = csv.DictReader(file)
            rp_list = []
            for x in reader:
                rp_list.append(x)

            return rp_list

    except FileNotFoundError:
        with open("rp_collection.csv", "w") as file:
            print("rp_collection.csv does not exist; the bot will now create one...")
            fieldnames = ["serial_code", "approved", "approved_id", "local", "rp_name", "main_host", "main_host_id",
                          "rp_start_date", "rp_start_time", "rp_duration", "doc", "sign_up", "ongoing", "ended"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

    return rp_list


class Functionality:
    def __init__(self, bot: commands.Bot = None, guild_details: Guild = None):
        @bot.event
        async def on_ready():
            # This is to start the checks and if said file does not exist, will create one.
            ban_id_check()
            rp_id_check()
            msg_check()

            # This is to begin the task loop.
            second_passing.start()
            print('Logged in as {0.user}'.format(bot))

        # This is a task loop, where it will self-update every 10 minutes.
        @tasks.loop(seconds=600.0)
        async def second_passing():
            _update_rp_list()

            with open("msg_list.csv", "w") as file:
                fieldnames = ["discord_id", "discord_name", "link", "message"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()

            await _inform_update_list()

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
        async def on_message(message: discord.Message):
            if message.author == bot.user:
                return

            await _check_url(message)

            if await _check_sent_in_honeypot_channel(message):
                return

            # Looks through the ban_id.csv
            ban_id_ = ban_id_check()

            if await _check_sent_in_relaying_channel(message, ban_id_):
                return

            await bot.process_commands(message)

        async def _check_url(message: discord.Message):
            regex_url = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(regex_url, message.content.lower())
            if urls:
                await _msg_update(message.author.id, message.author.name, urls, message.content, message)

        async def _check_sent_in_honeypot_channel(message: discord.Message) -> bool:
            if message.channel.name not in guild_details.honeypot_channels():
                return False

            muted_role = discord.utils.get(message.author.guild.roles,
                                           name=guild_details.bot_muted_role_name())
            user = message.author
            has_muted_role = False

            for role in user.roles:
                if role.id == guild_details.bot_muted_role_id():
                    has_muted_role = True

            if has_muted_role:
                await message.author.send(f'You are Muted from this server. You cannot send any messages.')
            else:
                await user.add_roles(muted_role)
                await message.author.send(f'You are now Muted for spamming reasons.')

            await _relay_message(
                message,
                prefix=guild_details.relaying_prefix(),
                suffix=guild_details.relaying_suffix())

            await message.delete()
            return True

        async def _check_if_banned(message: discord.Message, ban_id_: ban_ids_type) -> bool:
            # Right here, it will delete the message and notify the user who tried using the bot that they are banned.
            for user in ban_id_:
                if message.author.id == user["discord_id"] and not int(user["ended"]):
                    await message.delete(message)
                    await message.author.send("**You cannot use the bot due to your ban.**")
                    return True

            return False

        async def _check_sent_in_relaying_channel(message: discord.Message,
                                                  ban_id_: ban_ids_type) -> bool:
            if message.channel.name not in guild_details.relaying_channels():
                return False

            if await _check_if_banned(message, ban_id_):
                return True

            await _relay_message(
                message,
                prefix=guild_details.relaying_prefix(),
                suffix=guild_details.relaying_suffix())
            return True

        # -- Functions Area -- #

        def _get_channel(name: str) -> discord.TextChannel:
            channel = discord.utils.get(bot.get_all_channels(), name=name)
            if not channel:
                raise ValueError(f'Target channel {name} not found.')
            return channel

        def _validate_command(ctx: commands.Context) -> bool:
            if ctx.author == bot.user:
                return False

            if ctx.channel.name in guild_details.command_channels():
                return True

            for role in ctx.author.roles:
                if role.id in guild_details.command_always_accept_from_roles():
                    return True

            return False

        async def _relay_message(message: discord.Message, prefix: str = '', suffix: str = ''):
            for role in message.author.roles:
                if role.id in guild_details.relaying_ignore_roles():
                    return

            to_channel_name = guild_details.relaying_channels()[message.channel.name]
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
        def _admin_check(ctx: commands.Context):
            admin_roles = [role for role in ctx.guild.roles if role.permissions.administrator]
            user_roles = ctx.author.roles
            dro_bot_maintainer_role = ctx.guild.get_role(892524724230434826)

            for role in user_roles:
                if role == dro_bot_maintainer_role:
                    return True

            for admin_role in admin_roles:
                if admin_role in ctx.author.roles:
                    return True

            return None

        # Converts Seconds to Days
        def _second_to_day(second: int) -> int:
            answer = second / 86400
            return round(answer)

        # Converts Seconds to Hours
        def _second_to_hour(second: int) -> int:
            answer = second / 3600
            return round(answer)

        # This is for the message checks because bots are smart nowadays.
        async def _msg_update(_id, name, link, message, user):
            with open("msg_list.csv", "a") as file:
                fieldnames = ["discord_id", "discord_name", "link", "message"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writerow({"discord_id": _id, "discord_name": name, "link": link, "message": message.lower()})

            return await _msg_counter(_id, user)

        async def _msg_counter(_id, person):
            msgs = msg_check()
            msg_list = list()

            for m in msgs:
                if str(_id) == m['discord_id']:
                    msg_list.append(m['message'])

            counter = Counter(msg_list)
            for k, v in counter.items():
                if v >= 3:
                    muted_role = discord.utils.get(person.author.guild.roles,
                                                   name=guild_details.bot_maintainer_role_name())

                    user = person.author
                    has_muted_role = False

                    for role in user.roles:
                        if role.id == guild_details.bot_muted_role_id():
                            has_muted_role = True

                    if not has_muted_role:
                        await user.add_roles(muted_role)
                        await person.author.send(f'You are now Muted for spamming reasons.')

        def _ban_profile_check(_id):
            ban_list = ban_id_check()
            found = []

            for user in ban_list:
                if str(_id) == user["discord_id"]:
                    found.append(user)

            return found

        def _ban_profile_check_all():
            ban_list = ban_id_check()
            found = []

            for ban in ban_list:
                found.append(ban)

            return found

        def _update_unban(_id):
            ban_ids = ban_id_check()
            updated_ban_list = list()
            inform_ban_list = list()  # This is to inform players when their ban is over.

            for user in ban_ids:
                if str(_id) == user["discord_id"]:
                    update_dict = {"discord_id": user["discord_id"], "discord_name": user["discord_name"], "ban_timestamp": user["ban_timestamp"],
                                   "ban_length": user["ban_length"], "reason": user["reason"], "ended": 1}

                    inform_ban_list.append(update_dict)

                else:
                    update_dict = user

                updated_ban_list.append(update_dict)

            with open("ban_ids.csv", "w+") as file:
                fieldnames = ["discord_id", "discord_name", "ban_timestamp", "ban_length", "reason", "ended"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()

                for update in updated_ban_list:
                    writer.writerow(update)

            return updated_ban_list, inform_ban_list

        def _update_ban_list():
            ban_ids = ban_id_check()
            updated_ban_list = list()
            inform_ban_list = list()  # This is to inform players when their ban is over.
            update_dict = None

            for user in ban_ids:
                answer = int(user["ban_timestamp"]) + int(user["ban_length"])
                answer = round(time.time()) - answer

                if answer >= 0:
                    if user["ended"] == "1":
                        update_dict = user

                    if user["ended"] == "0":
                        update_dict = {"discord_id": user["discord_id"], "discord_name": user["discord_name"], "ban_timestamp": user["ban_timestamp"],
                                       "ban_length": user["ban_length"], "reason": user["reason"], "ended": 1}

                        inform_ban_list.append(update_dict)

                else:
                    update_dict = user

                updated_ban_list.append(update_dict)

            with open("ban_ids.csv", "w+") as file:
                fieldnames = ["discord_id", "discord_name", "ban_timestamp", "ban_length", "reason", "ended"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()

                for update in updated_ban_list:
                    writer.writerow(update)

            return updated_ban_list, inform_ban_list

        async def _inform_update_list():
            updated_list = _update_ban_list()[1]

            if updated_list:
                for user in updated_list:
                    answer = int(user["ban_timestamp"]) + int(user["ban_length"])
                    answer = round(time.time()) - answer

                    if answer >= 0:
                        target = await bot.fetch_user(int(user['discord_id']))
                        await target.send(f'**You are now unbanned from using the Server Bot. Please do not make the same offense again.**')

        def _update_rp_list():
            rp_list = rp_id_check()
            updated_rp_list = list()
            update_dict = None

            for user in rp_list:
                answer = round(time.time()) - int(user["rp_start_date"])

                if answer >= 0:
                    if user["ongoing"] == "1":
                        update_dict = user

                    if user["ongoing"] == "0":
                        update_dict = {"serial_code": user['serial_code'], "approved": user['approved'], "approved_id": user['approved_id'], "local": user['local'],
                                       "rp_name": user['rp_name'], "main_host": user['main_host'], "main_host_id": user['main_host_id'], "rp_start_date": user['rp_start_date'],
                                       "rp_start_time": user['rp_start_time'], "rp_duration": user['rp_duration'], "doc": user['doc'],
                                       "sign_up": 0, "ongoing": 1, "ended": 0}

                else:
                    update_dict = user

                updated_rp_list.append(update_dict)

            with open("rp_collection.csv", "w+") as file:
                fieldnames = ["serial_code", "approved", "approved_id", "local", "rp_name", "main_host", "main_host_id",
                              "rp_start_date", "rp_start_time", "rp_duration", "doc", "sign_up", "ongoing", "ended"]

                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()

                for update in updated_rp_list:
                    writer.writerow(update)

            return updated_rp_list

        def _update_rp_list_choice(_id, val):
            change_dict = {
                0: [0, 0, 0],  # Close Sign Ups
                1: [1, 0, 0],  # Open Sign Ups
                2: [0, 1, 0],  # Ongoing RP
                3: [0, 0, 1]  # Ends RP
            }

            rp_list = rp_id_check()
            updated_rp_list = list()
            inform_update = list()

            for user in rp_list:
                value_change = change_dict[val]

                if str(_id) == user["serial_code"]:
                    update_dict = {"serial_code": user['serial_code'], "approved": user['approved'], "approved_id": user['approved_id'], "local": user['local'],
                                   "rp_name": user['rp_name'], "main_host": user['main_host'], "main_host_id": user['main_host_id'], "rp_start_date": user['rp_start_date'],
                                   "rp_start_time": user['rp_start_time'], "rp_duration": user['rp_duration'], "doc": user['doc'],
                                   "sign_up": value_change[0], "ongoing": value_change[1], "ended": value_change[2]}

                    inform_update.append(update_dict)

                else:
                    update_dict = user

                updated_rp_list.append(update_dict)

            with open("rp_collection.csv", "w+") as file:
                fieldnames = ["serial_code", "approved", "approved_id", "local", "rp_name", "main_host", "main_host_id",
                              "rp_start_date", "rp_start_time", "rp_duration", "doc", "sign_up", "ongoing", "ended"]

                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()

                for update in updated_rp_list:
                    writer.writerow(update)

            return updated_rp_list, inform_update

        def _rp_profile_check(_id):
            rp_list = rp_id_check()
            found = []

            for rp in rp_list:
                if str(_id) == rp["serial_code"]:
                    found.append(rp)

            return found

        def _rp_profile_check_sign_up(val):
            if val != 0:
                return

            rp_list = rp_id_check()
            found = []

            for rp in rp_list:
                if rp["sign_up"] == "1":
                    found.append(rp)

            return found

        def _rp_profile_check_ongoing(val):
            if val != 1:
                return

            rp_list = rp_id_check()
            found = []

            for rp in rp_list:
                if rp["ongoing"] == "1":
                    found.append(rp)

            return found

        def _rp_profile_check_ended(val):
            if val != 2:
                return

            rp_list = rp_id_check()
            found = []

            for rp in rp_list:
                if rp["ended"] == "1":
                    found.append(rp)

            return found

        def _rp_profile_check_all(val):
            if val != 3:
                return

            rp_list = rp_id_check()
            found = []

            for rp in rp_list:
                found.append(rp)

            return found

        def _timezone_time_check(hour_change: int, inc_time: int):
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
            help=('Bans a Discord User from using the Bot. There are multiple arguments needed to be filled.'
                  '\nArguments: $ban_id <user_id> <ban_length : seconds> <reason> '
                  '\nExample: $ban_id 332456386946531328 259200 "There must be a open and close quotes for reason."')
        )
        async def ban_id(ctx: commands.Context, user_id: int, ban_length: int = 259200, reason="Unstated Reason"):
            if not _validate_command(ctx):
                return

            if not _admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            ban_ids = ban_id_check()

            try:
                target = await bot.fetch_user(user_id)
            except discord.NotFound as p:
                return await ctx.send(f"`{p}`\n**Please input a valid Discord ID that is in the server.**")

            for dict_ban in ban_ids:
                if str(user_id) == str(dict_ban["discord_id"]) and not int(dict_ban["ended"]):
                    return await ctx.send(f"**{target.name} is already in the list and his ban has not ended.**")

            with open("ban_ids.csv", "a") as file_:
                fieldnames = ["discord_id", "discord_name", "ban_timestamp", "ban_length", "reason", "ended"]
                writer = csv.DictWriter(file_, fieldnames=fieldnames)
                writer.writerow({"discord_id": user_id, "discord_name": target.name, "ban_timestamp": round(time.time()), "ban_length": ban_length, "reason": reason, "ended": 0})

            if ban_length < 86400:
                days = _second_to_hour(ban_length)
                word_ = f"{days} hours"

            else:
                days = _second_to_day(ban_length)
                word_ = f"{days} days"

            await ctx.channel.send(f'**{target.name} ({user_id}) is now banned from using the Server Bot for {word_}.**'
                                   f'\n`Reason: {reason}`')
            await target.send(f'**You are now banned from using the Server Bot for {word_}**'
                              f'\n`Reason: {reason}`')

        @bot.command(
            name='unban',
            brief='Unbans a Discord User from using the Bot.',
            help=('Unbans a Discord User from using the Bot. There is only a single argument needed to be filled.'
                  '\nArguments: $unban <discord_id>'
                  '\nExample: $unban 332456386946531328'),
        )
        async def unban(ctx: commands.Context, _id: int):
            if not _validate_command(ctx):
                return

            if not _admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            initial_check = _ban_profile_check(_id)
            if not initial_check:
                return await ctx.send("`Invalid Discord ID.`")

            updated_list = _update_unban(_id)
            updated_list = updated_list[1]

            for user in updated_list:
                target = await bot.fetch_user(int(user['discord_id']))
                await target.send(f'**You are now unbanned from using the Server Bot. Please do not make the same offense again.**')

            return await ctx.send("**Updated! Those whose ban is revoked will be notified.**")

        @bot.command(
            name='ban_profile',
            brief='Returns a profile of the banned user.',
            help=('Returns a profile of the banned user. There is only a single mandatory argument needed to be filled.'
                  '\nArguments: $ban_profile <discord_id> <_all>'
                  '\nExample: $ban_profile 332456386946531328 False'
                  "\n\n<_all> is optional, but it must be a boolean of either True or False. "
                  "\nFalse only returns the user's recent ban."
                  "\nTrue returns all of the user's bans."),
        )
        async def ban_profile(ctx: commands.Context, _id: int, _all=False):
            if not _validate_command(ctx):
                return

            if not _admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            profile = _ban_profile_check(_id)
            embed = None

            if not profile:
                return await ctx.send("`That ID does not exist in the database.`")

            for user in profile:
                date_ = time.strftime('%d-%B-%Y %H:%M:%S', time.gmtime(int(user["ban_timestamp"])))
                embed = discord.Embed(title=f'Ban Profile : {user["discord_name"]}',
                                      description=f'**Discord Name**: {user["discord_name"]}\n'
                                                  f'**Discord ID**: {user["discord_id"]}\n'
                                                  f'**Ban Date**: {date_}\n'
                                                  f'**Ban Length**: {_second_to_day(int(user["ban_length"]))}\n'
                                                  f'**Reason**: {user["reason"]}\n'
                                                  f'**Ban Ended**: {user["ended"]}',

                                      colour=discord.Color.dark_blue())
                embed.set_thumbnail(url=ctx.author.avatar.url)
                embed.set_footer(text=ctx.author)

                if _all:
                    await ctx.send(embed=embed)

            if not _all:
                await ctx.send(embed=embed)

        @bot.command(
            name='ban_profile_all',
            brief='Returns all ban profiles from all banned or previously banned users.',
            help=('Returns all ban profiles from all banned or previously banned users. An argument is not necessary.'
                  '\nArguments: $ban_profile_all'
                  '\nExample: $ban_profile_all')
        )
        async def ban_profile_all(ctx: commands.Context):
            if not _validate_command(ctx):
                return

            if not _admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            profile = _ban_profile_check_all()

            if not profile:
                return await ctx.send("`There are no bans in the Database.`")

            for user in profile:
                date_ = time.strftime('%d-%B-%Y %H:%M:%S', time.gmtime(int(user["ban_timestamp"])))
                embed = discord.Embed(title=f'Ban Profile : {user["discord_name"]}',
                                      description=f'**Discord Name**: {user["discord_name"]}\n'
                                                  f'**Discord ID**: {user["discord_id"]}\n'
                                                  f'**Ban Date**: {date_}\n'
                                                  f'**Ban Length**: {_second_to_day(int(user["ban_length"]))}\n'
                                                  f'**Reason**: {user["reason"]}\n'
                                                  f'**Ban Ended**: {user["ended"]}',

                                      colour=discord.Color.dark_blue())
                embed.set_thumbnail(url=ctx.author.avatar.url)
                embed.set_footer(text=ctx.author)

                await ctx.send(embed=embed)

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

            if not _admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            updated_list = _update_ban_list()[1]

            if updated_list:
                for user in updated_list:
                    answer = int(user["ban_timestamp"]) + int(user["ban_length"])
                    answer = round(time.time()) - answer

                    if answer >= 0:
                        target = await bot.fetch_user(int(user['discord_id']))
                        await target.send(f'**You are now unbanned from using the Server Bot. Please do not make the same offense again.**')

            await ctx.send("**Updated! Those whose ban is over will be notified.**")

        @bot.command(
            name='add_roleplay',
            brief='Adds a roleplay into the Database.',
            help=('Adds a roleplay into the Database. There are a lot of arguments needed to be filled; ensure you do "open and close" quotes IF they are not integers.'
                  '\nArguments: $add_roleplay <rp_name> <main_host_id> <rp_start_date> <rp_duration> <doc> '
                  '<serial_code: optional> <local: optional> <sign_up: optional> <ongoing: optional> <ended: optional>'
                  '\nExample: $add_roleplay "Helvetica Neue" 332456386946531328 42069 5 "https://www.epochconverter.com"'
                  '"HN" 1 0 0'
                  "\n\n<main_host_id> is the Main Host's Discord ID."
                  "\n<rp_start_date> is an epoch number. Use https://www.epochconverter.com"
                  "\n<rp_duration> is an integer. In hours, how long the Roleplay is."
                  "\n<serial_code> is an optional field, but can be customized. It is used to find your RP in [rp_profile] and store in the database."
                  "\n<local> is an optional field, can only be 0 or 1. --0: False (Hosted outside ODROS) | 1: True (Hosted within ODROS)--"
                  "\n<sign_up> is an optional field, can only be 0 or 1. --0: False (Sign ups are closed) | 1: True (Sign ups are open)--"
                  "\n<ongoing> is an optional field, can only be 0 or 1. --0: False (RP is not ongoing) | 1: True (RP is ongoing)--"
                  "\n<ended> is an optional field, can only be 0 or 1. --0: False (RP has not ended) | 1: True (RP ended)--"),
        )
        async def add_roleplay(ctx: commands.Context, rp_name, main_host_id: int, rp_start_date: int, rp_duration: int,
                               doc, serial_code=None, local: int = 1, sign_up: int = 1, ongoing: int = 0, ended: int = 0):
            if not _validate_command(ctx):
                return

            if not _admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            rp_list = rp_id_check()

            arg_check = [local, sign_up, ongoing, ended]
            for arg in arg_check:
                try:
                    arg = int(arg)
                    if arg not in [0, 1]:
                        return await ctx.send(f"`<Local>, <Sign Up>, <Ongoing>, and <Ended> Arguments must be either 0 or 1.`")
                except ValueError:
                    return await ctx.send(f"`Please input a valid integer. {arg} is not valid.`")

            if not serial_code:
                serial_code = create_code()

            for rp in rp_list:
                local_note = "in DRO servers"
                if rp["local"] == "0":
                    local_note = "outside of DRO servers"

                ongoing_note = "currently ongoing"
                if rp["ongoing"] == "0":
                    ongoing_note = "still on its sign up phase"

                if serial_code == rp["serial_code"]:
                    return await ctx.send(f"**Serial code {rp['serial_code']} was already used. RP Name: `{rp['rp_name']}`"
                                          f"\n**Hosted by {rp['main_host']}. Please use a different Serial Code.**")
                if rp_name.lower() == str(rp["rp_name"]).lower() and not int(rp["ended"]):
                    return await ctx.send(f"**{rp['rp_name']} is already in the Database and {ongoing_note} under the serial code:** `{rp['serial_code']}`**"
                                          f"\n**Hosted by {rp['main_host']} {local_note}.**")

            try:
                target = await bot.fetch_user(int(main_host_id))
            except discord.NotFound as p:
                return await ctx.send(f"`{p}`\n**Please input a valid Discord ID that is in the server.**")

            irl_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(rp_start_date)))
            other_timezones = str(irl_time)
            other_timezones = other_timezones.split(" ")
            hour_split = other_timezones[1].split(":")

            noted_time = time.strftime('%d-%B-%Y %H:%M:%S', time.gmtime(int(rp_start_date)))

            with open("rp_collection.csv", "a") as file:
                fieldnames = ["serial_code", "approved", "approved_id", "local", "rp_name", "main_host",
                              "main_host_id", "rp_start_date", "rp_start_time", "rp_duration", "doc", "sign_up", "ongoing", "ended"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writerow({"serial_code": serial_code, "approved": ctx.author.name, "approved_id": ctx.author.id, "local": local, "rp_name": rp_name, "main_host": target.name,
                                 "main_host_id": main_host_id, "rp_start_date": rp_start_date, "rp_start_time": f"{hour_split[0]}:{hour_split[1]}",
                                 "rp_duration": rp_duration, "doc": doc, "sign_up": sign_up, "ongoing": ongoing, "ended": ended})

            await ctx.channel.send(f'**{rp_name} ({serial_code}) was inserted to the Database; hosted by {target.name}.**'
                                   f'\n**First Session Date: {noted_time}**'
                                   f'\n`Doc:` {doc}')
            await target.send(f'**Your RP; {rp_name} ({serial_code}) was inserted to the Database; approved by {ctx.author.name}.**'
                              f'\n**You may announce it now and ensure to include the serial code.**'
                              f'\n**First Session Date: {noted_time}**')

        @bot.command(
            name='rp_profile',
            brief='Returns a profile of an RP.',
            help=('Returns a profile of an RP. There is only one required argument.'
                  '\nArguments: $rp_profile <_id>'
                  '\nExample: $rp_profile HN'
                  '\n\n<_id> is the Serial Code of said RP. It is case sensitive, so make sure it is correct.')
        )
        async def rp_profile(ctx: commands.Context, _id):
            if not _validate_command(ctx):
                return

            profile = _rp_profile_check(_id)

            embed = None
            bool_string = {"0": False, "1": True}

            if not profile:
                return await ctx.send("`That Serial Code does not exist in the database.`")

            for rp in profile:
                date_ = time.strftime('%d-%B-%Y %H:%M:%S', time.gmtime(int(rp["rp_start_date"])))
                embed = discord.Embed(title=f'RP Profile : {rp["rp_name"]}',
                                      description=f'**RP Name**: {rp["rp_name"]}\n'
                                                  f'**Serial Code**: {rp["serial_code"]}\n'
                                                  f'**Approved by**: {rp["approved"]}\n'
                                                  f'**Main Host**: {rp["main_host"]}\n'
                                                  f'**RP First Session Date**: {date_}\n'
                                                  f'**RP Start Time**: {rp["rp_start_time"]}\n'
                                                  f'**RP Length in Hours**: {rp["rp_duration"]}\n'
                                                  f'**Local ODROS**: {bool_string[rp["local"]]}\n'
                                                  f'**Sign Up Open**: {bool_string[rp["sign_up"]]}\n'
                                                  f'**Ongoing**: {bool_string[rp["ongoing"]]}\n'
                                                  f'**Ended**: {bool_string[rp["ended"]]}\n'
                                                  f'**Document**: {rp["doc"]}',

                                      colour=discord.Color.dark_blue())
                embed.set_thumbnail(url=ctx.author.avatar.url)
                embed.set_footer(text=ctx.author)

            return await ctx.send(embed=embed)

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

            try:
                value = int(value)
            except ValueError:
                return await ctx.send("`Input a valid value from 0-3 only.`")

            rp_dict = {
                0: _rp_profile_check_sign_up(value),
                1: _rp_profile_check_ongoing(value),
                2: _rp_profile_check_ended(value),
                3: _rp_profile_check_all(value)
            }

            bool_string = {"0": False, "1": True}

            try:
                profile = rp_dict[value]
            except KeyError:
                return await ctx.send("`Input a valid value from 0-3 only.`")

            if not profile:
                return await ctx.send("`Unfortunately, there is none in the database as of yet.`")

            for rp in profile:
                date_ = time.strftime('%d-%B-%Y %H:%M:%S', time.gmtime(int(rp["rp_start_date"])))
                embed = discord.Embed(title=f'RP Profile : {rp["rp_name"]}',
                                      description=f'**RP Name**: {rp["rp_name"]}\n'
                                                  f'**Serial Code**: {rp["serial_code"]}\n'
                                                  f'**Approved by**: {rp["approved"]}\n'
                                                  f'**Main Host**: {rp["main_host"]}\n'
                                                  f'**RP First Session Date**: {date_}\n'
                                                  f'**RP Start Time**: {rp["rp_start_time"]}\n'
                                                  f'**RP Length in Hours**: {rp["rp_duration"]}\n'
                                                  f'**Local ODROS**: {bool_string[rp["local"]]}\n'
                                                  f'**Sign Up Open**: {bool_string[rp["sign_up"]]}\n'
                                                  f'**Ongoing**: {bool_string[rp["ongoing"]]}\n'
                                                  f'**Ended**: {bool_string[rp["ended"]]}\n'
                                                  f'**Document**: {rp["doc"]}',

                                      colour=discord.Color.dark_blue())
                embed.set_thumbnail(url=ctx.author.avatar.url)
                embed.set_footer(text=ctx.author)

                await ctx.send(embed=embed)

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

            change_dict = {
                0: "closing sign ups",
                1: "opening sign ups",
                2: "labelling the RP as ongoing",
                3: "ending the RP"
            }

            try:
                value = int(value)
            except ValueError:
                return await ctx.send("`Input a valid value from 0-3 only.`")

            string_inform = None

            if not _admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            initial_check = _rp_profile_check(_id)

            if not initial_check:
                return await ctx.send('`Invalid RP Serial Code, cannot update.`')

            try:
                update = _update_rp_list_choice(_id, value)
            except KeyError:
                return await ctx.send("`Input a valid value from 0-3 only.`")

            update = update[1]

            for rp in update:
                string_inform = f"**You have updated {rp['rp_name']} ({rp['serial_code']}) by {change_dict[value]}!**"

            return await ctx.send(string_inform)

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
            name='hammertime',
            brief='Returns Hammertime Code. Can return remainder, as well.',
            help=('Returns Hammertime Code. Can return remainder, as well. For remainder, simply add a "1" at the end of the command and is an optional argument.\n'
                  'How this works is the DATE Format must be dashes [-] and TIME Format must be colons [:]. For DATE, it is DD-MM-YYYY. TIME uses the 24 Hour System\n'
                  'Use Correct Time Formatting and Numbers, otherwise it will not work. An example would be: Date = 31-12-2021 | Time = 10:00:00\n'
                  'Furthermore, at the very start, put a Timezone Abbreviation. For example: UTC, EST, MST, PST, GMT+2 or UTC+4.'
                  '\nArguments: $hammertime <timezone_abbreviation> <date> <time> <output_remainder_(optional)>'
                  '\nExample: $hammertime UTC+8 13-3-2022 5:00:00'
                  '\nRemainder Example: $hammertime UTC+8 13-3-2022 5:00:00 1'),
        )
        async def hammertime(ctx: commands.Context, timezone_: str, date_, time_, _remain=0):
            if not _validate_command(ctx):
                return

            try:
                _remain = int(_remain)
                if _remain not in (0, 1):
                    return await ctx.send("Please input a valid 0 | 1 at the end. [{}] is not a valid argument.".format(_remain))
                else:
                    text_add = ":R" if _remain else ":F"
            except ValueError:
                return await ctx.send("Please input a valid 0 | 1 at the end. [{}] is not a valid argument.".format(_remain))

            _TIMEZONE = timezone_list()
            if timezone_.upper() in _TIMEZONE:
                hour_add = _TIMEZONE[timezone_.upper()]
            else:
                return await ctx.send("Please input a valid timezone. [{}] is not a valid timezone.".format(timezone_.upper()))

            date_list, time_list = date_.split("-"), time_.split(":")

            if not len(date_list) == 3:
                return await ctx.send("Date Formatting Incorrect, please use dashes [-].")
            if not len(time_list) == 3:
                return await ctx.send("Time Formatting Incorrect, please use colons [:].")

            # Checking for Human Error
            check_date, check_time = check_value(date_list), check_value(time_list)
            ndv, ntv = check_date[1], check_time[1]
            new_date_list, new_time_list = check_date[0], check_time[0]
            check_list = new_date_list, new_time_list

            for err in check_list:
                if not err[0][0]:
                    return await ctx.send(f"**An error occured:** {err[0][1].title()}")

            new_hour = ntv[0]
            try:
                date_tuple = datetime.datetime(ndv[2], ndv[1], ndv[0], new_hour, ntv[1], ntv[2])
                time__ = calendar.timegm(date_tuple.timetuple())
                time__ -= hour_add * 3600
            except ValueError as f:
                return await ctx.send(f"**An error has occured:** {str(f).title()}")

            final_result = f"**Copy paste this code to activate the Hammertime Code:** \n-> `<t:{time__}{text_add}>`"
            return await ctx.send(final_result)

        async def _optin_role(ctx: commands.Context, role_name: str, role_id: int):
            if not _validate_command(ctx):
                return
            role = discord.utils.get(ctx.message.guild.roles, name=role_name)

            user = ctx.author
            has_role = False

            for user_role in user.roles:
                if user_role.id == role_id:
                    has_role = True

            if has_role:
                await user.remove_roles(role)
                await ctx.send(f'Removed role **{role_name}**.')
            else:
                await user.add_roles(role)
                await ctx.send(f'Added role **{role_name}**.')

        @bot.command(
            name='rpactive',
            brief='Changes your RP Active status',
            help=('If you did not have the RP Active role, the bot will give it to you. If you '
                  'already had it, the bot will take it away from you.'
                  '\nArguments: $rpactive'
                  '\nExample: $rpactive'),
        )
        async def rpactive(ctx: commands.Context):
            await _optin_role(ctx,
                              guild_details.rp_active_role_name(),
                              guild_details.rp_active_role_id())

        @bot.command(
            name='devtester',
            brief='Changes your Dev Tester status',
            help=('If you did not have the Dev Tester role, the bot will give it to you. If you '
                  'already had it, the bot will take it away from you.'
                  '\nArguments: $devtester'
                  '\nExample: $devtester'),
        )
        async def devtester(ctx: commands.Context):
            await _optin_role(ctx,
                              guild_details.dev_tester_role_name(),
                              guild_details.dev_tester_role_id())

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
                rp_list = rp_id_check()
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
                f"**-- Standard Time --**",
                f"**EST**: {_timezone_time_check(hour_change, -5)}:{hour_split[1]}:{hour_split[2]}",
                f"**CST**: {_timezone_time_check(hour_change, -6)}:{hour_split[1]}:{hour_split[2]}",
                f"**MST**: {_timezone_time_check(hour_change, -7)}:{hour_split[1]}:{hour_split[2]}",
                f"**PST**: {_timezone_time_check(hour_change, -8)}:{hour_split[1]}:{hour_split[2]}",
                f"**-- Daylight Time --**",
                f"**EDT**: {_timezone_time_check(hour_change, -4)}:{hour_split[1]}:{hour_split[2]}",
                f"**CDT**: {_timezone_time_check(hour_change, -5)}:{hour_split[1]}:{hour_split[2]}",
                f"**MDT**: {_timezone_time_check(hour_change, -6)}:{hour_split[1]}:{hour_split[2]}",
                f"**PDT**: {_timezone_time_check(hour_change, -7)}:{hour_split[1]}:{hour_split[2]}",
                f"**-- Europe Time --**",
                f"**UTC-1**: {_timezone_time_check(hour_change, -1)}:{hour_split[1]}:{hour_split[2]}",
                f"**UTC**: {_timezone_time_check(hour_change, 0)}:{hour_split[1]}:{hour_split[2]}",
                f"**UTC+1**: {_timezone_time_check(hour_change, 1)}:{hour_split[1]}:{hour_split[2]}",
                f"**UTC+2**: {_timezone_time_check(hour_change, 2)}:{hour_split[1]}:{hour_split[2]}",
                f"**UTC+3**: {_timezone_time_check(hour_change, 3)}:{hour_split[1]}:{hour_split[2]}",
            ]

            text_ = "\n".join(text_)

            embed = discord.Embed(title=title_embed,
                                  description=f'{text_}',
                                  colour=discord.Color.dark_gold())
            embed.set_thumbnail(url=ctx.author.avatar.url)
            embed.set_footer(text=ctx.author)

            await ctx.send(embed=embed)

        @bot.command(
            name='utc',
            brief='Lists the time for UTC timezones',
            help=('Lists the time for UTC timezones. There is an optional argument; if you input an epoch/unix time after the command, '
                  'you will get said time instead. Date format: YYYY-MM-DD.'
                  '\nArguments: $utc <seconds>'
                  '\nExample: $utc 1'
                  '\n\n<seconds> is an optional field; it is an epoch/unix second argument and MUST be an integer.')
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
            embed.set_thumbnail(url=ctx.author.avatar.url)
            embed.set_footer(text=ctx.author)

            await ctx.send(embed=embed)

        # -- Command Error Area -- #

        @ban_profile.error
        async def ban_profile_error(ctx: commands.Context, error):
            if isinstance(error, commands.BadBoolArgument):
                return await ctx.send("`Please input <_all> as either 0, 1 or False, True respectively.`")

            if isinstance(error, commands.BadArgument):
                return await ctx.send("`Please input <_id> as an integer, their Discord ID.`")

        @add_roleplay.error
        async def add_roleplay_error(ctx: commands.Context, error):
            if isinstance(error, commands.BadArgument):
                return await ctx.send("`Please input <main_host_id>, <rp_start_date>, <rp_duration>, <local>, "
                                      "<sign_up>, <ongoing>, and <ended> as integers.`")

        @ban_id.error
        async def ban_id_error(ctx: commands.Context, error):
            if isinstance(error, commands.BadArgument):
                return await ctx.send("`Please input <user_id> <ban_length> as integers.`")

        @unban.error
        async def unban_error(ctx: commands.Context, error):
            if isinstance(error, commands.BadArgument):
                return await ctx.send("`Please input <user_id> as integers.`")

        @bot.command(
            name='upload',
        )
        async def upload(ctx: commands.Context, server: str, file_type: str):
            success, msg = await _upload(ctx, server, file_type)
            await ctx.message.delete()

            if not msg:
                return

            str_success = 'successfully uploaded' if success else 'failed to upload'
            full_message = (
                f'{str_success} a file of type `{file_type}` to `{server}`.\r\n{msg}\r\n_ _'
            )
            await ctx.author.send(full_message[0].upper() + full_message[1:])

            for channel in guild_details.upload_log_channels():
                to_channel = _get_channel(channel)
                await to_channel.send(f'<@{ctx.author.id}> {full_message}')


        async def _upload(ctx: commands.Context, server: str, file_type: str) -> Tuple[bool, str]:
            if not _validate_command(ctx):
                return False, ''

            pre_download_valid, server, file_type, attachment, msg = (
                await _upload_check_pre_download(ctx, server, file_type))
            if not pre_download_valid:
                return False, msg

            download_valid, content, msg = (
                await _upload_check_download(ctx, attachment.url))
            if not download_valid:
                return False, msg

            yaml_valid, output, msg = (
                await _upload_check_yaml(ctx, server, file_type, content, attachment.filename))
            if not yaml_valid:
                return False, msg

            upload_valid, filename, msg = (
                await _upload_check_upload(ctx, server, file_type, content, attachment.filename))
            if not upload_valid:
                return False, msg

            msg = (
                f'Uploaded {file_type} `{attachment.filename}` to {server} with name: '
                f'`{filename}`.'
            )
            return True, msg

        async def _upload_check_pre_download(
            ctx: commands.Context, server: str,
            file_type: str) -> Tuple[bool, str, str, Union[discord.Attachment, None], str]:

            VALID_SERVERS = set(guild_details.upload_server_paths().keys())
            if server.lower().strip() not in VALID_SERVERS:
                msg = f'Expected server be one of `{VALID_SERVERS}`, found `{server}`.'
                return (False, '', '', None, msg)
            server = server.lower().strip()

            VALID_FILE_TYPES = set(guild_details.upload_asset_paths().keys())
            if file_type.lower().strip() not in VALID_FILE_TYPES:
                msg = f'Expected file type be one of `{VALID_FILE_TYPES}`, found `{file_type}`.'
                return (False, '', '', None, msg)
            file_type = file_type.lower().strip()

            attachments = ctx.message.attachments
            if not attachments:
                msg = 'Expected attachment.'
                return (False, '', '', None, msg)

            attachment = attachments[0]
            if not attachment.filename.endswith('.yaml'):
                msg = f'Expected file extension to be `.yaml`, found `{attachment.filename}`.'
                return (False, None, None, None, msg)

            MAX_FILE_SIZE = guild_details.upload_max_size_bytes()

            if attachment.size > MAX_FILE_SIZE:
                msg = (
                    f'Expected file size to not exceed `{MAX_FILE_SIZE/1024} KB`, '
                    f'found the file `{attachment.filename}` was `{attachment.size/2048} KB`.'
                )
                return (False, None, None, None, msg)

            return (True, server, file_type, attachment, '')

        async def _upload_check_download(ctx: commands.Context, url: str) -> Tuple[bool, str, str]:
            if not url.startswith('http') and not url.endswith('.yaml'):
                msg = f'SYSTEM: Invalid download link generated for `{url}`.'
                return (False, '', msg)

            response = requests.get(url)
            if not response:
                msg = (
                    f'SYSTEM: Invalid response read for download link generated for `{url}`: '
                    f'`{response}`.'
                )
                return (False, '', msg)

            raw_content = response.content
            try:
                content = raw_content.decode('utf-8')
            except UnicodeDecodeError as exc:
                msg = f'Invalid UTF-8 file read for download link generated for `{url}`: `{exc}`.'
                return (False, '', msg)

            if not content.strip():
                msg = 'Expected non-empty content, found no content.'
                return (False, '', msg)

            return (True, content, '')

        async def _upload_check_yaml(ctx: commands.Context, server: str, file_type: str,
                                     content: str,
                                     original_filename: str) -> Tuple[bool, str, str]:
            if not content.strip():
                msg = 'Expected non-empty content, found no content.'
                return (False, '', msg)

            temp_path = ''
            output = ''

            try:
                fd, temp_path = tempfile.mkstemp(suffix='.yaml')
                with os.fdopen(fd, 'w') as f:
                    f.write(content)

                command = [
                    'cd',
                    f'{guild_details.upload_server_paths()[server]}\\server\\validate',
                    '&&',
                    'python',
                    f'{file_type}.py',
                    f'"{temp_path}"'
                ]
                p = subprocess.Popen(
                    command,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                )
                p.stdin.write(b'n\n\n')
                raw_output, error = p.communicate()
                if error:
                    raise ValueError(f'SYSTEM: {error}')

                output = raw_output.decode('utf-8')
                lines = output.split('\r\n')
                if len(lines) < 4:
                    raise ValueError(f'SYSTEM: Invalid output from checker: {output}.')

                valid = lines[2].endswith('is VALID.')
                if not valid:
                    raise ValueError(
                        f'`{file_type}` YAML file `{original_filename}` is not syntactically '
                        f'valid.\r\n{lines[3]}')

                return True, output, ''
            except Exception as e:
                return False, output, e
            finally:
                if temp_path:
                    os.remove(temp_path)

        async def _upload_check_upload(ctx: commands.Context, server: str, file_type: str,
                                       content: str,
                                       original_filename: str) -> Tuple[bool, str, str]:
            if not content.strip():
                msg = 'Expected non-empty content, found no content.'
                return (False, '', msg)

            VALID_SERVERS = set(guild_details.upload_server_paths().keys())
            if server.lower().strip() not in VALID_SERVERS:
                msg = f'Expected server be one of `{VALID_SERVERS}`, found `{server}`.'
                return False, '', msg
            server = server.lower().strip()

            VALID_FILE_TYPES = set(guild_details.upload_asset_paths().keys())
            if file_type.lower().strip() not in VALID_FILE_TYPES:
                msg = f'Expected file type be one of `{VALID_FILE_TYPES}`, found `{file_type}`.'
                return False, '', msg
            file_type = file_type.lower().strip()

            directory = guild_details.upload_server_paths()[server]

            filename = f'{ctx.author.id % 10000}_{original_filename}'
            stem_path = f'{guild_details.upload_asset_paths()[file_type]}\\{filename}'

            try:
                with open(f'{directory}\\{stem_path}', mode='w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                msg = 'SYSTEM: Error while saving to path {stem_path}: {e}'
                return False, '', msg

            return True, filename, ''
