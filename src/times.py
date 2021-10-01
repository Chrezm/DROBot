# -*- coding: utf-8 -*-

import time

import discord
from discord.ext import commands

from src import roleplays


async def command_timezone(bot, guild_details, ctx: commands.Context, seconds=None):
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


async def commands_utc(bot, guild_details, ctx: commands.Context, seconds=None):
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

def timezone_time_check(hour_change: int, inc_time: int) -> int:
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
