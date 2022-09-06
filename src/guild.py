# -*- coding: utf-8 -*-

from typing import Dict, Set

class Guild():
    # General commands
    def command_channels(self) -> Set[str]:
        raise NotImplementedError

    def command_always_accept_from_roles(self) -> Set[int]:
        raise NotImplementedError


    # Relaying messages
    def relaying_channels(self) -> Dict[str, str]:
        raise NotImplementedError

    def relaying_prefix(self) -> str:
        raise NotImplementedError

    def relaying_suffix(self) -> str:
        raise NotImplementedError

    def relaying_ignore_roles(self) -> Set[int]:
        raise NotImplementedError


    # Honeypot
    def honeypot_channels(self) -> Set[str]:
        raise NotImplementedError


    # Upload
    def upload_server_paths(self) -> Dict[str, str]:
        raise NotImplementedError

    def upload_asset_paths(self) -> Dict[str, str]:
        raise NotImplementedError

    def upload_max_size_bytes(self) -> int:
        raise NotImplementedError

    def upload_log_channels(self) -> Set[str]:
        raise NotImplementedError


    # Role: Bot Muted
    def bot_muted_role_name(self) -> str:
        raise NotImplementedError

    def bot_muted_role_id(self) -> int:
        raise NotImplementedError


    # Role: RP Active
    def rp_active_role_name(self) -> str:
        raise NotImplementedError

    def rp_active_role_id(self) -> int:
        raise NotImplementedError


    # Role: Dev Tester
    def dev_tester_role_name(self) -> str:
        raise NotImplementedError

    def dev_tester_role_id(self) -> int:
        raise NotImplementedError


    # Role: Bot Maintainer
    def bot_maintainer_role_name(self) -> str:
        raise NotImplementedError

    def bot_maintainer_role_id(self) -> int:
        raise NotImplementedError
