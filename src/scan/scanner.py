import os
import re
import subprocess

from src.decoration.paint import paint
from src.managers.json_manager import JsonManager
from src.managers.log_manager import LogManager
from src.minecraft.get_minecraft_server_data import GetMinecraftServerData
from src.minecraft.show_minecraft_server import show_server
from src.scan.async_scanner import run_async_scan
from src.utilities.check_utilities import CheckUtilities
from src.utilities.get_utilities import GetUtilities


DEFAULT_SCAN_COMMANDS = {
    'nmap': 'nmap -p [1] -n -T5 -Pn -vvv -sS [0]',
    'quboscanner': 'cd ./src/scan && java -Dfile.encoding=UTF-8 -jar old_qubo.jar -range [0] -ports [1] -th 500 -ti 2000',
    'masscan': 'masscan -p [1] [0]',
    'naabu': 'naabu -host [0] -p [1] -silent',
    'rustscan': 'rustscan -a [0] -p [1] --greppable',
}


class Scanner:
    @staticmethod
    def _record_server(server, log_file):
        """Query a candidate ip:port as a Minecraft server, display it, and log if valid."""
        server_data = GetMinecraftServerData.get_data(server)
        if server_data is None:
            return 0

        show_server(server_data)
        if JsonManager.get('logs'):
            log_data = list(server_data.values())
            LogManager.write_log(log_file, 'scan', log_data)
        return 1

    @staticmethod
    def _run_mcscan(target, port_range, log_file, show_output):
        """Run the built-in asynchronous Python TCP scanner and verify Minecraft servers."""
        try:
            endpoints = run_async_scan(target, port_range)
        except ValueError as exc:
            msg = str(exc).lower()
            if 'port' in msg:
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "invalidArguments", "invalidPorts"]).replace("[0]", port_range)}')
            else:
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "invalidArguments", "invalidIP"]).replace("[0]", target)}')
            return None

        servers_found = 0
        for endpoint in endpoints:
            if show_output:
                print(f'Open port: {endpoint}')
            servers_found += Scanner._record_server(endpoint, log_file)
        return servers_found

    @staticmethod
    def scanner(target, port_range, scan_method):
        """
        Scan target ports using the configured scanner method and check for Minecraft servers.
        """
        log_file = LogManager.create_log_file('scan')
        show_output = bool(JsonManager.get(["scannerOptions", "showScanOutput"]))

        if scan_method == 'mcscan':
            try:
                return Scanner._run_mcscan(target, port_range, log_file, show_output)
            except KeyboardInterrupt:
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["commands", "ctrlC"])}')
                return 0

        # Prepare the scan command.
        command = Scanner.get_command(scan_method)
        if scan_method == 'naabu' and target.lower().endswith('.txt'):
            command = command.replace('-host [0]', '-l [0]')
        if scan_method == 'rustscan' and '-' in port_range and ',' not in port_range:
            command = command.replace('-p [1]', '-r [1]')

        command = command.replace('[0]', target).replace('[1]', port_range)
        servers_found = 0
        first_line = True

        # Add sudo before the command if necessary.
        if os.name != 'nt' and scan_method not in ('quboscanner', 'naabu', 'rustscan') and not CheckUtilities.check_termux():
            command = f'sudo {command}'

        try:
            # Start scan.
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            text_to_search, pattern, invalid_ip_text, invalid_ports_text = Scanner.get_scan_params(scan_method)

            # Review each line of the process output.
            for line in process.stdout:
                output_line = line.decode('latin-1').strip()

                if first_line:
                    if scan_method == 'quboscanner':
                        if 'not found' in output_line or '"java"' in output_line:
                            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "scan", "javaNotInstalled"])}')
                            return

                    first_line = False

                if show_output:
                    print(output_line)

                # If the line that refers to the IP entered as invalid.
                if any(text in output_line for text in invalid_ip_text):
                    paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "invalidArguments", "invalidIP"]).replace("[0]", target)}')
                    return

                # If the line that refers to the port range not being valid.
                if any(text in output_line for text in invalid_ports_text):
                    paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "invalidArguments", "invalidPorts"]).replace("[0]", port_range)}')
                    return

                # If the line contains an ip and a port.
                if text_to_search == '' or text_to_search in output_line:
                    for server in Scanner.extract_servers(output_line, pattern, scan_method):
                        servers_found += Scanner._record_server(server, log_file)

            process.wait()
            return servers_found

        except (KeyboardInterrupt, ValueError):
            try:
                process.terminate()

            except UnboundLocalError:
                pass

            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["commands", "ctrlC"])}')
            return servers_found

    @staticmethod
    def get_command(scan_method):
        return JsonManager.get(['scannerOptions', f'{scan_method}Command']) or DEFAULT_SCAN_COMMANDS.get(scan_method, '')

    @staticmethod
    def get_scan_params(scan_method):
        scan_params = {
            'nmap': ('Discovered open port', r'open port (\d+)/\w+ on (\d+\.\d+\.\d+\.\d+)', ['Failed to resolve "'], ['Your port specifications are illegal.', 'Your port range']),
            'masscan': ('Discovered open port', r'open port (\d+)/\w+ on (\d+\.\d+\.\d+\.\d+)', ['ERROR: bad IP address/range:', 'unknown command-line parameter'], ['bad target port:']),
            'quboscanner': (')(', r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b', ['Invalid IP range.'], ['port is out of range', 'For input string:']),
            'naabu': ('', r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b', ['Could not resolve host', 'invalid target'], ['invalid port', 'port out of range']),
            'rustscan': ('', r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b', ['Failed to resolve', 'Invalid IP'], ['Invalid port', 'Invalid range']),
        }

        return scan_params.get(scan_method, ('', '', [], []))

    @staticmethod
    def extract_server_info(output_line, pattern, scan_method):
        match = re.search(pattern, output_line)

        if match:
            if scan_method in ('nmap', 'masscan'):
                server = f'{match.group(2)}:{match.group(1)}'

            else:
                server = match.group(0)

            return server

    @staticmethod
    def extract_servers(output_line, pattern, scan_method):
        """Extract one or more ip:port strings from a scanner output line."""
        if scan_method == 'rustscan' and '->' in output_line:
            arrow_match = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})\s*->\s*\[([0-9,\s]+)\]', output_line)
            if arrow_match:
                ip = arrow_match.group(1)
                ports = [p.strip() for p in arrow_match.group(2).split(',') if p.strip().isdigit()]
                return [f'{ip}:{port}' for port in ports]

        server = Scanner.extract_server_info(output_line, pattern, scan_method)
        return [server] if server else []
