#!/usr/bin/env python3
"""
Hardware analysis tool for Elenchus.
Provides verification-first analysis of system hardware using trusted CLI tools.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone


def run_command(cmd: list[str], sudo: bool = False) -> tuple[bool, str, str]:
    """
    Run a command and return success, stdout, stderr.
    
    Args:
        cmd: Command and arguments as list
        sudo: Whether to run with sudo (for privileged commands)
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    if sudo:
        cmd = ['sudo'] + cmd
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        return (result.returncode == 0, result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        return (False, '', 'Command timed out')
    except OSError as e:  # Specific exceptions like FileNotFoundError for missing commands
        return (False, '', str(e))


def get_cpu_info() -> dict:
    """Get CPU information using lscpu."""
    success, stdout, stderr = run_command(['lscpu'])
    if not success:
        return {'error': f'lscpu failed: {stderr}'}
    
    info = {}
    for line in stdout.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    
    return info


def get_memory_info() -> dict:
    """Get memory information using lsmem and free."""
    info = {}
    
    # Try lsmem first
    success, stdout, stderr = run_command(['lsmem'])
    if success:
        info['lsmem'] = {}
        for line in stdout.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info['lsmem'][key.strip()] = value.strip()
    else:
        info['lsmem_error'] = f'lsmem failed: {stderr}'
    
    # Get free memory info
    success, stdout, stderr = run_command(['free', '-h'])
    if success:
        info['free'] = {}
        lines = stdout.split('\n')
        if len(lines) >= 2:
            headers = lines[0].split()
            values = lines[1].split()
            for i, header in enumerate(headers):
                if i < len(values):
                    info['free'][header] = values[i]
    else:
        info['free_error'] = f'free failed: {stderr}'
    
    return info


def get_storage_info() -> dict:
    """Get storage information using lsblk and df."""
    info = {}
    
    # lsblk
    success, stdout, stderr = run_command(['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,MODEL'])
    if success:
        info['lsblk'] = stdout
    else:
        info['lsblk_error'] = f'lsblk failed: {stderr}'
    
    # df
    success, stdout, stderr = run_command(['df', '-h'])
    if success:
        info['df'] = stdout
    else:
        info['df_error'] = f'df failed: {stderr}'
    
    return info


def get_pci_info() -> dict:
    """Get PCI information using lspci."""
    success, stdout, stderr = run_command(['lspci'])
    if not success:
        return {'error': f'lspci failed: {stderr}'}
    
    devices = []
    for line in stdout.split('\n'):
        if line.strip():
            devices.append(line.strip())
    
    return {'devices': devices, 'count': len(devices)}


def get_usb_info() -> dict:
    """Get USB information using lsusb."""
    success, stdout, stderr = run_command(['lsusb'])
    if not success:
        return {'error': f'lsusb failed: {stderr}'}
    
    devices = []
    for line in stdout.split('\n'):
        if line.strip():
            devices.append(line.strip())
    
    return {'devices': devices, 'count': len(devices)}


def get_system_info() -> dict:
    """Get system information using uname and uptime."""
    info = {}
    
    # uname
    success, stdout, stderr = run_command(['uname', '-a'])
    if success:
        info['uname'] = stdout.strip()
    else:
        info['uname_error'] = f'uname failed: {stderr}'
    
    # uptime
    success, stdout, stderr = run_command(['uptime'])
    if success:
        info['uptime'] = stdout.strip()
    else:
        info['uptime_error'] = f'uptime failed: {stderr}'
    
    return info


def analyze_hardware() -> dict:
    """
    Run all hardware analysis functions and return combined results.
    
    Returns:
        Dictionary with all hardware information
    """
    results = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'cpu': get_cpu_info(),
        'memory': get_memory_info(),
        'storage': get_storage_info(),
        'pci': get_pci_info(),
        'usb': get_usb_info(),
        'system': get_system_info()
    }
    
    return results


def reduce_hardware_output(
    full_data: dict,
    sections: list[str] | None = None,
    max_items: dict[str, int] | None = None
) -> dict:
    """
    Reduce hardware output by selecting sections or limiting items.
    
    Args:
        full_data: Full hardware data from analyze_hardware()
        sections: List of sections to keep (e.g., ['cpu', 'memory'])
        max_items: Dict mapping section names to maximum number of items to keep
        
    Returns:
        Reduced hardware data
    """
    if sections is None:
        sections = list(full_data.keys())
    
    reduced = {'timestamp': full_data.get('timestamp')}
    
    for section in sections:
        if section in full_data:
            reduced[section] = full_data[section]
    
    # Apply item limits if specified
    if max_items:
        for section, limit in max_items.items():
            if section in reduced and isinstance(reduced[section], list) and len(reduced[section]) > limit:
                reduced[section] = reduced[section][:limit]
                reduced[section].append(f'... and {len(full_data[section]) - limit} more items')
    
    return reduced


def main():
    """Main CLI interface for hardware analysis tools."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Elenchus hardware analysis tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Full hardware analysis
  python hardware_analyzer.py --analyze
  
  # Only CPU and memory info
  python hardware_analyzer.py --analyze --sections cpu memory
  
  # Limit PCI devices to top 10
  python hardware_analyzer.py --analyze --max-items pci:10
  
  # Output as JSON for further processing
  python hardware_analyzer.py --analyze --output-format json
        '''
    )
    
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze system hardware'
    )
    
    parser.add_argument(
        '--sections',
        nargs='+',
        choices=['cpu', 'memory', 'storage', 'pci', 'usb', 'system'],
        help='Specific sections to analyze (default: all)'
    )
    
    parser.add_argument(
        '--max-items',
        nargs='+',
        help='Limit items in sections (format: section:count, e.g. pci:10 usb:5)'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--reduce',
        action='store_true',
        help='Apply reduction based on --sections and --max-items'
    )
    
    args = parser.parse_args()
    
    if not args.analyze:
        parser.print_help()
        return
    
    # Parse max-items
    max_items = {}
    if args.max_items:
        for item in args.max_items:
            if ':' in item:
                section, count = item.split(':', 1)
                try:
                    max_items[section] = int(count)
                except ValueError:
                    print(f"Invalid count for section {section}: {count}", file=sys.stderr)
                    sys.exit(1)
            else:
                print(f"Invalid max-items format: {item} (expected section:count)", file=sys.stderr)
                sys.exit(1)
    
    # Get full hardware data
    full_data = analyze_hardware()
    
    # Apply reduction if requested
    if args.reduce or args.sections or args.max_items:
        sections = args.sections if args.sections else None
        data = reduce_hardware_output(full_data, sections=sections, max_items=max_items)
    else:
        data = full_data
    
    # Output
    if args.output_format == 'json':
        print(json.dumps(data, indent=2, default=str))
    else:
        print_hardware_analysis(data)


def print_hardware_analysis(data: dict):
    """Print hardware analysis in human-readable format."""
    print("=== Elenchus Hardware Analysis ===")
    print(f"Timestamp: {data.get('timestamp', 'Unknown')}")
    print()
    
    # CPU
    if 'cpu' in data:
        print("=== CPU Information ===")
        cpu = data['cpu']
        if 'error' in cpu:
            print(f"ERROR: {cpu['error']}")
        else:
            # Show key CPU info
            key_fields = ['Architecture', 'Model name', 'CPU(s)', 'Thread(s) per core', 
                         'Core(s) per socket', 'Socket(s)', 'L1d cache', 'L1i cache', 
                         'L2 cache', 'L3 cache']
            for field in key_fields:
                if field in cpu:
                    print(f"{field:25}: {cpu[field]}")
        print()
    
    # Memory
    if 'memory' in data:
        print("=== Memory Information ===")
        mem = data['memory']
        if 'lsmem_error' in mem:
            print(f"lsmem: {mem['lsmem_error']}")
        elif 'lsmem' in mem:
            print("LSMEM:")
            for k, v in list(mem['lsmem'].items())[:10]:  # Limit output
                print(f"  {k:20}: {v}")
            if len(mem['lsmem']) > 10:
                print(f"  ... and {len(mem['lsmem']) - 10} more lines")
        
        if 'free_error' in mem:
            print(f"free: {mem['free_error']}")
        elif 'free' in mem:
            print("FREE:")
            for k, v in mem['free'].items():
                print(f"  {k:10}: {v}")
        print()
    
    # Storage
    if 'storage' in data:
        print("=== Storage Information ===")
        stor = data['storage']
        if 'lsblk_error' in stor:
            print(f"lsblk: {stor['lsblk_error']}")
        else:
            print("LSLBK (first 20 lines):")
            lines = stor['lsblk'].split('\n')[:20]
            for line in lines:
                print(f"  {line}")
            if len(stor['lsblk'].split('\n')) > 20:
                total_lines = len(stor['lsblk'].split('\n'))
                remaining = total_lines - 20
                print(f"  ... and {remaining} more lines")
        
        if 'df_error' in stor:
            print(f"df: {stor['df_error']}")
        else:
            print("DF (first 10 lines):")
            lines = stor['df'].split('\n')[:10]
            for line in lines:
                print(f"  {line}")
            if len(stor['df'].split('\n')) > 10:
                total_lines = len(stor['df'].split('\n'))
                remaining = total_lines - 10
                print(f"  ... and {remaining} more lines")
        print()
    
    # PCI
    if 'pci' in data:
        print("=== PCI Devices ===")
        pci = data['pci']
        if 'error' in pci:
            print(f"ERROR: {pci['error']}")
        else:
            print(f"Found {pci['count']} PCI devices:")
            for device in pci['devices'][:15]:  # Show first 15
                print(f"  {device}")
            if len(pci['devices']) > 15:
                remaining = len(pci['devices']) - 15
                print(f"  ... and {remaining} more devices")
        print()
    
    # USB
    if 'usb' in data:
        print("=== USB Devices ===")
        usb = data['usb']
        if 'error' in usb:
            print(f"ERROR: {usb['error']}")
        else:
            print(f"Found {usb['count']} USB devices:")
            for device in usb['devices'][:15]:  # Show first 15
                print(f"  {device}")
            if len(usb['devices']) > 15:
                remaining = len(usb['devices']) - 15
                print(f"  ... and {remaining} more devices")
        print()
    
    # System
    if 'system' in data:
        print("=== System Information ===")
        sysinfo = data['system']
        if 'uname_error' in sysinfo:
            print(f"uname: {sysinfo['uname_error']}")
        else:
            print(f"UNAME: {sysinfo.get('uname', 'Unknown')}")
        
        if 'uptime_error' in sysinfo:
            print(f"uptime: {sysinfo['uptime_error']}")
        else:
            print(f"UPTIME: {sysinfo.get('uptime', 'Unknown')}")
        print()


if __name__ == '__main__':
    main()