import requests
import time
import re

from src.managers.json_manager import JsonManager
from src.api.api import convert_server_data
from src.api.minecraft_server_data import JavaServerData, BedrockServerData, MinecraftServerData
from src.utilities.check_utilities import CheckUtilities
from src.utilities.get_utilities import GetUtilities


class GetMinecraftServerData:
    @staticmethod
    def get_data(server, bot=True, clean_data=True):
        """
        Get Minecraft server data from different APIs based on configuration.

        Args:
            server (str): The address of the Minecraft server.

        Returns:
            JavaServerData or None or str: Minecraft server data as a JavaServerData object if successful,
            None if an API request fails or the server is not responding, or 'API_ERROR' if there's a configuration error.
        """

        # Add a short delay before making the API request.
        time.sleep(0.5)

        try:
            # Check the configured API in the JsonManager.
            if JsonManager.get('api') == 'localhost':
                return GetMinecraftServerData.sort_dictionary(GetMinecraftServerData.get_data_via_local_API(server, bot, clean_data))

            elif JsonManager.get('api') == 'mcsrvstat.us':
                return GetMinecraftServerData.sort_dictionary(convert_server_data(GetMinecraftServerData.get_data_via_mcsrvstatus(server, bot, clean_data)))

            elif JsonManager.get('api') == 'mcstatus.io':
                return GetMinecraftServerData.sort_dictionary(convert_server_data(GetMinecraftServerData.get_data_via_mcstatusio(server, bot, clean_data)))

            else:
                return 'API_ERROR'
                
        except KeyboardInterrupt:
            return None
        
    @staticmethod
    def get_data_via_local_API(server, bot, clean_data):
        """
        Retrieve Minecraft server data via a local API.

        Args:
            server (str): The address of the Minecraft server.

        Returns:
            dict or None or str: Minecraft server data as a dictionary if successful,
            None if the API request fails, or 'API_ERROR' if there's an API-related error.
        """

        try:
            # Get the local API port from the configuration.
            local_api_port = JsonManager.get('local_api_port')

            # Send a GET request to the local API with the server address as a parameter.
            response = requests.get(f'http://127.0.0.1:{local_api_port}/api/minecraft_server_data',
                            params={'server_address': server, 'bot': bot, 'clean_data': clean_data}, timeout=5)
                
            # Check if the API request was successful (status code 200).
            if response.status_code == 200:
                response = response.json()
                return response
            
            else:
                return None

        except KeyboardInterrupt:
            return None

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects, requests.exceptions.RequestException,
                ConnectionError) as e:

            settings = JsonManager.load_json('./config/config.json')
            settings['api'] = 'mcsrvstat.us'
            JsonManager.save_json(settings, './config/config.json')
            return None

    @staticmethod
    def get_data_via_mcsrvstatus(server, bot, clean_data):
        """
        Retrieve Minecraft server data via the mcsrvstatus API.

        Args:
            server (str): The address of the Minecraft server.

        Returns:
            JavaServerData or None or str: Minecraft server data as a JavaServerData object if successful,
            None if the API request fails or the server is not responding, or 'API_ERROR' if there's an API-related error.
        """

        try:
            # Send a GET request to the mcsrvstatus API with the server address.
            response = requests.get(f'https://api.mcsrvstat.us/3/{server}', headers={'User-Agent': 'MCPTool/4.0.5 (https://github.com/MokkaMS/MCPTool)'}, timeout=10)

            # Check if the API request was successful (status code 200) and the server is responding (ping is true).
            if response.status_code == 200 and response.json()['online']:
                r_json = response.json()

                motd_raw = (r_json.get("motd") or {}).get("raw") or []
                motd = '\n'.join(motd_raw[:2]) if motd_raw else ''
                version = f'{r_json.get("version", "")}'
                protocol_ver = (r_json.get("protocol") or {}).get("version", "47")
                players_data = r_json.get("players") or {}
                player_sample = players_data.get("list")
                info_raw = (r_json.get("info") or {}).get("raw")

                if clean_data:
                    motd = GetMinecraftServerData.clean_data(motd)
                    version = GetMinecraftServerData.clean_data(version)

                if bot:
                    return JavaServerData(
                        'Java',
                        f'{r_json["ip"]}:{r_json["port"]}',
                        motd,
                        version,
                        protocol_ver,
                        players_data.get("online", '0'),
                        players_data.get("max", '0'),
                        GetUtilities.get_clean_list_player_names(player_sample) if player_sample else None,
                        player_sample if player_sample is not None else info_raw,
                        r_json.get("icon"),
                        None,
                        [],
                        None,
                        MinecraftServerData.get_bot_response_sync(f'{r_json["ip"]}:{r_json["port"]}', str(protocol_ver))
                    )

                else:
                    return JavaServerData(
                        'Java',
                        f'{r_json["ip"]}:{r_json["port"]}',
                        motd,
                        version,
                        protocol_ver,
                        players_data.get("online", '0'),
                        players_data.get("max", '0'),
                        GetUtilities.get_clean_list_player_names(player_sample) if player_sample else None,
                        player_sample if player_sample is not None else info_raw,
                        r_json.get("icon"),
                        None,
                        [],
                        None,
                        None
                    )

            else:
                response = requests.get(f'https://api.mcsrvstat.us/bedrock/3/{server}', headers={'User-Agent': 'MCPTool/4.0.5 (https://github.com/MokkaMS/MCPTool)'}, timeout=10)

                if response.status_code == 200 and response.json()['online']:
                    r_json = response.json()
                    motd_raw = (r_json.get("motd") or {}).get("raw") or []
                    motd = ' '.join(motd_raw[:2]) if motd_raw else ''
                    version = f'{r_json.get("version", "")}'
                    protocol_ver = (r_json.get("protocol") or {}).get("version", "0")
                    players_data = r_json.get("players") or {}

                    if clean_data:
                        motd = GetMinecraftServerData.clean_data(motd)
                        version = GetMinecraftServerData.clean_data(version)

                    return BedrockServerData(
                        'Bedrock',
                        f'{r_json["ip"]}:{r_json["port"]}',
                        motd,
                        version,
                        protocol_ver,
                        r_json.get('software'),
                        players_data.get("online", "0"),
                        players_data.get("max", "0"),
                        (r_json.get('map') or {}).get('raw'),
                        r_json.get('gamemode'),
                        None,
                        None,
                    )

        except KeyboardInterrupt:
            return None

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects, requests.exceptions.RequestException,
                ConnectionError) as e:
            
            settings = JsonManager.load_json('./config/config.json')
            settings['api'] = 'mcstatus.io'
            JsonManager.save_json(settings, './config/config.json')
            return None
        

    @staticmethod
    def get_data_via_mcstatusio(server, bot, clean_data):
        """
        Retrieve Minecraft server data via the mcsrvstatus API.

        Args:
            server (str): The address of the Minecraft server.

        Returns:
            JavaServerData or None or str: Minecraft server data as a JavaServerData object if successful,
            None if the API request fails or the server is not responding, or 'API_ERROR' if there's an API-related error.
        """

        try:
            # Send a GET request to the mcsrvstatus API with the server address.
            response = requests.get(f'https://api.mcstatus.io/v2/status/java/{server}', timeout=10)

            # Check if the API request was successful (status code 200) and the server is responding (ping is true).
            if response.status_code == 200 and response.json()['online']:
                r_json = response.json()
                
                motd = (r_json.get('motd') or {}).get('raw') or ''
                version_info = r_json.get("version") or {}
                version = version_info.get('name_raw') or version_info.get('name_clean') or ''
                protocol_ver = version_info.get("protocol", '47')
                players_data = r_json.get("players") or {}
                player_sample = players_data.get("list")
                info_raw = (r_json.get("info") or {}).get("raw")

                if clean_data:
                    motd = GetMinecraftServerData.clean_data(motd)
                    version = GetMinecraftServerData.clean_data(version)

                if bot:
                    return JavaServerData(
                        'Java',
                        f'{r_json["ip_address"]}:{r_json["port"]}',
                        motd,
                        version,
                        protocol_ver,
                        players_data.get("online", '0'),
                        players_data.get("max", '0'),
                        GetUtilities.get_clean_list_player_names(player_sample) if player_sample else None,
                        player_sample if player_sample is not None else info_raw,
                        r_json.get("icon"),
                        None,
                        [],
                        None,
                        MinecraftServerData.get_bot_response_sync(f'{r_json["ip_address"]}:{r_json["port"]}', str(protocol_ver))
                    )

                else:
                    return JavaServerData(
                        'Java',
                        f'{r_json["ip_address"]}:{r_json["port"]}',
                        motd,
                        version,
                        protocol_ver,
                        players_data.get("online", '0'),
                        players_data.get("max", '0'),
                        GetUtilities.get_clean_list_player_names(player_sample) if player_sample else None,
                        player_sample if player_sample is not None else info_raw,
                        r_json.get("icon"),
                        None,
                        [],
                        None,
                        None
                    )

            else:
                response = requests.get(f'https://api.mcstatus.io/v2/status/bedrock/{server}', timeout=10)

                if response.status_code == 200 and response.json()['online']:
                    r_json = response.json()

                    motd = (r_json.get('motd') or {}).get('raw') or ''
                    version_info = r_json.get("version") or {}
                    version = version_info.get('name') or ''
                    protocol_ver = version_info.get("protocol", '47')
                    players_data = r_json.get("players") or {}

                    if clean_data:
                        motd = GetMinecraftServerData.clean_data(motd)
                        version = GetMinecraftServerData.clean_data(version)

                    return BedrockServerData(
                        'Bedrock',
                        f'{r_json["ip_address"]}:{r_json["port"]}',
                        motd,
                        version,
                        protocol_ver,
                        r_json.get('software'),
                        players_data.get("online", "0"),
                        players_data.get("max", "0"),
                        (r_json.get('map') or {}).get('raw'),
                        r_json.get('gamemode'),
                        None,
                        None,
                    )

        except KeyboardInterrupt:
            return None

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects, requests.exceptions.RequestException,
                ConnectionError) as e:
            
            settings = JsonManager.load_json('./config/config.json')
            settings['api'] = 'mcsrvstat.us'
            JsonManager.save_json(settings, './config/config.json')
            return None
        
    @staticmethod
    def sort_dictionary(response):
        if response is not None:
            if response['platform_type'] == 'Java':
                key_order = ['platform_type', 'ip_port', 'motd', 'version', 'protocol', 'connected_players', 'max_player_limit', 'player_list', 'default_player_list', 'favicon', 'mod_type', 'mod_list', 'latency', 'bot_response']

            else:
                key_order = ['platform_type', 'ip_port', 'motd', 'version', 'protocol', 'brand', 'connected_players', 'max_player_limit', 'map', 'gamemode', 'latency', 'bot_response']

            return {key: response[key] for key in key_order if key in response}
        
        else:
            return None


    @staticmethod
    def clean_data(data):
        """
        Clean and format data by removing extra spaces and newline characters.

        Args:
            data (str or dict): The data to be cleaned.

        Returns:
            str: The cleaned and formatted data.
        """

        if type(data) != str:
            data = data.raw

        # Remove newline characters.
        data = str(data).replace('\n', '')

        # Replace multiple spaces with a single space.
        data = re.sub(' +', ' ', data)

        # Remove hexadecimal colors.
        data = re.sub(r'§#[0-9A-Fa-f]{6}', '', data)
        return data