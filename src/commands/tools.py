import json
import os
import re
import subprocess
import sys
import time
import requests

from src.decoration.paint import paint
from src.managers.json_manager import JsonManager
from src.updater.proxy_updater import ProxyUpdater, VELOCITY_JAR_PATH, WATERFALL_JAR_PATH
from src.utilities.check_utilities import CheckUtilities
from src.utilities.get_utilities import GetUtilities


def _run_version(cmd):
    """Run a CLI command and return its first non-empty output line, or None on failure."""
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            shell=isinstance(cmd, str),
        )
        output = (res.stdout or res.stderr or '').strip()
        if res.returncode != 0 and not output:
            return None
        for line in output.splitlines():
            line = line.strip()
            if line:
                return line
        return None
    except (OSError, subprocess.SubprocessError):
        return None


def _get_mineflayer_version():
    """Return installed mineflayer version from node_modules, or None."""
    pkg_path = os.path.join('node_modules', 'mineflayer', 'package.json')
    if not os.path.exists(pkg_path):
        return None
    try:
        with open(pkg_path, 'r', encoding='utf-8') as f:
            return json.load(f).get('version')
    except (OSError, json.JSONDecodeError):
        return None


def _parse_semver(text):
    """Extract (major, minor, patch) tuple from a version string, or None."""
    match = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', str(text or ''))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3) or 0)


def _check_online_apis(spaces):
    """Check reachability and latency of upstream APIs used by MCPTool."""
    paint(f'\n{spaces}&c&l• &b&lUpstream APIs')
    headers = {'User-Agent': 'MCPTool/4.0.5 (https://github.com/MokkaMS/MCPTool)'}
    endpoints = [
        ('api.mcstatus.io', 'https://api.mcstatus.io/v2/status/java/mc.hypixel.net'),
        ('api.mcsrvstat.us', 'https://api.mcsrvstat.us/3/mc.hypixel.net'),
        ('api.mojang.com', 'https://api.mojang.com/users/profiles/minecraft/Notch'),
        ('ip-api.com', 'http://ip-api.com/json/1.1.1.1?fields=status'),
        ('fill.papermc.io', 'https://fill.papermc.io/v3/projects/velocity'),
    ]

    for label, url in endpoints:
        started = time.monotonic()
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            elapsed_ms = int((time.monotonic() - started) * 1000)
            if resp.status_code < 400:
                paint(f'{spaces}  &a[+] &f&l{label:<18} &aOK &7(HTTP {resp.status_code}, {elapsed_ms} ms)')
            else:
                paint(f'{spaces}  &e[!] &f&l{label:<18} &eHTTP {resp.status_code} &7({elapsed_ms} ms)')
        except requests.RequestException as exc:
            paint(f'{spaces}  &c[-] &f&l{label:<18} &cUnreachable &7({type(exc).__name__})')


def tools_command(*args):
    """
    Audit installed runtimes, scanners, proxies, tunnels, and optionally upstream APIs.
    """
    spaces = GetUtilities.get_spaces()
    check_online = bool(args and args[0].lower() in ('online', 'check', 'all', '--online'))

    paint(f'\n{spaces}&c&lMCPTool Toolchain & Dependency Status')

    # --- Runtimes ---
    paint(f'\n{spaces}&c&l• &b&lRuntimes')
    py_ver = f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
    paint(f'{spaces}  &a[+] &f&lPython             &a{py_ver} &7({sys.executable})')

    node_ver = _run_version(['node', '--version'])
    if node_ver:
        paint(f'{spaces}  &a[+] &f&lNode.js            &a{node_ver}')
    else:
        paint(f'{spaces}  &c[-] &f&lNode.js            &cNot found &7(required for Mineflayer bots)')

    mf_ver = _get_mineflayer_version()
    if mf_ver:
        paint(f'{spaces}  &a[+] &f&lmineflayer         &av{mf_ver} &7(MC 1.8 - 26.1)')
    else:
        paint(f'{spaces}  &c[-] &f&lmineflayer         &cNot installed &7(run npm install)')

    java_major = ProxyUpdater._get_java_major_version()
    if java_major is not None:
        if java_major >= 21:
            paint(f'{spaces}  &a[+] &f&lJava               &aJava {java_major}')
        else:
            paint(f'{spaces}  &e[!] &f&lJava               &eJava {java_major} &7(Java 21+ recommended for Velocity)')
    else:
        paint(f'{spaces}  &e[!] &f&lJava               &eNot found &7(needed for proxies & QuboScanner)')

    # --- Scanners ---
    paint(f'\n{spaces}&c&l• &d&lScanners &7(scan <target> <ports> <method>)')
    paint(f'{spaces}  &a[+] &f&lmcscan [3]         &aBuilt-in async TCP scanner &7(no external deps)')

    if CheckUtilities.check_nmap():
        nmap_ver = _run_version(['nmap', '--version']) or 'installed'
        paint(f'{spaces}  &a[+] &f&lnmap [0]           &a{nmap_ver}')
    else:
        paint(f'{spaces}  &e[!] &f&lnmap [0]           &eNot installed')

    qubo_exists = os.path.exists('src/scan/old_qubo.jar')
    if qubo_exists and java_major is not None:
        paint(f'{spaces}  &a[+] &f&lqubo [1]           &aold_qubo.jar v0.3.5 &7(legacy Java scanner)')
    elif qubo_exists:
        paint(f'{spaces}  &e[!] &f&lqubo [1]           &eold_qubo.jar present, but Java is missing')
    else:
        paint(f'{spaces}  &e[!] &f&lqubo [1]           &eold_qubo.jar missing')

    if CheckUtilities.check_masscan():
        masscan_ver = _run_version('masscan --version') or 'installed'
        note = ' &7(requires Npcap on Windows)' if os.name == 'nt' else ''
        paint(f'{spaces}  &a[+] &f&lmasscan [2]        &a{masscan_ver}{note}')
    else:
        paint(f'{spaces}  &e[!] &f&lmasscan [2]        &eNot installed')

    if CheckUtilities.check_naabu():
        naabu_ver = _run_version(['naabu', '-version']) or 'installed'
        paint(f'{spaces}  &a[+] &f&lnaabu [4]          &a{naabu_ver}')
    else:
        paint(f'{spaces}  &7[-] &f&lnaabu [4]          &7Not installed &8(optional: github.com/projectdiscovery/naabu)')

    if CheckUtilities.check_rustscan():
        rustscan_ver = _run_version(['rustscan', '--version']) or 'installed'
        paint(f'{spaces}  &a[+] &f&lrustscan [5]       &a{rustscan_ver}')
    else:
        paint(f'{spaces}  &7[-] &f&lrustscan [5]       &7Not installed &8(optional: github.com/bee-san/RustScan)')

    # --- Proxies & Tunnels ---
    paint(f'\n{spaces}&c&l• &6&lProxies & Tunnels')
    vel_ready = os.path.exists(VELOCITY_JAR_PATH)
    paint(f'{spaces}  {"&a[+]" if vel_ready else "&e[!]"} &f&lVelocity           {"&aJAR cached" if vel_ready else "&eAuto-downloads on first use"} &7(recommended)')

    wf_ready = os.path.exists(WATERFALL_JAR_PATH)
    paint(f'{spaces}  &e[!] &f&lWaterfall          {"&7JAR cached" if wf_ready else "&7Auto-downloads on use"} &e(PaperMC EOL since Mar 2024; legacy BungeeCord only)')

    ngrok_cmd = JsonManager.get(['proxyConfig', 'ngrokCommand']) or 'ngrok'
    if CheckUtilities.check_ngrok():
        ngrok_ver = _run_version(f'{ngrok_cmd} version') or 'installed'
        parsed_ngrok = _parse_semver(ngrok_ver)
        if parsed_ngrok and parsed_ngrok < (3, 10, 0):
            paint(f'{spaces}  &e[!] &f&lngrok              &e{ngrok_ver} &7(outdated; run &a{ngrok_cmd} update&7 to avoid ERR_NGROK_121)')
        else:
            paint(f'{spaces}  &a[+] &f&lngrok              &a{ngrok_ver}')
    else:
        paint(f'{spaces}  &e[!] &f&lngrok              &eNot found')

    if CheckUtilities.check_bore():
        bore_ver = _run_version(['bore', '--version']) or 'installed'
        paint(f'{spaces}  &a[+] &f&lbore               &a{bore_ver} &7(zero-auth TCP tunnel)')
    else:
        paint(f'{spaces}  &7[-] &f&lbore               &7Not installed &8(optional: github.com/ekzhang/bore)')

    shodan_key = JsonManager.get(['shodanApiKey'])
    if shodan_key:
        paint(f'{spaces}  &a[+] &f&lShodan API Key     &aConfigured &7(in config/config.json)')
    else:
        paint(f'{spaces}  &e[!] &f&lShodan API Key     &eNot configured')

    if check_online:
        _check_online_apis(spaces)
    else:
        paint(f'\n{spaces}&7Tip: Run &atools online&7 to also test live API reachability.')
