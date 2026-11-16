import os
import requests
import shutil

from src.utilities.get_utilities import GetUtilities
from src.decoration.paint import paint

PAPERMC_HEADERS = {
    'User-Agent': 'MCPTool/4.0.5 (https://github.com/MokkaMS/MCPTool)'
}


def update_velocity(url):
    """
    Update Velocity.jar and replace the current one.

    Args:
        url (str): Velocity download link.

    Returns:
        bool: True if the update succeeded, False otherwise.
    """

    temp_folder = 'mcptool_temp'
    os.makedirs(temp_folder, exist_ok=True)
    temp_jar = f'{temp_folder}/Velocity.jar'

    try:
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "downloadingUpdate"])}')
        velocity = requests.get(url, headers=PAPERMC_HEADERS, timeout=60)

        if velocity.status_code != 200 or not velocity.content.startswith(b'PK'):
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateFailed"])}')
            return False

        with open(temp_jar, 'wb') as f:
            f.write(velocity.content)

        if os.path.exists('src/proxy/jar/fakeproxy/Velocity.jar'):
            os.remove('src/proxy/jar/fakeproxy/Velocity.jar')
        if os.path.exists('src/proxy/jar/velocity/Velocity.jar'):
            os.remove('src/proxy/jar/velocity/Velocity.jar')
        shutil.copy(temp_jar, 'src/proxy/jar/fakeproxy/Velocity.jar')
        shutil.copy(temp_jar, 'src/proxy/jar/velocity/Velocity.jar')
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateCompleted"]).replace("[0]", "Velocity")}')
        return True

    except (requests.RequestException, OSError):
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["proxyMessages", "updateFailed"])}')
        return False

    finally:
        if os.path.exists(temp_jar):
            os.remove(temp_jar)
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder, ignore_errors=True)
