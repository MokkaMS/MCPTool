import time

from src.decoration.paint import paint
from src.utilities.bot_launcher import build_bot_command, resolve_java_server, run_bot_command
from src.utilities.check_utilities import CheckUtilities
from src.utilities.get_utilities import GetUtilities


def kickall_command(server, version, loop, *args):
    """Connects to the specified Minecraft server and disconnects all listed players."""
    try:
        if not CheckUtilities.check_loop_argument(loop):
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "invalidArguments", "invalidLoopArgument"])}')
            return

        loop = GetUtilities.get_loop_argument(loop)
        resolved = resolve_java_server(server)
        if resolved is None:
            return

        ip, port, server_data = resolved
        players = []
        sample = server_data['default_player_list']

        if sample:
            for player in sample:
                if type(player) == dict and player['name'] != 'Anonymous Player':
                    players.append(player['name'])
                elif type(player) != dict:
                    players = []
                    break

        if not players:
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "kickall", "noPlayers"])}')
            return

        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "kickall", "startingTheAttack"])}')

        while True:
            if loop:
                time.sleep(1)

            for player in players:
                command = build_bot_command('kick', ip, port, player, version, len(GetUtilities.get_spaces()))
                run_bot_command(command)

            if not loop:
                break

    except KeyboardInterrupt:
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["commands", "ctrlC"])}')
