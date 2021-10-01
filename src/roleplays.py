# -*- coding: utf-8 -*-

import csv
import random
import string
import time

from typing import List, Tuple

import discord
from discord.ext import commands


async def command_add_roleplay(bot, guild_details, ctx: commands.Context, rp_name, main_host_id: int,
                               rp_start_date: int, rp_duration: int, doc, serial_code=None,
                               local: int = 1, sign_up: int = 1, ongoing: int = 0, ended: int = 0):
    rp_list = rp_id_check()

    arg_check = [local, sign_up, ongoing, ended]
    for arg in arg_check:
        try:
            arg = int(arg)
            if arg not in [0, 1]:
                return await ctx.send("`<Local>, <Sign Up>, <Ongoing>, and <Ended> "
                                      "Arguments must be either 0 or 1.`")
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
            return await ctx.send(f"**Serial code {rp['serial_code']} was already used. "
                                  f"RP Name: `{rp['rp_name']}`"
                                  f"\n**Hosted by {rp['main_host']}. Please use a different "
                                  f"Serial Code.**")
        if rp_name.lower() == str(rp["rp_name"]).lower() and not int(rp["ended"]):
            return await ctx.send(f"**{rp['rp_name']} is already in the Database and "
                                  f"{ongoing_note} under the serial code:** "
                                  f"`{rp['serial_code']}`**"
                                  f"\n**Hosted by {rp['main_host']} {local_note}.**")

    try:
        target = await bot.fetch_user(int(main_host_id))
    except discord.NotFound as p:
        return await ctx.send(f"`{p}`\n**Please input a valid Discord ID that is in the "
                              "server.**")

    irl_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(rp_start_date)))
    other_timezones = str(irl_time)
    other_timezones = other_timezones.split(" ")
    hour_split = other_timezones[1].split(":")

    noted_time = time.strftime('%d-%B-%Y %H:%M:%S', time.gmtime(int(rp_start_date)))

    with open("rp_collection.csv", "a") as file:
        fieldnames = [
            "serial_code",
            "approved",
            "approved_id",
            "local",
            "rp_name",
            "main_host",
            "main_host_id",
            "rp_start_date",
            "rp_start_time",
            "rp_duration",
            "doc",
            "sign_up",
            "ongoing",
            "ended"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerow({
            "serial_code": serial_code,
            "approved": ctx.author.name,
            "approved_id": ctx.author.id,
            "local": local,
            "rp_name": rp_name,
            "main_host": target.name,
            "main_host_id": main_host_id,
            "rp_start_date": rp_start_date,
            "rp_start_time": f"{hour_split[0]}:{hour_split[1]}",
            "rp_duration": rp_duration,
            "doc": doc,
            "sign_up": sign_up,
            "ongoing": ongoing,
            "ended": ended
            })

    await ctx.channel.send(f'**{rp_name} ({serial_code}) was inserted to the Database; '
                           f'hosted by {target.name}.**'
                           f'\n**First Session Date: {noted_time}**'
                           f'\n`Doc:` {doc}')
    await target.send(f'**Your RP; {rp_name} ({serial_code}) was inserted to the Database; '
                      f'approved by {ctx.author.name}.**'
                      f'\n**You may announce it now and ensure to include the serial code.**'
                      f'\n**First Session Date: {noted_time}**')


async def command_rp_profile(bot, guild_details, ctx: commands.Context, _id):
    profile = rp_profile_check(_id)

    embed = None
    bool_string = {"0": False, "1": True}

    if not profile:
        await ctx.send("`That Serial Code does not exist in the database.`")
        return

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
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(text=ctx.author)

    await ctx.send(embed=embed)


async def command_rp_profile_filter(bot, guild_details, ctx: commands.Context, value):
    try:
        value = int(value)
    except ValueError:
        await ctx.send("`Input a valid value from 0-3 only.`")
        return

    rp_dict = {
        0: rp_profile_check_sign_up(value),
        1: rp_profile_check_ongoing(value),
        2: rp_profile_check_ended(value),
        3: rp_profile_check_all(value)
    }

    bool_string = {"0": False, "1": True}

    try:
        profile = rp_dict[value]
    except KeyError:
        await ctx.send("`Input a valid value from 0-3 only.`")
        return

    if not profile:
        await ctx.send("`Unfortunately, there is none in the database as of yet.`")
        return

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
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(text=ctx.author)

        await ctx.send(embed=embed)


async def command_rp_change_status(bot, guild_details, ctx: commands.Context, _id, value="0"):
    change_dict = {
        0: "closing sign ups",
        1: "opening sign ups",
        2: "labelling the RP as ongoing",
        3: "ending the RP"
    }

    try:
        value = int(value)
    except ValueError:
        await ctx.send("`Input a valid value from 0-3 only.`")
        return

    string_inform = None

    initial_check = rp_profile_check(_id)

    if not initial_check:
        await ctx.send('`Invalid RP Serial Code, cannot update.`')
        return

    try:
        update = update_rp_list_choice(_id, value)
    except KeyError:
        await ctx.send("`Input a valid value from 0-3 only.`")
        return

    update = update[1]

    for rp in update:
        string_inform = (
            f"**You have updated {rp['rp_name']} ({rp['serial_code']}) by "
            f"{change_dict[value]}!**"
            )
    await ctx.send(string_inform)
    return


# This is a string generator for RP Serial Codes. But it can be used for something more in the future.
def create_code() -> str:
    lowercase_letter = string.ascii_lowercase
    uppercase_letter = string.ascii_uppercase
    digits = str(string.digits)
    code = ''.join(random.sample(lowercase_letter + uppercase_letter + digits, 12))
    return code


# This is the initial check for rp_collection.csv and obtaining its data.
def rp_id_check() -> List:
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
            fieldnames = [
                "serial_code",
                "approved",
                "approved_id",
                "local",
                "rp_name",
                "main_host",
                "main_host_id",
                "rp_start_date",
                "rp_start_time",
                "rp_duration",
                "doc",
                "sign_up",
                "ongoing",
                "ended"
                ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

    return rp_list


def update_rp_list() -> List:
    rp_list = rp_id_check()
    updated_rp_list = list()
    update_dict = None

    for user in rp_list:
        answer = round(time.time()) - int(user["rp_start_date"])

        if answer >= 0:
            if user["ongoing"] == "1":
                update_dict = user

            if user["ongoing"] == "0":
                update_dict = {
                    "serial_code": user['serial_code'],
                    "approved": user['approved'],
                    "approved_id": user['approved_id'],
                    "local": user['local'],
                    "rp_name": user['rp_name'],
                    "main_host": user['main_host'],
                    "main_host_id": user['main_host_id'],
                    "rp_start_date": user['rp_start_date'],
                    "rp_start_time": user['rp_start_time'],
                    "rp_duration": user['rp_duration'],
                    "doc": user['doc'],
                    "sign_up": 0,
                    "ongoing": 1,
                    "ended": 0
                    }

        else:
            update_dict = user

        updated_rp_list.append(update_dict)

    with open("rp_collection.csv", "w+") as file:
        fieldnames = [
            "serial_code",
            "approved",
            "approved_id",
            "local",
            "rp_name",
            "main_host",
            "main_host_id",
            "rp_start_date",
            "rp_start_time",
            "rp_duration",
            "doc",
            "sign_up",
            "ongoing",
            "ended"
            ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for update in updated_rp_list:
            writer.writerow(update)

    return updated_rp_list


def update_rp_list_choice(_id, val) -> Tuple[List, List]:
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
            update_dict = {
                "serial_code": user['serial_code'],
                "approved": user['approved'],
                "approved_id": user['approved_id'],
                "local": user['local'],
                "rp_name": user['rp_name'],
                "main_host": user['main_host'],
                "main_host_id": user['main_host_id'],
                "rp_start_date": user['rp_start_date'],
                "rp_start_time": user['rp_start_time'],
                "rp_duration": user['rp_duration'],
                "doc": user['doc'],
                "sign_up": value_change[0],
                "ongoing": value_change[1],
                "ended": value_change[2]
                }

            inform_update.append(update_dict)

        else:
            update_dict = user

        updated_rp_list.append(update_dict)

    with open("rp_collection.csv", "w+") as file:
        fieldnames = [
            "serial_code",
            "approved",
            "approved_id",
            "local",
            "rp_name",
            "main_host",
            "main_host_id",
            "rp_start_date",
            "rp_start_time",
            "rp_duration",
            "doc",
            "sign_up",
            "ongoing",
            "ended"
            ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for update in updated_rp_list:
            writer.writerow(update)

    return updated_rp_list, inform_update


def rp_profile_check(_id) -> List:
    rp_list = rp_id_check()
    found = []

    for rp in rp_list:
        if str(_id) == rp["serial_code"]:
            found.append(rp)

    return found


def rp_profile_check_sign_up(val) -> List:
    if val != 0:
        return

    rp_list = rp_id_check()
    found = []

    for rp in rp_list:
        if rp["sign_up"] == "1":
            found.append(rp)

    return found


def rp_profile_check_ongoing(val) -> List:
    if val != 1:
        return

    rp_list = rp_id_check()
    found = []

    for rp in rp_list:
        if rp["ongoing"] == "1":
            found.append(rp)

    return found


def rp_profile_check_ended(val) -> List:
    if val != 2:
        return

    rp_list = rp_id_check()
    found = []

    for rp in rp_list:
        if rp["ended"] == "1":
            found.append(rp)

    return found


def rp_profile_check_all(val) -> List:
    if val != 3:
        return

    rp_list = rp_id_check()
    found = []

    for rp in rp_list:
        found.append(rp)

    return found
