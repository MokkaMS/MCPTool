import json
import sys
import time
import requests

from src.decoration.print_banner import print_banner
from src.managers.json_manager import JsonManager
from src.utilities.get_utilities import GetUtilities
from src.utilities.check_utilities import CheckUtilities

REPO_URL = 'https://github.com/MokkaMS/MCPTool'
REMOTE_CONFIG_URL = 'https://raw.githubusercontent.com/MokkaMS/MCPTool/main/config/config.json'


class MCPToolUpdater:
    @staticmethod
    def show_banner_update():
        """
        Display an update banner and check MokkaMS/MCPTool for newer releases.
        """

        try:
            update_banner_name = 'update' if not CheckUtilities.check_termux() else 'update_termux'

            print_banner(
                update_banner_name,
                GetUtilities.get_translated_text(['banners', 'update', 'title']),
                GetUtilities.get_translated_text(['banners', 'update', 'checkingUpdates']),
                '', '', '', '', ''
            )

            time.sleep(1)

            if MCPToolUpdater.check_update():
                print_banner(
                    update_banner_name,
                    GetUtilities.get_translated_text(['banners', 'update', 'title']),
                    GetUtilities.get_translated_text(['banners', 'update', 'checkingUpdates']),
                    GetUtilities.get_translated_text(['banners', 'update', 'newVersion']),
                    '', '', '', ''
                )

                time.sleep(1)

                print_banner(
                    update_banner_name,
                    GetUtilities.get_translated_text(['banners', 'update', 'title']),
                    GetUtilities.get_translated_text(['banners', 'update', 'checkingUpdates']),
                    GetUtilities.get_translated_text(['banners', 'update', 'newVersion']),
                    GetUtilities.get_translated_text(['banners', 'update', 'url']),
                    f'&a&l{REPO_URL}', ''
                )

                time.sleep(10)
                sys.exit()

            else:
                print_banner(
                    update_banner_name,
                    GetUtilities.get_translated_text(['banners', 'update', 'title']),
                    GetUtilities.get_translated_text(['banners', 'update', 'checkingUpdates']),
                    GetUtilities.get_translated_text(['banners', 'update', 'notFound']),
                    '', '', ''
                )

                time.sleep(2)

        except KeyboardInterrupt:
            return

    @staticmethod
    def _parse_version(version_str):
        """Parse a dot-separated version string into a tuple of ints."""
        parts = []
        for part in str(version_str).strip().split('.'):
            digits = ''.join(ch for ch in part if ch.isdigit())
            parts.append(int(digits) if digits else 0)
        return tuple(parts)

    @staticmethod
    def check_update():
        """
        Check if a newer version is available on MokkaMS/MCPTool.

        Returns:
            bool: True if a newer version is available, False otherwise.
        """

        current_version = JsonManager.get('currentVersion')
        latest_version = MCPToolUpdater.get_latest_version()

        if latest_version is None or current_version is None:
            return False

        return MCPToolUpdater._parse_version(latest_version) > MCPToolUpdater._parse_version(current_version)

    @staticmethod
    def get_latest_version():
        """
        Retrieve the latest version of MCPTool from MokkaMS/MCPTool on GitHub.

        Returns:
            str or None: The latest version number as a string, or None on error.
        """

        update_url = JsonManager.get('updateConfigUrl') or REMOTE_CONFIG_URL

        try:
            response = requests.get(update_url, timeout=5)
            js = json.loads(response.text)
            return js.get('currentVersion')
        except Exception:
            return None
