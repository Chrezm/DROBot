# -*- coding: utf-8 -*-

from src.guild import Guild
from typing import Dict, Set


class Sample(Guild):
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


    def command_channels(self) -> Set[str]:
        return {
            'bot-commands',
        }

    def command_always_accept_from_roles(self) -> Set[int]:
        return {
            816054356091994164,
        }


    def rp_active_role_name(self) -> str:
        return 'epic role'

    def rp_active_role_id(self) -> int:
        return 816054356091994164


    def dev_tester_role_name(self) -> str:
        return 'dev tester'

    def dev_tester_role_id(self) -> int:
        return 892586465907855400


    def bot_maintainer_role_name(self) -> str:
        return 'bot maintainer'

    def bot_maintainer_role_id(self) -> int:
        return 892524724230434826
