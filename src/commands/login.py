from src.decoration.paint import paint
from src.utilities.bot_launcher import build_bot_command, read_nonempty_file, resolve_java_server, run_bot_command
from src.utilities.get_utilities import GetUtilities


def login_command(server, username, version, password_file, *args):
    """Connect a bot to the specified server to try to guess the user's password."""
    try:
        if not read_nonempty_file(password_file, 'login'):
            return

        resolved = resolve_java_server(server)
        if resolved is None:
            return

        ip, port, _ = resolved
        command = build_bot_command('login', ip, port, username, version, password_file, len(GetUtilities.get_spaces()))
        run_bot_command(command)

    except KeyboardInterrupt:
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["commands", "ctrlC"])}')
