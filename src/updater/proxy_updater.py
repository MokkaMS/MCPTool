import os
import re
import shutil
import socket
import subprocess
import time
import requests

from src.decoration.print_banner import print_banner
from src.managers.json_manager import JsonManager
from src.utilities.get_utilities import GetUtilities
from src.utilities.check_utilities import CheckUtilities
from src.decoration.paint import paint

FILL_API_BASE = 'https://fill.papermc.io/v3/projects'
FILL_API_HEADERS = {
    'User-Agent': 'MCPTool/4.0.5 (https://github.com/MokkaMS/MCPTool)'
}

VELOCITY_JAR_PATH = 'src/proxy/jar/velocity/Velocity.jar'
WATERFALL_JAR_PATH = 'src/proxy/jar/waterfall/waterfall.jar'


class ProxyUpdater:
    @staticmethod
    def update_proxies():
        """Check for updates for WaterFall and Velocity proxies and update them if necessary."""

        proxy_update_name = 'proxy_update' if not CheckUtilities.check_termux() else 'proxy_update_termux'
        print_banner(proxy_update_name)
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateCheck"]).replace("[0]", "WaterFall")}')

        try:
            url = ProxyUpdater.check_waterfall_update()

            if url is not None:
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateAvailable"]).replace("[0]", "WaterFall")}')
                if ProxyUpdater.download_proxy_jar(url, WATERFALL_JAR_PATH, 'waterfall'):
                    ProxyUpdater._save_proxy_version('waterfallVersion', url)
            else:
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "noUpdatesFound"])}')

            time.sleep(1)
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateCheck"]).replace("[0]", "Velocity")}')
            url = ProxyUpdater.check_velocity_update()

            if url is not None:
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateAvailable"]).replace("[0]", "Velocity")}')
                if ProxyUpdater.download_proxy_jar(url, VELOCITY_JAR_PATH, 'Velocity'):
                    ProxyUpdater._save_proxy_version('velocityVersion', url)
            else:
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "noUpdatesFound"])}')

            time.sleep(1)

        except (KeyError, ValueError, TypeError):
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateFailed"])}')
            time.sleep(1)

        except KeyboardInterrupt:
            return

    @staticmethod
    def download_proxy_jar(url, dest_path, label):
        """
        Download a proxy JAR to dest_path after validating the HTTP response and ZIP header.

        Returns:
            bool: True if the download succeeded, False otherwise.
        """
        temp_folder = 'mcptool_temp'
        os.makedirs(temp_folder, exist_ok=True)
        temp_jar = os.path.join(temp_folder, os.path.basename(dest_path))

        try:
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "downloadingUpdate"])}')
            response = requests.get(url, headers=FILL_API_HEADERS, timeout=60)

            if response.status_code != 200 or not response.content.startswith(b'PK'):
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateFailed"])}')
                return False

            with open(temp_jar, 'wb') as f:
                f.write(response.content)

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            if os.path.exists(dest_path):
                os.remove(dest_path)
            shutil.copy(temp_jar, dest_path)
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateCompleted"]).replace("[0]", label)}')
            return True

        except (requests.RequestException, OSError):
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateFailed"])}')
            return False

        finally:
            if os.path.exists(temp_jar):
                os.remove(temp_jar)
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder, ignore_errors=True)

    @staticmethod
    def ensure_proxy_jar(proxy_type):
        """Ensure the required proxy JAR exists on disk, downloading it if missing."""
        if proxy_type in ('velocity', 'fakeproxy'):
            if os.path.exists(VELOCITY_JAR_PATH):
                return True
            url = ProxyUpdater._get_latest_fill_url('velocity', preferred_group=None if (ProxyUpdater._get_java_major_version() or 0) >= 25 else '3.0.0')
            url = url or JsonManager.get(['proxyConfig', 'velocityVersion'])
            return bool(url and ProxyUpdater.download_proxy_jar(url, VELOCITY_JAR_PATH, 'Velocity'))

        if os.path.exists(WATERFALL_JAR_PATH):
            return True
        url = ProxyUpdater._get_latest_fill_url('waterfall') or JsonManager.get(['proxyConfig', 'waterfallVersion'])
        return bool(url and ProxyUpdater.download_proxy_jar(url, WATERFALL_JAR_PATH, 'waterfall'))

    @staticmethod
    def _save_proxy_version(config_key, url):
        settings = JsonManager.load_json('./config/config.json')
        settings['proxyConfig'][config_key] = url
        JsonManager.save_json(settings, './config/config.json')

    @staticmethod
    def _get_java_major_version():
        """Return the installed Java major version, or None if unavailable."""
        try:
            result = subprocess.run(
                ['java', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stderr or result.stdout
            match = re.search(r'version "(\d+)(?:\.(\d+))?', output)
            if not match:
                return None
            major = int(match.group(1))
            if major == 1 and match.group(2):
                return int(match.group(2))
            return major
        except (OSError, subprocess.SubprocessError, ValueError):
            return None

    @staticmethod
    def _get_latest_fill_url(project, preferred_group=None):
        """Query PaperMC Fill v3 API for the latest server JAR download URL."""
        try:
            project_resp = requests.get(
                f'{FILL_API_BASE}/{project}',
                headers=FILL_API_HEADERS,
                timeout=10
            )
            project_resp.raise_for_status()
            versions_by_group = project_resp.json().get('versions', {})
            if not versions_by_group:
                return None

            if preferred_group and preferred_group in versions_by_group:
                version_list = versions_by_group[preferred_group]
            else:
                version_list = next(iter(versions_by_group.values()))

            if not version_list:
                return None

            target_version = version_list[0]
            builds_resp = requests.get(
                f'{FILL_API_BASE}/{project}/versions/{target_version}/builds',
                headers=FILL_API_HEADERS,
                timeout=10
            )
            builds_resp.raise_for_status()
            builds = builds_resp.json()
            if not builds:
                return None

            return builds[0].get('downloads', {}).get('server:default', {}).get('url')
        except (socket.gaierror, socket.timeout, requests.RequestException):
            return None

    @staticmethod
    def check_waterfall_update():
        """Return the latest Waterfall JAR URL if it differs from config, else None."""
        url = ProxyUpdater._get_latest_fill_url('waterfall')
        if url and (not os.path.exists(WATERFALL_JAR_PATH) or JsonManager.get(["proxyConfig", "waterfallVersion"]) != url):
            return url
        return None

    @staticmethod
    def check_velocity_update():
        """
        Return the latest compatible Velocity JAR URL if it differs from config, else None.

        Velocity 4.x requires Java 25+, whereas Velocity 3.x (3.5.1) runs on Java 21
        and remains compatible with Adventure 4 plugins.
        """
        java_major = ProxyUpdater._get_java_major_version()
        preferred_group = None if (java_major is not None and java_major >= 25) else '3.0.0'
        url = ProxyUpdater._get_latest_fill_url('velocity', preferred_group=preferred_group)
        if url and (not os.path.exists(VELOCITY_JAR_PATH) or JsonManager.get(["proxyConfig", "velocityVersion"]) != url):
            return url
        return None
