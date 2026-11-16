import os
import subprocess
import datetime
import time

from src.proxy.fakeproxy import FakeProxy
from src.decoration.paint import paint
from src.managers.json_manager import JsonManager
from src.utilities.file_utilities import FileUtilities
from src.utilities.get_utilities import GetUtilities
from src.utilities.check_utilities import CheckUtilities
from src.minecraft.get_minecraft_server_data import GetMinecraftServerData
from src.managers.log_manager import LogManager
from src.updater.proxy_updater import ProxyUpdater


class ProxyLauncher:
    @staticmethod
    def start_proxy(proxy_type, address, velocity_mode=None):
        """
        Start a Minecraft proxy server of the specified type.

        Args:
            proxy_type (str): The type of proxy to start ('velocity', 'fakeproxy', 'waterfall').
            address (str): The server IP address or domain to connect to.
            velocity_mode (str, optional): The velocity mode for 'velocity' proxy type (default is None).
        """

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = ''

        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "configuring"])}')
        time.sleep(0.5)

        if not ProxyUpdater.ensure_proxy_jar(proxy_type):
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["proxyMessages", "proxyServerNotStartup"])}')
            return None

        server_data = GetMinecraftServerData.get_data(address, bot=False, clean_data=False)

        if server_data is None:
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "invalidArguments", "invalidServer"])}')
            return None

        if JsonManager.get(["proxyConfig", "convertDomainToIP"]):
            address = server_data['ip_port']

        proxy_config_path = f'./src/proxy/settings/{proxy_type}.config'
        with open(proxy_config_path, 'r', encoding='utf8') as f:
            proxy_config = f.read()

        proxy_config, proxy_port = ProxyLauncher.replace_proxy_variables(proxy_type, proxy_config, address, velocity_mode)

        if proxy_type in ['velocity', 'fakeproxy']:
            if JsonManager.get('logs'):
                log_file = LogManager.create_log_file(proxy_type)
                if proxy_type == 'velocity':
                    LogManager.write_log(log_file, 'fakeproxy', f'{current_time} Target: {address}\n')
                else:
                    LogManager.write_log(log_file, 'fakeproxy', f'{current_time} Target: {address} (Forwarding mode: {velocity_mode})\n')

            FileUtilities.write_file(f'./src/proxy/jar/{proxy_type}/velocity.toml', proxy_config, 'w+', True)

            if proxy_type == 'fakeproxy' and FakeProxy.setup(address) is False:
                return None

            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "starting"])}')
            velocity_cmd = JsonManager.get(["proxyConfig", "velocityCommand"])
            if proxy_type == 'fakeproxy' and not os.path.exists('./src/proxy/jar/fakeproxy/Velocity.jar'):
                velocity_cmd = velocity_cmd.replace('Velocity.jar', '../velocity/Velocity.jar')

            subprocess.Popen(f'cd ./src/proxy/jar/{proxy_type} && {velocity_cmd}', stdout=subprocess.PIPE, shell=True)

        else:
            if JsonManager.get('logs'):
                log_file = LogManager.create_log_file('waterfall')
                LogManager.write_log(log_file, 'waterfall', f'{current_time} Target: {address}\n')

            FileUtilities.write_file(f'./src/proxy/jar/{proxy_type}/config.yml', proxy_config, 'w+', True)
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "starting"])}')
            subprocess.Popen(f'cd ./src/proxy/jar/{proxy_type} && {JsonManager.get(["proxyConfig", "waterfallCommand"])}', stdout=subprocess.PIPE, shell=True)

        time.sleep(5)

        if not CheckUtilities.check_local_port(int(proxy_port)):
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["proxyMessages", "proxyServerNotStartup"])}')
            return

        if proxy_type == 'fakeproxy':
            ngrok_ip = GetUtilities.get_ip_ngrok()
            if ngrok_ip is not None:
                paint(f"""\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["proxyMessages", "proxyServerStarted"]).replace("[0]", f"127.0.0.1:{proxy_port} &f&l(&d{ngrok_ip}&f&l)")}""")
            else:
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "fakeproxy", "ipNgrokError"])}')
                paint(f"""\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["proxyMessages", "proxyServerStarted"]).replace("[0]", f"127.0.0.1:{proxy_port}")}""")
        else:
            paint(f"""\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["proxyMessages", "proxyServerStarted"]).replace("[0]", f"127.0.0.1:{proxy_port}")}""")

        if proxy_type == 'fakeproxy':
            FakeProxy.show_data(address, log_file)
        else:
            while True:
                time.sleep(1)

    @staticmethod
    def replace_proxy_variables(proxy_type, proxy_config, address, velocity_mode):
        """Replace placeholders in a proxy configuration string with specific values."""
        if '[[ADDRESS]]' in proxy_config:
            proxy_config = proxy_config.replace('[[ADDRESS]]', address)

        if '[[PORT]]' in proxy_config:
            if proxy_type == 'fakeproxy':
                port = JsonManager.get(['proxyConfig', 'fakeProxyPort'])
            elif proxy_type == 'velocity':
                port = JsonManager.get(['proxyConfig', 'velocityPort'])
            else:
                port = JsonManager.get(['proxyConfig', 'waterfallPort'])

            proxy_config = proxy_config.replace('[[PORT]]', port)
        else:
            port = "2"

        if '[[MODE]]' in proxy_config:
            proxy_config = proxy_config.replace('[[MODE]]', velocity_mode)

        return proxy_config, port
