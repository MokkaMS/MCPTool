from src.decoration.paint import paint
from src.utilities.argument_checker import ArgumentChecker
from src.utilities.check_utilities import CheckUtilities
from src.utilities.get_utilities import GetUtilities


CATEGORIES = [
    ('information', '&b&lInformation', ['server', 'uuid', 'ipinfo', 'dnslookup']),
    ('discovery', '&d&lDiscovery & Scanning', ['shodan', 'websearch', 'subdomains', 'scan', 'listening', 'playerlogs']),
    ('attack', '&4&lAttack & Spoofing', ['fakeproxy', 'login', 'pinlogin', 'sendcmd', 'kick', 'kickall', 'rconbrute']),
    ('utilities', '&6&lUtilities & Proxies', ['checker', 'waterfall', 'velocity', 'connect', 'rcon']),
    ('general', '&a&lGeneral', ['help', 'tools', 'clear', 'language', 'discord', 'exit']),
]

ALIASES = {
    'cls': 'clear',
    'dc': 'discord',
    'lang': 'language',
    'quit': 'exit',
}

CATEGORY_ALIASES = {
    'info': 'information',
    'information': 'information',
    'discovery': 'discovery',
    'scan': 'discovery',
    'scanning': 'discovery',
    'attack': 'attack',
    'spoof': 'attack',
    'spoofing': 'attack',
    'util': 'utilities',
    'utils': 'utilities',
    'utility': 'utilities',
    'utilities': 'utilities',
    'proxy': 'utilities',
    'proxies': 'utilities',
    'general': 'general',
    'system': 'general',
}

COMMAND_DOCS = {
    'server': {
        'shortcut': '01',
        'summary': 'Inspect a Java or Bedrock Minecraft server (MOTD, version, players, plugins/mods).',
        'notes': [
            'Supports IP:port (e.g. 127.0.0.1:25565) or domain (e.g. play.example.net).',
            'Uses the API configured in config/config.json (mcstatus.io, mcsrvstat.us, or localhost).',
        ],
        'examples': ['server play.example.net', 'server 127.0.0.1:25565'],
    },
    'uuid': {
        'shortcut': '02',
        'summary': 'Look up online (Mojang) and offline (cracked) UUIDs for a username.',
        'notes': ['Computes both the premium Mojang UUID (if registered) and offline MD5 UUID.'],
        'examples': ['uuid Notch'],
    },
    'ipinfo': {
        'shortcut': '03',
        'summary': 'Get geolocation, ISP, ASN, and reverse DNS details for an IP address.',
        'notes': ['Requires a valid IPv4 address.'],
        'examples': ['ipinfo 1.1.1.1'],
    },
    'dnslookup': {
        'shortcut': '04',
        'summary': 'Query DNS records (A, AAAA, MX, NS, TXT, CNAME, SRV) for a domain.',
        'notes': ['Useful for uncovering backend IPs or Minecraft SRV records (_minecraft._tcp).'],
        'examples': ['dnslookup example.com'],
    },
    'shodan': {
        'shortcut': '05',
        'summary': 'Search Shodan for Minecraft servers matching query terms.',
        'notes': [
            'Requires a valid shodanApiKey in config/config.json.',
            'Separate multiple queries with --- (e.g. shodan spigot 1.20 --- paper 1.21).',
        ],
        'examples': ['shodan Minecraft 1.20.4', 'shodan spigot 1.8.8 --- paper 1.21'],
    },
    'websearch': {
        'shortcut': '06',
        'summary': 'Scrape public Minecraft server lists for servers matching a tag.',
        'notes': ['Automatically checks discovered servers and logs results.'],
        'examples': ['websearch survival'],
    },
    'subdomains': {
        'shortcut': '07',
        'summary': 'Brute-force subdomains of a domain using a wordlist file.',
        'notes': ['Resolves matching subdomains and displays their IP addresses.'],
        'examples': ['subdomains example.com files/subdomains.txt'],
    },
    'scan': {
        'shortcut': '08',
        'summary': 'Scan an IP, IP range, CIDR, or file of IPs for open Minecraft servers.',
        'notes': [
            'Methods: nmap (0), qubo (1), masscan (2), mcscan / async (3), naabu (4), rustscan (5).',
            'mcscan (3) is built in (pure Python asyncio) and needs no Java, Nmap, or Npcap.',
            'qubo requires Java; nmap requires Nmap; naabu/rustscan require their binaries on PATH.',
            'Target can be an IP, range (127.0.0.1-255), CIDR (192.168.1.0/24 in mcscan), or .txt file.',
        ],
        'examples': ['scan 127.0.0.1 25560-25570 3', 'scan 192.168.1.1-254 25565 mcscan'],
    },
    'listening': {
        'shortcut': '09',
        'summary': 'Poll a server to capture the current online player list and UUIDs.',
        'notes': ['Continuously monitors the target until stopped with Ctrl+C.'],
        'examples': ['listening play.example.net'],
    },
    'playerlogs': {
        'shortcut': '10',
        'summary': 'Monitor and log player join/leave timestamps and UUIDs on a server.',
        'notes': ['Logs sessions to the logs/ directory until stopped with Ctrl+C.'],
        'examples': ['playerlogs 127.0.0.1:25565'],
    },
    'fakeproxy': {
        'shortcut': '12',
        'summary': 'Launch a Velocity fake proxy that clones server info and captures traffic.',
        'notes': [
            'Requires Java 21+ (and optionally Ngrok for public tunneling).',
            'Forwarding modes: none, legacy, bungeeguard, modern.',
            'Captures player logins, IPs, chat messages, and commands.',
        ],
        'examples': ['fakeproxy 127.0.0.1:25565 modern', 'fakeproxy play.example.net none'],
    },
    'login': {
        'shortcut': '13',
        'summary': 'Brute-force /login authentication on an offline-mode server with a bot.',
        'notes': [
            'Requires Node.js + Mineflayer dependencies.',
            'Specify a Minecraft version (e.g. 1.20.4) and a password wordlist file.',
        ],
        'examples': ['login 127.0.0.1:25565 Steve 1.20.4 files/passwords.txt'],
    },
    'pinlogin': {
        'shortcut': '14',
        'summary': 'Brute-force PIN/title-based login plugins (e.g. AdvancedLogin) with a bot.',
        'notes': ['Requires Node.js + Mineflayer dependencies.'],
        'examples': ['pinlogin 127.0.0.1:25565 Steve 1.20.4 files/pins.txt'],
    },
    'sendcmd': {
        'shortcut': '15',
        'summary': 'Connect a bot that sends commands or chat messages from a file.',
        'notes': [
            'Requires Node.js + Mineflayer dependencies.',
            'Loop argument: y (repeat continuously) or n (run once).',
        ],
        'examples': ['sendcmd 127.0.0.1:25565 BotName 1.20.4 cmds.txt n'],
    },
    'kick': {
        'shortcut': '16',
        'summary': 'Kick a player on offline-mode servers by logging in with their username.',
        'notes': [
            'Requires Node.js + Mineflayer dependencies.',
            'Loop argument: y (keep rejoining to keep kicked) or n (single kick).',
        ],
        'examples': ['kick 127.0.0.1:25565 TargetUser 1.20.4 n'],
    },
    'kickall': {
        'shortcut': '17',
        'summary': 'Kick all currently online players on an offline-mode server.',
        'notes': [
            'Queries online players and spawns bots to disconnect each one.',
            'Loop argument: y or n.',
        ],
        'examples': ['kickall 127.0.0.1:25565 1.20.4 n'],
    },
    'rconbrute': {
        'shortcut': '18',
        'summary': 'Brute-force the RCON password of a Minecraft server.',
        'notes': ['Target must include the RCON port (default Minecraft RCON port is 25575).'],
        'examples': ['rconbrute 127.0.0.1:25575 files/passwords.txt'],
    },
    'checker': {
        'shortcut': '19',
        'summary': 'Check and summarize status/players/versions for servers listed in a file.',
        'notes': ['Reads one server (IP:port or domain) per line from the input file.'],
        'examples': ['checker servers.txt'],
    },
    'waterfall': {
        'shortcut': '20',
        'summary': 'Start a local Waterfall (BungeeCord) proxy pointing to a target server.',
        'notes': [
            'Requires Java 21+. Includes built-in proxy exploit/spoofing plugins.',
            'Note: PaperMC marked Waterfall End-of-Life (Mar 2024); prefer velocity for new setups.',
        ],
        'examples': ['waterfall 127.0.0.1:25565'],
    },
    'velocity': {
        'shortcut': '21',
        'summary': 'Start a local Velocity proxy pointing to a target server.',
        'notes': [
            'Requires Java 21+ (Java 25+ for Velocity 4.x; Velocity 3.x runs on Java 21).',
            'Forwarding modes: none, legacy, bungeeguard, modern.',
        ],
        'examples': ['velocity 127.0.0.1:25565 modern'],
    },
    'connect': {
        'shortcut': '22',
        'summary': 'Join a Minecraft server directly from the terminal as a Mineflayer bot.',
        'notes': ['Requires Node.js + Mineflayer dependencies.'],
        'examples': ['connect 127.0.0.1:25565 MyBot 1.20.4'],
    },
    'rcon': {
        'shortcut': '23',
        'summary': 'Open an interactive RCON console to run server commands remotely.',
        'notes': ['Requires RCON enabled on the target server and the RCON password.'],
        'examples': ['rcon 127.0.0.1:25575 mySecretPass'],
    },
    'help': {
        'shortcut': '00',
        'args': ['command?'],
        'summary': 'Show all commands, or detailed usage and examples for a specific command.',
        'notes': [
            'Pass a command name (e.g. help scan), shortcut number (e.g. help 08),',
            'or category (info, discovery, attack, utilities, general).',
        ],
        'examples': ['help', 'help scan', 'help 12', 'help attack'],
    },
    'tools': {
        'shortcut': '24',
        'args': ['online?'],
        'summary': 'Check tool versions, scanner readiness, and optional live API health.',
        'notes': [
            'Audits Python, Node.js, Mineflayer, Java, scanners (mcscan/nmap/qubo/masscan/naabu/rustscan),',
            'proxies, ngrok/bore, and Shodan config. Pass "online" to test live API reachability.',
        ],
        'examples': ['tools', 'tools online'],
    },
    'clear': {
        'aliases': ['cls'],
        'summary': 'Clear the terminal screen and redraw the main menu banner.',
        'notes': ['Alias: cls'],
        'examples': ['clear', 'cls'],
    },
    'language': {
        'aliases': ['lang'],
        'summary': 'Switch the interface language (saved to config/config.json).',
        'notes': [
            'Alias: lang',
            'Available languages: en, es, de, fr, pt, cat, sk, tr.',
        ],
        'examples': ['language en', 'lang es'],
    },
    'discord': {
        'aliases': ['dc'],
        'summary': 'Show the official MCPTool Discord server link.',
        'notes': ['Alias: dc'],
        'examples': ['discord'],
    },
    'exit': {
        'aliases': ['quit'],
        'summary': 'Stop background services and exit MCPTool cleanly.',
        'notes': ['Alias: quit (Ctrl+C also exits cleanly).'],
        'examples': ['exit', 'quit'],
    },
}


def _format_args(command_name):
    """Return formatted argument placeholders for command_name."""
    spec = COMMAND_DOCS.get(command_name, {})
    args = spec.get('args')
    if args is None:
        args = ArgumentChecker.get_command_arguments(command_name)
    if not args:
        return ''
    return ' '.join(f'<{arg}>' for arg in args)


def _resolve_command(query):
    """Resolve a command name, alias, or numeric shortcut to its canonical command name."""
    key = query.strip().lower()
    if key in COMMAND_DOCS:
        return key
    if key in ALIASES:
        return ALIASES[key]

    indexes = ArgumentChecker.get_command_indexes()
    if key.isdigit():
        padded = key.zfill(2)
        if padded in indexes:
            return indexes[padded]
    return None


def _print_category(label, command_names, compact=False):
    """Print one help category block with command syntax and one-line summaries."""
    spaces = GetUtilities.get_spaces()
    paint(f'\n{spaces}&c&l• {label}')

    for cmd in command_names:
        spec = COMMAND_DOCS[cmd]
        shortcut = spec.get('shortcut')
        aliases = spec.get('aliases')

        tag_parts = []
        if shortcut:
            tag_parts.append(shortcut)
        if aliases:
            tag_parts.extend(aliases)
        tag = f' &8[&7{"/".join(tag_parts)}&8]' if tag_parts else ''

        args_str = _format_args(cmd)
        usage = f'&f&l{cmd}' + (f' &7{args_str}' if args_str else '')

        if compact:
            paint(f'{spaces}  &6> {usage}{tag}')
            paint(f'{spaces}    &7{spec["summary"]}')
        else:
            syntax_plain = cmd + (f' {args_str}' if args_str else '')
            tag_plain = f' [{"/".join(tag_parts)}]' if tag_parts else ''
            used_width = len(syntax_plain) + len(tag_plain)
            col_width = 42
            if used_width <= col_width - 2:
                pad = col_width - used_width
                paint(f'{spaces}  &6> {usage}{tag}{" " * pad}&7{spec["summary"]}')
            else:
                paint(f'{spaces}  &6> {usage}{tag}')
                paint(f'{spaces}      &7{spec["summary"]}')


def _print_command_detail(command_name):
    """Print detailed help for a single command."""
    spaces = GetUtilities.get_spaces()
    spec = COMMAND_DOCS[command_name]
    args_str = _format_args(command_name)
    usage = f'{command_name} {args_str}'.strip()

    aliases = []
    if spec.get('shortcut'):
        aliases.append(f'shortcut: {spec["shortcut"]}')
    if spec.get('aliases'):
        aliases.append(f'aliases: {", ".join(spec["aliases"])}')
    meta = f' &8(&7{"; ".join(aliases)}&8)' if aliases else ''

    paint(f'\n{spaces}&c&l• &b&l{command_name.upper()}{meta}')
    paint(f'{spaces}  &f&l{spec["summary"]}')
    paint(f'\n{spaces}  &6&lUsage: &a{usage}')

    notes = spec.get('notes', [])
    if notes:
        paint(f'\n{spaces}  &6&lDetails:')
        for note in notes:
            paint(f'{spaces}    &7- {note}')

    examples = spec.get('examples', [])
    if examples:
        paint(f'\n{spaces}  &6&lExamples:')
        for example in examples:
            paint(f'{spaces}    &f&l> &a{example}')


def help_command(*args):
    """
    Display categorized command help, or detailed usage for a specific command/category.
    """
    spaces = GetUtilities.get_spaces()
    compact = CheckUtilities.check_termux()

    if args:
        query = args[0].strip().lower()
        resolved_cmd = _resolve_command(query)
        if resolved_cmd:
            _print_command_detail(resolved_cmd)
            return

        if query in CATEGORY_ALIASES:
            target_cat = CATEGORY_ALIASES[query]
            for cat_id, cat_label, cat_cmds in CATEGORIES:
                if cat_id == target_cat:
                    _print_category(cat_label, cat_cmds, compact=compact)
                    paint(f'\n{spaces}&7Tip: Run &ahelp <command>&7 for detailed usage and examples.')
                    return

        paint(f'\n{spaces}{GetUtilities.get_translated_text(["prefix"])}&cUnknown command or category: &f&l{args[0]}')
        paint(f'{spaces}{GetUtilities.get_translated_text(["prefix"])}&7Run &ahelp&7 to see all available commands.')
        return

    paint(f'\n{spaces}&c&lMCPTool Command Reference &8(&7use &ahelp <command>&7 for details & examples&8)')

    for _, cat_label, cat_cmds in CATEGORIES:
        _print_category(cat_label, cat_cmds, compact=compact)

    paint(f'\n{spaces}&7Shortcuts: Enter a command name or its 2-digit number (e.g. &a08&7 = &ascan&7).')
    paint(f'{spaces}&7Filter by category: &ahelp info&7, &ahelp discovery&7, &ahelp attack&7, &ahelp utilities&7, &ahelp general')
    guide_msg = GetUtilities.get_translated_text(['commands', 'help', 'message'])
    if guide_msg:
        paint(f'{spaces}{guide_msg}')
