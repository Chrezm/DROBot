# -*- coding: utf-8 -*-

import discord
from discord.ext import commands


async def command_rpactive(bot, guild_details, ctx):
    await _optin_role(ctx,
                      guild_details.rp_active_role_name,
                      guild_details.rp_active_role_id)


async def command_devtester(bot, guild_details, ctx):
    await _optin_role(ctx,
                      guild_details.dev_tester_role_name,
                      guild_details.dev_tester_role_id)


async def _optin_role(ctx: commands.Context, role_name: str, role_id: int):
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
