import shutil
import subprocess
import socket
import os

from src.managers.json_manager import JsonManager


class CheckUtilities:
    @staticmethod
    def check_language(language):
        """
        Check if the entered language is valid.

        Args:
            language (str): Language.

        Returns:
            bool: Returns true if the language is valid.
        """

        valid_languages = os.listdir('./config/lang/')
        language += '.json'

        if language in valid_languages:
            return True

        return False

    @staticmethod
    def check_local_port(port):
        """
        Check whether a local TCP port is listening.
        """

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex(('127.0.0.1', port))
        s.close()

        if result == 0:
            return True

        return False

    @staticmethod
    def check_termux():
        """
        Check if MCPTool is running on Termux

        Returns:
            bool: True if "ANDROID_ROOT" is found in `os.environ`
        """

        return 'ANDROID_ROOT' in os.environ

    @staticmethod
    def check_ngrok():
        """
        Check if ngrok is installed on the system.

        Returns:
            bool: Returns true if it is installed
        """

        if subprocess.call(f'{JsonManager.get(["proxyConfig", "ngrokCommand"])} version >nul 2>&1', shell=True) != 0:
            return False

        return True

    @staticmethod
    def check_ip_address(ip_address):
        """
        Check if the ip address is valid.

        Args:
            ip_address (str): IP Address.

        Returns
            bool: Returns True if the entered ip is valid.
        """

        try:
            socket.inet_pton(socket.AF_INET, ip_address)
            return True

        except socket.error:
            return False

    @staticmethod
    def check_scan_method(method):
        """
        Check the scanning method is valid.

        Args:
            method (str): Scan method

        Returns:
            bool: Returns True if the scan method is valid.
        """

        methods = [
            'nmap', 'qubo', 'quboscanner', 'masscan', 'mcscan', 'async', 'naabu', 'rustscan',
            '0', '1', '2', '3', '4', '5',
        ]

        if method in methods:
            return True

        return False

    @staticmethod
    def check_nmap():
        """
        Check if nmap is installed on the system.

        Returns:
            bool: Returns true if it is installed
        """

        if subprocess.call(f'nmap --version >nul 2>&1', shell=True) != 0:
            return False

        return True

    @staticmethod
    def check_masscan():
        """
        Check if masscan is installed on the system or bundled in the project root.

        Returns:
            bool: Returns true if it is installed
        """

        return shutil.which('masscan') is not None or os.path.exists('masscan.exe')

    @staticmethod
    def check_naabu():
        """Return True if naabu is available on PATH or in the project directory."""
        return shutil.which('naabu') is not None or os.path.exists('naabu.exe')

    @staticmethod
    def check_rustscan():
        """Return True if rustscan is available on PATH or in the project directory."""
        return shutil.which('rustscan') is not None or os.path.exists('rustscan.exe')

    @staticmethod
    def check_bore():
        """Return True if bore TCP tunnel CLI is available on PATH or in the project directory."""
        return shutil.which('bore') is not None or os.path.exists('bore.exe')

    @staticmethod
    def check_file_encoding(file):
        """
        Returns the encoding type of the file.

        Args:
            file (str): File.

        Returns:
            str: File encoding mode.
        """

        try:
            with open(file, 'r', encoding='utf8') as f:
                f.read()

            return 'utf8'

        except (UnicodeError, UnicodeDecodeError, UnicodeEncodeError, LookupError):
            return 'unicode_escape'

    @staticmethod
    def check_loop_argument(argument):
        """
        Check if the loop argument is valid.

        Args:
            argument: Loop argument.

        Returns:
            bool: Returns true if the argument is valid.
        """

        valid_arguments = ['yes', 'y', 'no', 'n']

        if argument in valid_arguments:
            return True

        return False

    @staticmethod
    def check_ip(ip_address):
        """
        Check if the ip address is valid.

        Args:
            ip_address (str): IP Address.

        Returns
            bool: Returns True if the entered ip is valid.
        """

        try:
            socket.inet_pton(socket.AF_INET, ip_address)
            return True

        except socket.error:
            return False

    @staticmethod
    def check_port(port):
        """
        Check if the entered port is valid.

        Args:
            port (str: Ports.

        Returns:
            bool: Returns true if the entered port is valid.
        """

        try:
            if 0 < int(port) <= 65535:
                return True

            return False

        except ValueError:
            return False

    @staticmethod
    def check_ip_port(ip_port):
        """
        Check if the entered IP and port are valid. (IP:PORT)

        Args:
            ip_port (str): IP Address and Port.

        Returns:
            bool: Returns true if it is valid.
        """

        if ':' in ip_port:
            ip_port = ip_port.split(':')

            if CheckUtilities.check_ip(ip_port[0]):
                if CheckUtilities.check_port(ip_port[1]):
                    try:
                        _ = ip_port[2]
                        return False

                    except IndexError:
                        return True

        return False
