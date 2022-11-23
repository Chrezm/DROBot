# -*- coding: utf-8 -*-

from src.guild import Guild
from typing import Dict, Set


class SampleGuild(Guild):
    # General commands
    def command_channels(self) -> Set[str]:
        return {
            'bot-commands',
        }

    def command_always_accept_from_roles(self) -> Set[int]:
        return {
            816054356091994164,
        }


    # Relaying messages
    def relaying_channels(self) -> Dict[str, str]:
        return {
            'test-1': 'test-2',
        }

    def relaying_prefix(self) -> str:
        return ''

    def relaying_suffix(self) -> str:
        return '<@&816054356091994164>'

    def relaying_ignore_roles(self) -> Set[int]:
        return {
            892557549944057887,
        }


    # Honeypot
    def honeypot_channels(self) -> Set[str]:
        return {
            'bots-only',
        }


    # Upload
    def upload_server_paths(self) -> Dict[str, str]:
        return {
            'main': 'D:\\AO\\TsuserverDR'
        }

    def upload_asset_paths(self) -> Dict[str, str]:
        return {
            'areas': 'config\\area_lists',
            'music': 'config\\music_lists',
            'backgrounds': 'config\\bg_lists',
            'characters': 'config\\char_lists',
        }

    def upload_max_size_bytes(self) -> int:
        return 204800  # 200 Kibibytes

    def upload_log_channels(self) -> Set[str]:
        return {
            'test-2',
        }


    # Role: Bot Muted
    def bot_muted_role_name(self) -> str:
        return 'muted'

    def bot_muted_role_id(self) -> int:
        return 1016481835456397362


    # Role: RP Active
    def rp_active_role_name(self) -> str:
        return 'epic role'

    def rp_active_role_id(self) -> int:
        return 816054356091994164


    # Role: Dev Tester
    def dev_tester_role_name(self) -> str:
        return 'dev tester'

    def dev_tester_role_id(self) -> int:
        return 892586465907855400


    # Role: Bot Maintainer
    def bot_maintainer_role_name(self) -> str:
        return 'bot maintainer'

    def bot_maintainer_role_id(self) -> int:
        return 892524724230434826
