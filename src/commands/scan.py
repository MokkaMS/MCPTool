from src.scan.scanner import Scanner
from src.decoration.paint import paint
from src.utilities.get_utilities import GetUtilities
from src.utilities.check_utilities import CheckUtilities


def scan_command(target, port_range, scan_method, *args):
    """
    Scan the specified ports of an IP address (which can also be an IP range)
    and check if there are Minecraft servers hosted on those ports.

    Args:
        target (str): IP Address, CIDR, range, or filename containing IP addresses.
        port_range (str): Port range (e.g., "25560-25570").
        scan_method (str): The scanner to use (nmap/0, qubo/1, masscan/2, mcscan/3, naabu/4, rustscan/5).
        *args: Additional arguments.
    """

    try:
        if not CheckUtilities.check_scan_method(scan_method):
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "invalidArguments", "invalidScanMethod"])}')
            return

        scan_method = GetUtilities.get_scan_method(scan_method)

        if scan_method == 'nmap' and CheckUtilities.check_nmap() is False:
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "scan", "nmapNotInstalled"])}')
            return

        if scan_method == 'masscan' and CheckUtilities.check_masscan() is False:
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "scan", "masscanNotInstalled"])}')
            return

        if scan_method == 'naabu' and CheckUtilities.check_naabu() is False:
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}&f&lYou must install &anaabu &f&l(github.com/projectdiscovery/naabu) to use this method!')
            return

        if scan_method == 'rustscan' and CheckUtilities.check_rustscan() is False:
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}&f&lYou must install &arustscan &f&l(github.com/bee-san/RustScan) to use this method!')
            return

        if target.endswith('.txt'):
            # Check if the target is a text file with a list of IP addresses.
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "scan", "scanningIpRange"]).replace("[0]", target)}')

        else:
            # Display a message when scanning a single IP address.
            paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "scan", "scanningIpAddress"]).replace("[0]", target)}')

        # Perform the scanning operation using the specified scanner.
        servers_found = Scanner.scanner(target, port_range, scan_method)

        if servers_found is not None:
            if servers_found >= 1:
                # Display the number of Minecraft servers found.
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "scan", "scanFinished"]).replace("[0]", str(servers_found))}')

            else:
                # Display a message when no Minecraft servers are found.
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", "scan", "noPortsFound"])}')

    except KeyboardInterrupt:
        paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["commands", "ctrlC"])}')
