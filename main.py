import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="$")


class test_discord():
    relaying_channels = {
        'test-1': 'test-2'
        }
    relaying_prefix = ''
    relaying_suffix = '<@&816054356091994164>'
    relaying_ignore_roles = {
        #816054356091994164
        }

    command_channels = {
        'bot-commands',
    }
    command_always_accept_from_roles = {
        816054356091994164
    }

    rp_active_role_name = 'epic role'
    rp_active_role_id = 816054356091994164


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


def _validate_command(ctx: commands.Context) -> bool:
    if ctx.author == bot.user:
        return False

    if ctx.channel.name in guild_details.command_channels:
        return True

    for role in ctx.author.roles:
        if role.id in guild_details.command_always_accept_from_roles:
            return True

    return False


@bot.command(name='ping')
async def ping(ctx: commands.Context):
    if not _validate_command(ctx):
        return

    await ctx.channel.send('Pong.')


@bot.command(name='rpactive')
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


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # No need to do anything fancy here
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


def get_channel(name):
    channel = discord.utils.get(bot.get_all_channels(), name=name)
    if not channel:
        raise ValueError(f'Target channel {name} not found.')
    return channel


async def _relay_message(message, prefix='', suffix=''):
    for role in message.author.roles:
        if role.id in guild_details.relaying_ignore_roles:
            return

    to_channel_name = guild_details.relaying_channels[message.channel.name]
    to_channel = get_channel(to_channel_name)
    relay_format = (
        '**RELAYED MESSAGE**\r\n'
        '**User**: {message.author.name}#{message.author.discriminator} (<@{message.author.id}>)\r\n'
        '**Channel**: <#{message.channel.id}>\r\n'
        '**Time**: {message.created_at}\r\n'
        '**Message**: {message.content}\r\n'
        )
    if prefix:
        relay_format = '{prefix}\r\n' + relay_format
    if suffix:
        relay_format += '{suffix}'

    final_message = relay_format.format(
        message=message,
        prefix=prefix,
        suffix=suffix,
        )

    await message.delete()
    await to_channel.send(final_message)


if __name__ == '__main__':
    production = False
    if production:
        token_file = '.token'
        from DRO_discord import DRO_discord
        guild_details = DRO_discord()
    else:
        token_file = 'test.token'
        guild_details = test_discord()
        print('THIS IS A TEST BOT')

    try:
        with open(token_file, 'r') as f:
            token = f.read()
        if not token:
            raise RuntimeError
    except (OSError, RuntimeError):
        raise RuntimeError(f'No token file or contents found: {token_file}')

    bot.run(token)
