import os
import subprocess

from src.decoration.paint import paint
from src.managers.json_manager import JsonManager
from src.minecraft.get_minecraft_server_data import GetMinecraftServerData
from src.utilities.check_utilities import CheckUtilities
from src.utilities.get_utilities import GetUtilities


def resolve_java_server(server):
    """Fetch server data and return (ip, port, server_data) for a Java server, or None on failure."""
    paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "gettingDataFromServer"])}')
    server_data = GetMinecraftServerData.get_data(server, bot=False)

    if server_data is None:
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "invalidArguments", "invalidServer"])}')
        return None

    if server_data['platform_type'] != 'Java':
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "errorBedrockServer"])}')
        return None

    ip, port = server_data['ip_port'].split(':')
    return ip, port, server_data


def read_nonempty_file(file_path, empty_key):
    """Validate that file_path exists and is non-empty, printing the localized error otherwise."""
    if not os.path.exists(file_path):
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "invalidArguments", "invalidFile"]).replace("[0]", file_path)}')
        return False

    with open(file_path, 'r', encoding=CheckUtilities.check_file_encoding(file_path)) as f:
        lines = f.readlines()

    if len(lines) == 0:
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", empty_key, "emptyFile"])}')
        return False

    return True


def build_bot_command(script_name, *args):
    """Construct the NodeJS command for a Mineflayer bot script with optional proxy file."""
    node_cmd = JsonManager.get(["minecraftServerOptions", "nodeCommand"]) or 'node'
    joined_args = ' '.join(str(arg) for arg in args)
    command = f'{node_cmd} ./src/scripts/{script_name}.js {joined_args}'

    if JsonManager.get(["minecraftServerOptions", "proxy"]):
        command += f' {JsonManager.get(["minecraftServerOptions", "proxyFileForTheBot"])}'

    return command


def run_bot_command(command):
    """Execute a Mineflayer bot command once."""
    subprocess.run(command, shell=True)
