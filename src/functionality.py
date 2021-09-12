# -*- coding: utf-8 -*-
import discord
from discord.ext import commands

from typing import Dict

class Functionality():
    def __init__(self, bot: commands.Bot = None, guild_details: Dict = None):
        @bot.event
        async def on_ready():
            print('Logged in as {0.user}'.format(bot))

        @bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                await ctx.send('Unrecognized command.')
                return
            raise error

        @bot.event
        async def on_message(message):
            if message.author == bot.user:
                return

            if message.channel.name in guild_details.relaying_channels:
                await _relay_message(
                    message,
                    prefix=guild_details.relaying_prefix,
                    suffix=guild_details.relaying_suffix)

            await bot.process_commands(message)

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

        @bot.command(
            name='ping',
            brief='Returns Pong. Used to check if the bot is up and running',
            help=('Returns Pong. If the bot does not respond, it means it is down or something '
                  'terrible has happened.'),
        )
        async def ping(ctx: commands.Context):
            if not _validate_command(ctx):
                return

            await ctx.channel.send('Pong.')


        @bot.command(
            name='rpactive',
            brief='Changes your RP Active status',
            help=('If you did not have the RP Active role, the bot will give it to you. If you '
                  'already had it, the bot will take it away from you.'),
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
