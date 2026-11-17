import sys

from src.decoration.paint import paint
from src.utilities.get_utilities import GetUtilities


def exit_command(*args):
    """Print the localized stopping message and exit MCPTool cleanly."""
    paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["stopping"])}')
    sys.exit(0)
