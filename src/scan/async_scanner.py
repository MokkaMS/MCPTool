import asyncio
import ipaddress
import os
import socket


def parse_targets(target_spec):
    """
    Parse an IP, IP range, CIDR block, hostname, or .txt file into a list of IP strings.

    Raises:
        ValueError: If the target specification is invalid.
    """
    target_spec = str(target_spec).strip()
    if not target_spec:
        raise ValueError('Empty target')

    if target_spec.lower().endswith('.txt'):
        if not os.path.exists(target_spec):
            raise ValueError(f'File not found: {target_spec}')
        ips = []
        with open(target_spec, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ips.extend(parse_targets(line))
        if not ips:
            raise ValueError('No valid targets in file')
        return ips

    if '/' in target_spec:
        network = ipaddress.ip_network(target_spec, strict=False)
        if network.num_addresses == 1:
            return [str(network.network_address)]
        return [str(ip) for ip in network.hosts()]

    if '-' in target_spec:
        start_part, end_part = target_spec.split('-', 1)
        start_ip = ipaddress.IPv4Address(start_part.strip())

        if '.' in end_part:
            end_ip = ipaddress.IPv4Address(end_part.strip())
            if int(end_ip) < int(start_ip):
                raise ValueError('End IP precedes start IP')
            return [
                str(ipaddress.IPv4Address(addr))
                for addr in range(int(start_ip), int(end_ip) + 1)
            ]

        end_octet = int(end_part.strip())
        start_octets = str(start_ip).split('.')
        start_last = int(start_octets[3])
        if not (0 <= end_octet <= 255) or end_octet < start_last:
            raise ValueError('Invalid last-octet range')
        prefix = '.'.join(start_octets[:3])
        return [f'{prefix}.{octet}' for octet in range(start_last, end_octet + 1)]

    try:
        ipaddress.ip_address(target_spec)
        return [target_spec]
    except ValueError:
        try:
            return [socket.gethostbyname(target_spec)]
        except socket.gaierror as exc:
            raise ValueError(f'Invalid host: {target_spec}') from exc


def parse_ports(port_spec):
    """
    Parse a port, comma-separated port list, or port range (e.g. '25560-25570') into ints.

    Raises:
        ValueError: If any port or range is invalid.
    """
    port_spec = str(port_spec).strip()
    if not port_spec:
        raise ValueError('Empty port specification')

    ports = []
    seen = set()

    for part in port_spec.split(','):
        part = part.strip()
        if not part:
            raise ValueError('Empty port segment')

        if '-' in part:
            bounds = part.split('-', 1)
            start_port = int(bounds[0])
            end_port = int(bounds[1])
            if not (1 <= start_port <= 65535 and 1 <= end_port <= 65535) or end_port < start_port:
                raise ValueError(f'Invalid port range: {part}')
            for port in range(start_port, end_port + 1):
                if port not in seen:
                    seen.add(port)
                    ports.append(port)
        else:
            port = int(part)
            if not (1 <= port <= 65535):
                raise ValueError(f'Invalid port: {port}')
            if port not in seen:
                seen.add(port)
                ports.append(port)

    if not ports:
        raise ValueError('No ports specified')
    return ports


async def _probe_tcp(ip, port, semaphore, timeout):
    """Return 'ip:port' if TCP port accepts a connection within timeout, else None."""
    async with semaphore:
        writer = None
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout,
            )
            return f'{ip}:{port}'
        except (OSError, asyncio.TimeoutError):
            return None
        finally:
            if writer is not None:
                writer.close()
                if hasattr(writer, 'transport') and writer.transport is not None:
                    writer.transport.abort()


async def _scan_all(targets, ports, concurrency, timeout):
    """Probe all target/port pairs concurrently and return open 'ip:port' endpoints."""
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        asyncio.create_task(_probe_tcp(ip, port, semaphore, timeout))
        for ip in targets
        for port in ports
    ]
    results = await asyncio.gather(*tasks)
    return [endpoint for endpoint in results if endpoint is not None]


def run_async_scan(target_spec, port_spec, concurrency=200, timeout=1.2):
    """
    Run an asynchronous TCP scan across parsed targets and ports.

    Returns:
        list[str]: Open 'ip:port' endpoints.
    """
    targets = parse_targets(target_spec)
    ports = parse_ports(port_spec)
    return asyncio.run(_scan_all(targets, ports, concurrency=concurrency, timeout=timeout))
