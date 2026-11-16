import time

from src.decoration.paint import paint
from src.utilities.bot_launcher import build_bot_command, read_nonempty_file, resolve_java_server, run_bot_command
from src.utilities.check_utilities import CheckUtilities
from src.utilities.get_utilities import GetUtilities


def sendcmd_command(server, username, version, command_file, loop, *args):
    """Connects to the specified Minecraft server and executes a series of commands from a file."""
    try:
        if not read_nonempty_file(command_file, 'sendcmd'):
            return

        if not CheckUtilities.check_loop_argument(loop):
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "invalidArguments", "invalidLoopArgument"])}')
            return

        loop = GetUtilities.get_loop_argument(loop)
        resolved = resolve_java_server(server)
        if resolved is None:
            return

        ip, port, _ = resolved
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "sendcmd", "startingTheAttack"])}')
        command = build_bot_command('sendcmd', ip, port, username, version, command_file, len(GetUtilities.get_spaces()))

        if loop:
            while True:
                time.sleep(4)
                run_bot_command(command)
        else:
            run_bot_command(command)

    except KeyboardInterrupt:
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["commands", "ctrlC"])}')
