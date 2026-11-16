from src.decoration.paint import paint
from src.utilities.bot_launcher import build_bot_command, resolve_java_server, run_bot_command
from src.utilities.get_utilities import GetUtilities


def connect_command(server, username, version, *args):
    """Connects to the specified Minecraft server using a Mineflayer bot."""
    try:
        resolved = resolve_java_server(server)
        if resolved is None:
            return

        ip, port, _ = resolved
        command = build_bot_command('connect', ip, port, username, version, len(GetUtilities.get_spaces()))
        run_bot_command(command)

    except KeyboardInterrupt:
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["commands", "ctrlC"])}')
