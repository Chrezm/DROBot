import discord

client = discord.Client()


class test_discord():
    relaying_channels = {
        'test-1': 'test-2'
        }
    relaying_prefix = ''
    relaying_suffix = '<@&816054356091994164>'
    relaying_ignore_roles = {
        816054356091994164
        }


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name in guild_details.relaying_channels:
        await _relay_message(
            message,
            prefix=guild_details.relaying_prefix,
            suffix=guild_details.relaying_suffix)


def get_channel(name):
    channel = discord.utils.get(client.get_all_channels(), name=name)
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

    client.run(token)
