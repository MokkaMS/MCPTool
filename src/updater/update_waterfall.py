import os
import requests
import shutil

from src.utilities.get_utilities import GetUtilities
from src.decoration.paint import paint

PAPERMC_HEADERS = {
    'User-Agent': 'MCPTool/4.0.5 (https://github.com/MokkaMS/MCPTool)'
}


def update_waterfall(url):
    """
    Update waterfall.jar and replace the current one.

    Args:
        url (str): waterfall download link.

    Returns:
        bool: True if the update succeeded, False otherwise.
    """

    temp_folder = 'mcptool_temp'
    os.makedirs(temp_folder, exist_ok=True)
    temp_jar = f'{temp_folder}/waterfall.jar'

    try:
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "downloadingUpdate"])}')
        waterfall = requests.get(url, headers=PAPERMC_HEADERS, timeout=60)

        if waterfall.status_code != 200 or not waterfall.content.startswith(b'PK'):
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateFailed"])}')
            return False

        with open(temp_jar, 'wb') as f:
            f.write(waterfall.content)

        if os.path.exists('src/proxy/jar/waterfall/waterfall.jar'):
            os.remove('src/proxy/jar/waterfall/waterfall.jar')
        shutil.copy(temp_jar, 'src/proxy/jar/waterfall/waterfall.jar')
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateCompleted"]).replace("[0]", "waterfall")}')
        return True

    except (requests.RequestException, OSError):
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateFailed"])}')
        return False

    finally:
        if os.path.exists(temp_jar):
            os.remove(temp_jar)
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder, ignore_errors=True)
