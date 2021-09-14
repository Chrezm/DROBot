# -*- coding: utf-8 -*-
import discord
import time
import csv
import string
import random
import asyncio
from discord.ext import commands
from discord.ext import commands, tasks

from typing import Dict


# This is a string generator for RP Serial Codes. But it can be used for something more in the future.
def code_creator():
    lowercase_letter, uppercase_letter, digits = string.ascii_lowercase, string.ascii_uppercase, str(string.digits)
    code = ''.join(random.sample(lowercase_letter + uppercase_letter + digits, 12))
    return code


# This is the initial check for ban_ids.csv and obtaining its data.
def ban_id_check():
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
            writer.writerow({"discord_id": 0, "discord_name": "Example", "ban_timestamp": 42069, "ban_length": 69420, "reason": "he called me cringe", "ended": 1})

    return ban_list


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
            writer.writerow({"serial_code": code_creator(), "approved": "MODERATOR", "approved_id": 420, "local": 1, "rp_name": "Love Hotel is NOT REAL", "main_host": "Deez",
                             "main_host_id": 0, "rp_start_date": 0, "rp_start_time": 10, "rp_duration": 5, "doc": "https://www.youtube.com/watch?v=YoU3r6ZK8xQ",
                             "sign_up": 0, "ongoing": 0, "ended": 1})

    return rp_list


# This is to start the checks and if said file does not exist, will create one.
ban_id_check()
rp_id_check()


class Functionality:
    def __init__(self, bot: commands.Bot = None, guild_details: Dict = None):
        @bot.event
        async def on_ready():
            # This is to begin the task loop.
            second_passing.start()
            print('Logged in as {0.user}'.format(bot))

        # This is a task loop, where it will self-update every 10 minutes.
        @tasks.loop(seconds=600.0)
        async def second_passing():
            print(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(round(time.time()))))
            update_rp_list()
            update_ban_list()

        # This will execute before the function <second_passing> will run.
        @second_passing.before_loop
        async def inform_check():
            print('The Ten-Minute Self-Update is now Running.')

        @bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                await ctx.send('`Unrecognized command.`')
                return

            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send("`Please input the required arguments.`")
                return

            raise error

        @bot.event
        async def on_message(message):
            # Looks through the ban_id.csv
            ban_id_ = ban_id_check()

            if message.author == bot.user:
                return

            if message.channel.name in guild_details.relaying_channels:
                # Right here, it will delete the message and notify the user who tried using the bot that they are banned.
                # The ban_id_[1:] is to skip the example ID.
                for user in ban_id_[1:]:
                    bool_ = int(user["ended"])
                    bool_ = bool(bool_)
                    if message.author.id == user["discord_id"] and bool_ is False:
                        await message.delete(message)
                        return await message.author.send("**You cannot access the bot due to your ban.**")

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
        def admin_check(ctx):
            admin_roles = [role for role in ctx.guild.roles if role.permissions.administrator]

            for admin_role in admin_roles:
                if admin_role in ctx.author.roles:
                    return True

            return None

        # Converts Seconds to Days
        def second_to_day(second: int):
            answer = second / 86400
            return round(answer)

        def ban_profile_check(_id):
            ban_list = ban_id_check()
            found = []

            for user in ban_list:
                if str(_id) == user["discord_id"]:
                    found.append(user)

            return found

        def update_unban(_id):
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

        def update_ban_list():
            ban_ids = ban_id_check()
            updated_ban_list = list()
            inform_ban_list = list()  # This is to inform players when their ban is over.
            update_dict = None

            for user in ban_ids:
                answer = int(user["ban_timestamp"]) + int(user["ban_length"])
                answer = round(time.time()) - answer

                if answer >= 0:
                    if bool(int(user["ended"])) is True:
                        update_dict = user

                    if bool(int(user["ended"])) is False:
                        update_dict = {"discord_id": user["discord_id"], "discord_name": user["discord_name"], "ban_timestamp": user["ban_timestamp"],
                                       "ban_length": user["ban_length"], "reason": user["reason"], "ended": 1}

                        inform_ban_list.append(update_dict)

                elif answer < 0:
                    update_dict = user

                updated_ban_list.append(update_dict)

            with open("ban_ids.csv", "w+") as file:
                fieldnames = ["discord_id", "discord_name", "ban_timestamp", "ban_length", "reason", "ended"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()

                for update in updated_ban_list:
                    writer.writerow(update)

            return updated_ban_list, inform_ban_list

        def update_rp_list():
            rp_list = rp_id_check()
            updated_rp_list = list()
            update_dict = None

            for user in rp_list:
                answer = round(time.time()) - int(user["rp_start_date"])

                if answer >= 0:
                    if bool(int(user["ongoing"])) is True:
                        update_dict = user

                    if bool(int(user["ongoing"])) is False:
                        update_dict = {"serial_code": user['serial_code'], "approved": user['approved'], "approved_id": user['approved_id'], "local": user['local'],
                                       "rp_name": user['rp_name'], "main_host": user['main_host'], "main_host_id": user['main_host_id'], "rp_start_date": user['rp_start_date'],
                                       "rp_start_time": user['rp_start_time'], "rp_duration": user['rp_duration'], "doc": user['doc'],
                                       "sign_up": 0, "ongoing": 1, "ended": 0}

                elif answer < 0:
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

        def update_rp_list_choice(_id, val):
            change_dict = {
                0: [0, 0, 0],  # Close Sign Ups
                1: [1, 0, 0],  # Open Sign Ups
                2: [0, 1, 0],  # Ongoing RP
                3: [0, 0, 1]   # Ends RP
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

        def rp_profile_check(_id):
            rp_list = rp_id_check()
            found = []

            for rp in rp_list:
                if str(_id) == rp["serial_code"]:
                    found.append(rp)

            return found

        def rp_profile_check_sign_up(val):
            if val != 0:
                return

            rp_list = rp_id_check()
            found = []

            for rp in rp_list:
                if str(1) == rp["sign_up"]:
                    found.append(rp)

            return found

        def rp_profile_check_ongoing(val):
            if val != 1:
                return

            rp_list = rp_id_check()
            found = []

            for rp in rp_list:
                if str(1) == rp["ongoing"]:
                    found.append(rp)

            return found

        def rp_profile_check_ended(val):
            if val != 2:
                return

            rp_list = rp_id_check()
            found = []

            for rp in rp_list:
                if str(1) == rp["ended"]:
                    found.append(rp)

            return found

        def rp_profile_check_all(val):
            if val != 3:
                return

            rp_list = rp_id_check()
            found = []

            for rp in rp_list:
                found.append(rp)

            return found

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
            help=('Bans a Discord User from using the Bot. There are multiple arguments needed to be filled.'
                  '\nArguments: $ban_id <discord_id> <ban_length : seconds> <reason> '
                  '\nExample: $ban_id 332456386946531328 259200 "There must be a open and close quotes for reason."'),
            hidden=True,
        )
        async def ban_id(ctx: commands.Context, user_id: int, ban_length: int = 259200, reason: str = "Unstated Reason"):
            if not _validate_command(ctx):
                return

            if not admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            ban_ids = ban_id_check()

            try:
                target = await bot.fetch_user(user_id)
                print(target.name)
            except discord.NotFound as p:
                return await ctx.send(f"`{p}`\n**Please input a valid Discord ID that is in the server.**")

            for dict_ban in ban_ids[1:]:
                bool_ = int(dict_ban["ended"])
                bool_ = bool(bool_)

                if str(user_id) == str(dict_ban["discord_id"]) and bool_ is False:
                    return await ctx.send(f"**{target.name} is already in the list and his ban has not ended.**")

            with open("ban_ids.csv", "a") as file_:
                fieldnames = ["discord_id", "discord_name", "ban_timestamp", "ban_length", "reason", "ended"]
                writer = csv.DictWriter(file_, fieldnames=fieldnames)
                writer.writerow({"discord_id": user_id, "discord_name": target.name, "ban_timestamp": round(time.time()), "ban_length": ban_length, "reason": reason, "ended": 0})

            days = second_to_day(ban_length)
            await ctx.channel.send(f'**{target.name} ({user_id}) is now banned from accessing the Server Bot for {days} days.**'
                                   f'\n`Reason: {reason}`')
            await target.send(f'**You are now banned from accessing the Server Bot for {days} days.**'
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

            if not admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            initial_check = ban_profile_check(_id)
            if not initial_check:
                return await ctx.send("`Invalid Discord ID.`")

            updated_list = update_unban(_id)
            updated_list = updated_list[1]

            for user in updated_list:
                target = await bot.fetch_user(int(user['discord_id']))
                await target.send(f'**You are now unbanned from accessing the Server Bot. Please do not make the same offense again.**')

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
        async def ban_profile(ctx: commands.Context, _id: int, _all: bool = False):
            if not _validate_command(ctx):
                return

            if not admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            profile = ban_profile_check(_id)
            embed = None

            if not profile:
                return await ctx.send("`That ID does not exist in the database.`")

            for user in profile:
                date_ = time.strftime('%d-%B-%Y %H:%M:%S', time.gmtime(int(user["ban_timestamp"])))
                embed = discord.Embed(title=f'Ban Profile : {user["discord_name"]}',
                                      description=f'**Discord Name**: {user["discord_name"]}\n'
                                                  f'**Discord ID**: {user["discord_id"]}\n'
                                                  f'**Ban Date**: {date_}\n'
                                                  f'**Ban Length**: {second_to_day(int(user["ban_length"]))}\n'
                                                  f'**Reason**: {user["reason"]}\n'
                                                  f'**Ban Ended**: {user["ended"]}',


                                      colour=discord.Color.dark_blue())
                embed.set_thumbnail(url=ctx.author.avatar_url)
                embed.set_footer(text=ctx.author)

                if _all is True:
                    await ctx.send(embed=embed)

            if _all is False:
                await ctx.send(embed=embed)

            return

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

            if not admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            updated_list = update_ban_list()[1]

            if updated_list:
                for user in updated_list:
                    answer = int(user["ban_timestamp"]) + int(user["ban_length"])
                    answer = round(time.time()) - answer

                    if answer >= 0:
                        target = await bot.fetch_user(int(user['discord_id']))
                        await target.send(f'**You are now unbanned from accessing the Server Bot. Please do not make the same offense again.**')

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
                  "\n<local> is an optional field, can only be 0 or 1. --0: False (Hosted outside DRO) | 1: True (Hosted within DRO)--"
                  "\n<sign_up> is an optional field, can only be 0 or 1. --0: False (Sign ups are closed) | 1: True (Sign ups are open)--"
                  "\n<ongoing> is an optional field, can only be 0 or 1. --0: False (RP is not ongoing) | 1: True (RP is ongoing)--"
                  "\n<ended> is an optional field, can only be 0 or 1. --0: False (RP has not ended) | 1: True (RP ended)--"),
        )
        async def add_roleplay(ctx: commands.Context, rp_name, main_host_id: int, rp_start_date: int, rp_duration: int,
                               doc, serial_code=None, local: int = 1, sign_up: int = 1, ongoing: int = 0, ended: int = 0):
            if not _validate_command(ctx):
                return

            if not admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            rp_list = rp_id_check()

            if not serial_code:
                serial_code = code_creator()

            for rp in rp_list[1:]:
                bool_ = int(rp["ended"])
                bool_ = bool(bool_)

                local_note = "in DRO servers"
                if bool(int(rp['local'])) is False:
                    local_note = "outside of DRO servers"

                ongoing_note = "currently ongoing"
                if bool(int(rp['ongoing'])) is False:
                    ongoing_note = "still on its sign up phase"

                if serial_code == rp["serial_code"]:
                    return await ctx.send(f"**Serial code {rp['serial_code']} was already used. RP Name: `{rp['rp_name']}`"
                                          f"\n**Hosted by {rp['main_host']}. Please use a different Serial Code.**")
                if rp_name.lower() == str(rp["rp_name"]).lower() and bool_ is False:
                    return await ctx.send(f"**{rp['rp_name']} is already in the Database and {ongoing_note} under the serial code:** `{rp['serial_code']}`**"
                                          f"\n**Hosted by {rp['main_host']} {local_note}.**")

            try:
                target = await bot.fetch_user(main_host_id)
                print(target.name)
            except discord.NotFound as p:
                return await ctx.send(f"`{p}`\n**Please input a valid Discord ID that is in the server.**")

            irl_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(rp_start_date))
            other_timezones = str(irl_time)
            other_timezones = other_timezones.split(" ")
            hour_split = other_timezones[1].split(":")

            noted_time = time.strftime('%d-%B-%Y %H:%M:%S', time.gmtime(rp_start_date))

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
                  '\n<_id> is the Serial Code of said RP. It is case sensitive, so make sure it is correct.')
        )
        async def rp_profile(ctx: commands.Context, _id):
            if not _validate_command(ctx):
                return

            profile = rp_profile_check(_id)
            embed = None

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
                                                  f'**Local DRO**: {bool(int(rp["local"]))}\n'
                                                  f'**Sign Up Open**: {bool(int(rp["sign_up"]))}\n'
                                                  f'**Ongoing**: {bool(int(rp["ongoing"]))}\n'
                                                  f'**Ended**: {bool(int(rp["ended"]))}\n'
                                                  f'**Document**: {rp["doc"]}',

                                      colour=discord.Color.dark_blue())
                embed.set_thumbnail(url=ctx.author.avatar_url)
                embed.set_footer(text=ctx.author)

            return await ctx.send(embed=embed)

        @bot.command(
            name='rp_profile_filter',
            brief='Returns a list of RP profiles that are filtered.',
            help=('Returns a list of RP profiles that are filtered based on value of 0-3'
                  '\nArguments: $rp_profile_filter <value>'
                  '\nExample: $rp_profile_filter 0'
                  '\n<value> is the code for filter action.'
                  '\n0 - Filters RP profiles whose Sign Ups are Open.'
                  '\n1 - Filters RP profiles which are currently Ongoing.'
                  '\n2 - Filters RP Profiles which have ended.'
                  '\n3 - Does not filter and returns all RP profiles.')
        )
        async def rp_profile_filter(ctx: commands.Context, value: int = 0):
            if not _validate_command(ctx):
                return

            try:
                value = int(value)
            except ValueError:
                return await ctx.send("`Input a valid value from 0-3 only.`")

            rp_dict = {
                0: rp_profile_check_sign_up(value),
                1: rp_profile_check_ongoing(value),
                2: rp_profile_check_ended(value),
                3: rp_profile_check_all(value)
            }

            profile = rp_dict[value]

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
                                                  f'**Local DRO**: {bool(int(rp["local"]))}\n'
                                                  f'**Sign Up Open**: {bool(int(rp["sign_up"]))}\n'
                                                  f'**Ongoing**: {bool(int(rp["ongoing"]))}\n'
                                                  f'**Ended**: {bool(int(rp["ended"]))}\n'
                                                  f'**Document**: {rp["doc"]}',

                                      colour=discord.Color.dark_blue())
                embed.set_thumbnail(url=ctx.author.avatar_url)
                embed.set_footer(text=ctx.author)

                await ctx.send(embed=embed)

            return

        @bot.command(
            name='rp_change_status',
            brief='Changes RP status.',
            help=('Changes RP status based on the value of 0-3'
                  '\nArguments: $rp_change_status <_id> <value>'
                  '\nExample: $rp_change_status HN 0'
                  '\n<_id> is the Serial Code for the RP; the one you are planning to change.'
                  '\n<value> is the code for status change action.'
                  '\n0 - Closes Sign Ups.'
                  '\n1 - Opens Sign Ups.'
                  '\n2 - Labels the RP as Ongoing.'
                  '\n3 - Ending the RP.')
        )
        async def rp_change_status(ctx: commands.Context, _id, value: int = 0):
            if not _validate_command(ctx):
                return

            string_inform = None

            if not admin_check(ctx):
                return await ctx.send("`Insufficient Privileges.`")

            initial_check = rp_profile_check(_id)

            if not initial_check:
                return await ctx.send('`Invalid RP Serial Code, cannot update.`')

            change_dict = {
                0: "closing sign ups",
                1: "opening sign ups",
                2: "labelling the RP as ongoing",
                3: "ending the RP"
            }

            update = update_rp_list_choice(_id, value)
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

            rp_active_role = discord.utils.get(ctx.message.guild.roles,
                                               name=guild_details.rp_active_role_name)

            user = ctx.author
            has_rp_active = False

            for role in user.roles:
                if role.id == guild_details.rp_active_role_id:
                    has_rp_active = True

            if has_rp_active:
                await user.remove_roles(rp_active_role)
                await ctx.send(f'Removed role **{guild_details.rp_active_role_name}**.')
            else:
                await user.add_roles(rp_active_role)
                await ctx.send(f'Added role **{guild_details.rp_active_role_name}**.')

        @bot.command(
            name='timezone',
            brief='Lists the time based on <important> timezones.',
            help=('Lists the time based on <important> timezones. Date format: YYYY-MM-DD.'
                  '\nArguments: $timezone <seconds>'
                  '\nExample: $timezone HN'
                  '\n<seconds> is an optional field; it is an epoch/unix second argument. It can also be an RP Serial Code.'
                  "\nInputting <seconds> as an RP Serial Code will return you said RP's First Session Date."
                  )
        )
        async def timezone(ctx: commands.Context, seconds=None):
            if not _validate_command(ctx):
                return

            irl_time = None
            title_embed = None

            if not seconds:
                irl_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(round(time.time())))
                title_embed = f'It is {irl_time} UTC'

            try:
                seconds = int(seconds)
                irl_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(seconds))
                title_embed = f'It is {irl_time} UTC'
            except ValueError:
                rp_list = rp_id_check()
                for rp in rp_list:
                    if seconds == rp["serial_code"]:
                        irl_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(rp["rp_start_time"])))
                        title_embed = f'RP Hosted at {irl_time} UTC'
            except TypeError as p:
                raise p

            other_timezones = str(irl_time)
            other_timezones = other_timezones.split(" ")
            hour_split = other_timezones[1].split(":")
            hour_change = int(hour_split[0])
            text_ = [
                f"**-- Standard Time --**",
                f"**EST**: {timezone_time_check(hour_change, -5)}:{hour_split[1]}:{hour_split[2]}",
                f"**CST**: {timezone_time_check(hour_change, -6)}:{hour_split[1]}:{hour_split[2]}",
                f"**MST**: {timezone_time_check(hour_change, -7)}:{hour_split[1]}:{hour_split[2]}",
                f"**PST**: {timezone_time_check(hour_change, -8)}:{hour_split[1]}:{hour_split[2]}",
                f"**-- Daylight Time --**",
                f"**EDT**: {timezone_time_check(hour_change, -4)}:{hour_split[1]}:{hour_split[2]}",
                f"**CDT**: {timezone_time_check(hour_change, -5)}:{hour_split[1]}:{hour_split[2]}",
                f"**MDT**: {timezone_time_check(hour_change, -6)}:{hour_split[1]}:{hour_split[2]}",
                f"**PDT**: {timezone_time_check(hour_change, -7)}:{hour_split[1]}:{hour_split[2]}",
                f"**-- Europe Time --**",
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
            help=('Lists the time for UTC timezones. There is an optional argument; if you input an epoch/unix time after the command, '
                  'you will get said time instead. Date format: YYYY-MM-DD.'
                  '\nArguments: $utc <seconds>'
                  '\nExample: $utc 1'
                  '\n<seconds> is an optional field; it is an epoch/unix second argument and MUST be an integer.')
        )
        async def utc(ctx: commands.Context, seconds: int = None):
            if not _validate_command(ctx):
                return

            irl_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(seconds))
            if not seconds:
                irl_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(round(time.time())))

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