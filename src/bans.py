# -*- coding: utf-8 -*-
import csv
import time

from typing import List

import discord
from discord.ext import commands


async def command_ban_id(bot, guild_details, ctx: commands.Context, user_id: int,
                         ban_length: int = 259200, reason="Unstated Reason"):
    ban_ids = ban_id_check()

    try:
        target = await bot.fetch_user(user_id)
    except discord.NotFound as p:
        return await ctx.send(f"`{p}`\n**Please input a valid Discord ID that is in the "
                              "server.**")

    for dict_ban in ban_ids:
        if str(user_id) == str(dict_ban["discord_id"]) and not int(dict_ban["ended"]):
            return await ctx.send(f"**{target.name} is already in the list and his ban has "
                                  "not ended.**")

    with open("ban_ids.csv", "a") as file_:
        fieldnames = [
            "discord_id",
            "discord_name",
            "ban_timestamp",
            "ban_length",
            "reason",
            "ended"
            ]
        writer = csv.DictWriter(file_, fieldnames=fieldnames)
        writer.writerow({
            "discord_id": user_id,
            "discord_name": target.name,
            "ban_timestamp": round(time.time()),
            "ban_length": ban_length,
            "reason": reason,
            "ended": 0
            })

    if ban_length < 86400:
        days = _second_to_hour(ban_length)
        word_ = f"{days} hours"

    else:
        days = _second_to_day(ban_length)
        word_ = f"{days} days"

    await ctx.channel.send(f'**{target.name} ({user_id}) is now banned from using the '
                           f'Server Bot for {word_}.**'
                           f'\n`Reason: {reason}`')
    await target.send(f'**You are now banned from using the Server Bot for {word_}**'
                      f'\n`Reason: {reason}`')


async def command_unban(bot, guild_details, ctx: commands.Context, _id: int):
    initial_check = _browse_ban_profile(user_id=_id)
    if not initial_check:
        return await ctx.send("`Invalid Discord ID.`")

    updated_list = _update_unban(_id)
    updated_list = updated_list[1]

    for user in updated_list:
        target = await bot.fetch_user(int(user['discord_id']))
        await target.send('**You are now unbanned from using the Server Bot. Please do not '
                          'commit the same offense again.**')

    return await ctx.send("**Updated! Those whose ban is revoked will be notified.**")


async def command_ban_profile(bot, guild_details, ctx: commands.Context, _id: int, _all=False):
    profile = _browse_ban_profile(user_id=_id)
    embed = None

    if not profile:
        return await ctx.send("`That ID does not exist in the database.`")

    for user in profile:
        date_ = time.strftime('%d-%B-%Y %H:%M:%S', time.gmtime(int(user["ban_timestamp"])))
        description = (
            f'**Discord Name**: {user["discord_name"]}\n'
            f'**Discord ID**: {user["discord_id"]}\n'
            f'**Ban Date**: {date_}\n'
            f'**Ban Length**: {_second_to_day(int(user["ban_length"]))}\n'
            f'**Reason**: {user["reason"]}\n'
            f'**Ban Ended**: {user["ended"]}'
        )
        embed = discord.Embed(title=f'Ban Profile : {user["discord_name"]}',
                              description=description,
                              colour=discord.Color.dark_blue())
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(text=ctx.author)

        if _all:
            await ctx.send(embed=embed)

    if not _all:
        await ctx.send(embed=embed)


async def command_ban_profile_all(bot, guild_details, ctx: commands.Context):
    profile = _browse_ban_profile()

    if not profile:
        return await ctx.send("`There are no bans in the Database.`")

    for user in profile:
        date_ = time.strftime('%d-%B-%Y %H:%M:%S', time.gmtime(int(user["ban_timestamp"])))
        description = (
                f'**Discord Name**: {user["discord_name"]}\n'
                f'**Discord ID**: {user["discord_id"]}\n'
                f'**Ban Date**: {date_}\n'
                f'**Ban Length**: {_second_to_day(int(user["ban_length"]))}\n'
                f'**Reason**: {user["reason"]}\n'
                f'**Ban Ended**: {user["ended"]}'
            )
        embed = discord.Embed(title=f'Ban Profile : {user["discord_name"]}',
                              description=description,
                              colour=discord.Color.dark_blue())
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(text=ctx.author)

        await ctx.send(embed=embed)


async def command_ban_list_update(bot, guild_details, ctx: commands.Context):
    updated_list = _update_ban_list()[1]

    if updated_list:
        for user in updated_list:
            answer = int(user["ban_timestamp"]) + int(user["ban_length"])
            answer = round(time.time()) - answer

            if answer >= 0:
                target = await bot.fetch_user(int(user['discord_id']))
                await target.send('**You are now unbanned from using the Server Bot. '
                                  'Please do not make the same offense again.**')

    await ctx.send("**Updated! Those whose ban is over will be notified.**")


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

    return ban_list


# Converts Seconds to Days
def _second_to_day(second: int) -> int:
    answer = second / 86400
    return round(answer)


# Converts Seconds to Hours
def _second_to_hour(second: int) -> int:
    answer = second / 3600
    return round(answer)


def _browse_ban_profile(user_id: int = None) -> List:
    ban_list = ban_id_check()
    found = []

    for user in ban_list:
        if user_id is None or user['discord_id'] == str(user_id):
            found.append(user)

    return found


def _update_unban(_id):
    ban_ids = ban_id_check()
    updated_ban_list = list()
    inform_ban_list = list()  # This is to inform players when their ban is over.

    for user in ban_ids:
        if str(_id) == user["discord_id"]:
            update_dict = {
                "discord_id": user["discord_id"],
                "discord_name": user["discord_name"],
                "ban_timestamp": user["ban_timestamp"],
                "ban_length": user["ban_length"],
                "reason": user["reason"],
                "ended": 1
                }
            inform_ban_list.append(update_dict)

        else:
            update_dict = user

        updated_ban_list.append(update_dict)

    with open("ban_ids.csv", "w+") as file:
        fieldnames = [
            "discord_id",
            "discord_name",
            "ban_timestamp",
            "ban_length",
            "reason",
            "ended"
            ]
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
                update_dict = {
                    "discord_id": user["discord_id"],
                    "discord_name": user["discord_name"],
                    "ban_timestamp": user["ban_timestamp"],
                    "ban_length": user["ban_length"],
                    "reason": user["reason"],
                    "ended": 1
                    }

                inform_ban_list.append(update_dict)

        else:
            update_dict = user

        updated_ban_list.append(update_dict)

    with open("ban_ids.csv", "w+") as file:
        fieldnames = [
            "discord_id",
            "discord_name",
            "ban_timestamp",
            "ban_length",
            "reason",
            "ended"
            ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for update in updated_ban_list:
            writer.writerow(update)

    return updated_ban_list, inform_ban_list


async def inform_update_list(bot):
    updated_list = _update_ban_list()[1]

    if updated_list:
        for user in updated_list:
            answer = int(user["ban_timestamp"]) + int(user["ban_length"])
            answer = round(time.time()) - answer

            if answer >= 0:
                target = await bot.fetch_user(int(user['discord_id']))
                await target.send("**You are now unbanned from using the Server Bot. "
                                  "Please do not commit the same offense again.**")

    return
