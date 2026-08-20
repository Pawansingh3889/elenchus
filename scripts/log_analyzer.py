#!/usr/bin/env python3
"""
Log analysis tool for Elenchus.
Provides verification-first analysis of application logs with local-only dependencies.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path


def analyze_app_logs(log_lines: list[str]) -> dict:
    """
    Analyze application log lines and return structured summary.
    
    Args:
        log_lines: List of log lines to analyze
        
    Returns:
        Dictionary with analysis results
    """
    # Pattern for Elenchus app logs: LEVEL LOGGER: MESSAGE
    log_pattern = re.compile(r'^(\w+)\s+([^:]+):\s*(.*)$')
    
    stats = {
        'total_lines': len(log_lines),
        'levels': Counter(),
        'loggers': Counter(),
        'messages': Counter(),
        'errors': [],
        'warnings': [],
        'info_count': 0,
        'debug_count': 0
    }
    
    for line in log_lines:
        line = line.strip()
        if not line:
            continue
            
        match = log_pattern.match(line)
        if match:
            level, logger, message = match.groups()
            level = level.upper()
            
            stats['levels'][level] += 1
            stats['loggers'][logger] += 1
            stats['messages'][message] += 1
            
            if level == 'ERROR':
                stats['errors'].append({
                    'logger': logger,
                    'message': message,
                    'line': line
                })
            elif level == 'WARNING':
                stats['warnings'].append({
                    'logger': logger,
                    'message': message,
                    'line': line
                })
            elif level == 'INFO':
                stats['info_count'] += 1
            elif level == 'DEBUG':
                stats['debug_count'] += 1
    
    # Calculate ratios
    total = stats['total_lines']
    if total > 0:
        stats['level_ratios'] = {
            level: count / total for level, count in stats['levels'].items()
        }
        stats['logger_ratios'] = {
            logger: count / total for logger, count in stats['loggers'].items()
        }
    
    # Top items
    stats['top_loggers'] = stats['loggers'].most_common(10)
    stats['top_messages'] = stats['messages'].most_common(10)
    stats['top_levels'] = stats['levels'].most_common()
    
    return stats


def analyze_llm_ledger(ledger_path: Path) -> dict:
    """
    Analyze the LLM ledger JSONL file.
    
    Args:
        ledger_path: Path to the LLM ledger JSONL file
        
    Returns:
        Dictionary with LLM usage analysis
    """
    if not ledger_path.exists():
        return {'error': f'LLM ledger not found at {ledger_path}'}
    
    entries = []
    try:
        with open(ledger_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError as e:
                    return {
                        'error': f'Invalid JSON at line {line_num}: {e}',
                        'line_content': line[:100]
                    }
    except OSError as e:  # Specific file-related exceptions
        return {'error': f'Failed to read ledger: {e}'}
    
    if not entries:
        return {'message': 'No entries found in LLM ledger'}
    
    # Analyze entries
    stats = {
        'total_entries': len(entries),
        'tiers_used': Counter(),
        'models_used': Counter(),
        'total_input_tokens': 0,
        'total_output_tokens': 0,
        'total_cost_usd': 0.0,
        'local_vs_remote': Counter(),
        'errors': []
    }
    
    for entry in entries:
        # Extract tier info
        tier = entry.get('tier', 'unknown')
        stats['tiers_used'][tier] += 1
        
        # Extract model
        model = entry.get('model', 'unknown')
        stats['models_used'][model] += 1
        
        # Token usage
        input_tokens = entry.get('input_tokens', 0)
        output_tokens = entry.get('output_tokens', 0)
        stats['total_input_tokens'] += input_tokens
        stats['total_output_tokens'] += output_tokens
        
        # Cost
        cost = entry.get('cost_usd', 0.0)
        stats['total_cost_usd'] += cost
        
        # Local vs remote
        is_local = entry.get('local', False)
        stats['local_vs_remote']['local' if is_local else 'remote'] += 1
        
        # Errors
        if 'error' in entry:
            stats['errors'].append(entry['error'])
    
    # Calculate averages
    if stats['total_entries'] > 0:
        stats['avg_input_tokens'] = stats['total_input_tokens'] / stats['total_entries']
        stats['avg_output_tokens'] = stats['total_output_tokens'] / stats['total_entries']
        if stats['total_entries'] > 0:
            stats['avg_cost_per_entry'] = stats['total_cost_usd'] / stats['total_entries']
    
    # Top items
    stats['top_tiers'] = stats['tiers_used'].most_common()
    stats['top_models'] = stats['models_used'].most_common()
    
    return stats


def reduce_log_volume(
    log_lines: list[str], 
    keep_levels: list[str] | None = None,
    drop_patterns: list[str] | None = None,
    sample_rate: float | None = None
) -> list[str]:
    """
    Reduce log volume by filtering or sampling.
    
    Args:
        log_lines: Original log lines
        keep_levels: List of log levels to keep (e.g., ['ERROR', 'WARNING'])
        drop_patterns: List of regex patterns to drop lines matching
        sample_rate: If 0.0 < rate < 1.0, keep this fraction of lines
        
    Returns:
        Filtered log lines
    """
    if keep_levels is None:
        keep_levels = []
    if drop_patterns is None:
        drop_patterns = []
    
    filtered = []
    log_pattern = re.compile(r'^(\w+)\s+[^:]+:\s*(.*)$')
    
    for line in log_lines:
        line_stripped = line.strip()
        if not line_stripped:
            filtered.append(line)  # Keep empty lines
            continue
            
        # Check log level filter
        if keep_levels:
            match = log_pattern.match(line_stripped)
            if not match or match.group(1).upper() not in [l.upper() for l in keep_levels]:
                continue
                
        # Check drop patterns
        should_drop = False
        for pattern in drop_patterns:
            try:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    should_drop = True
                    break
            except re.error:
                # Invalid regex, skip this pattern
                continue
                
        if should_drop:
            continue
            
        # Apply sampling
        if sample_rate is not None and 0.0 < sample_rate < 1.0:
            import random
            if random.random() > sample_rate:
                continue
                
        filtered.append(line)
    
    return filtered


def main():
    """Main CLI interface for log analysis tools."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Elenchus log analysis and reduction tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Analyze application logs from stdin
  cat app.log | python log_analyzer.py --analyze-app
  
  # Analyze LLM ledger
  python log_analyzer.py --analyze-llm
  
  # Reduce log volume by keeping only errors and warnings
  cat app.log | python log_analyzer.py --reduce --keep-levels ERROR WARNING
  
  # Reduce by dropping specific noisy patterns
  cat app.log | python log_analyzer.py --reduce --drop-patterns "health check" "token usage"
        '''
    )
    
    parser.add_argument(
        '--analyze-app',
        action='store_true',
        help='Analyze application log format from stdin'
    )
    
    parser.add_argument(
        '--analyze-llm',
        action='store_true',
        help='Analyze LLM ledger at var/llm_ledger.jsonl'
    )
    
    parser.add_argument(
        '--reduce',
        action='store_true',
        help='Reduce log volume (reads from stdin, writes to stdout)'
    )
    
    parser.add_argument(
        '--keep-levels',
        nargs='+',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Log levels to keep when reducing'
    )
    
    parser.add_argument(
        '--drop-patterns',
        nargs='+',
        help='Regex patterns of log lines to drop when reducing'
    )
    
    parser.add_argument(
        '--sample-rate',
        type=float,
        help='Keep this fraction of lines (0.0-1.0) when reducing'
    )
    
    parser.add_argument(
        '--ledger-path',
        default='var/llm_ledger.jsonl',
        help='Path to LLM ledger JSONL file (default: var/llm_ledger.jsonl)'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['text', 'json'],
        default='text',
        help='Output format for analysis (default: text)'
    )
    
    args = parser.parse_args()
    
    # Handle analysis modes
    if args.analyze_app:
        log_lines = [line.rstrip('\n') for line in sys.stdin]
        if not log_lines:
            print("No input provided on stdin", file=sys.stderr)
            sys.exit(1)
            
        results = analyze_app_logs(log_lines)
        
        if args.output_format == 'json':
            print(json.dumps(results, indent=2, default=str))
        else:
            print_log_analysis(results)
            
    elif args.analyze_llm:
        ledger_path = Path(args.ledger_path)
        # If relative path, make it relative to project root
        if not ledger_path.is_absolute():
            ledger_path = Path.cwd() / ledger_path
            
        results = analyze_llm_ledger(ledger_path)
        
        if args.output_format == 'json':
            print(json.dumps(results, indent=2, default=str))
        else:
            print_llm_analysis(results)
            
    elif args.reduce:
        log_lines = [line.rstrip('\n') for line in sys.stdin]
        reduced = reduce_log_volume(
            log_lines,
            keep_levels=args.keep_levels,
            drop_patterns=args.drop_patterns,
            sample_rate=args.sample_rate
        )
        
        for line in reduced:
            print(line)
            
        # Show reduction stats to stderr
        original_count = len(log_lines)
        reduced_count = len(reduced)
        if original_count > 0:
            reduction_pct = (1 - reduced_count / original_count) * 100
            print(
                f"Reduced {original_count} lines to {reduced_count} "
                f"({reduction_pct:.1f}% reduction)",
                file=sys.stderr
            )
    else:
        parser.print_help()


def print_log_analysis(stats: dict):
    """Print log analysis in human-readable format."""
    print("=== Elenchus Application Log Analysis ===")
    print(f"Total lines: {stats['total_lines']}")
    print()
    
    print("Log Levels:")
    for level, count in stats['top_levels']:
        pct = (count / stats['total_lines']) * 100 if stats['total_lines'] > 0 else 0
        print(f"  {level:8} {count:6} ({pct:5.1f}%)")
    print()
    
    print("Top Loggers:")
    for logger, count in stats['top_loggers']:
        pct = (count / stats['total_lines']) * 100 if stats['total_lines'] > 0 else 0
        print(f"  {logger:25} {count:6} ({pct:5.1f}%)")
    print()
    
    print("Top Messages:")
    for message, count in stats['top_messages']:
        # Truncate long messages for display
        display_msg = message[:60] + "..." if len(message) > 60 else message
        pct = (count / stats['total_lines']) * 100 if stats['total_lines'] > 0 else 0
        print(f"  [{count:4}] {display_msg}")
    print()
    
    if stats['errors']:
        print(f"Errors Found: {len(stats['errors'])}")
        for error in stats['errors'][:5]:  # Show first 5 errors
            print(f"  [{error['logger']}] {error['message'][:80]}")
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more")
        print()
    
    if stats['warnings']:
        print(f"Warnings Found: {len(stats['warnings'])}")
        for warning in stats['warnings'][:5]:  # Show first 5 warnings
            print(f"  [{warning['logger']}] {warning['message'][:80]}")
        if len(stats['warnings']) > 5:
            print(f"  ... and {len(stats['warnings']) - 5} more")
        print()


def print_llm_analysis(stats: dict):
    """Print LLM ledger analysis in human-readable format."""
    if 'error' in stats:
        print(f"ERROR: {stats['error']}")
        if 'line_content' in stats:
            print(f"Line content: {stats['line_content']}")
        return
        
    if 'message' in stats:
        print(stats['message'])
        return
        
    print("=== Elenchus LLM Ledger Analysis ===")
    print(f"Total entries: {stats['total_entries']}")
    print()
    
    print("Tokens Used:")
    print(f"  Input:  {stats['total_input_tokens']:,}")
    print(f"  Output: {stats['total_output_tokens']:,}")
    print(f"  Total:  {stats['total_input_tokens'] + stats['total_output_tokens']:,}")
    print()
    
    if 'avg_input_tokens' in stats:
        print("Average per entry:")
        print(f"  Input:  {stats['avg_input_tokens']:.1f}")
        print(f"  Output: {stats['avg_output_tokens']:.1f}")
        print(f"  Total:  {stats['avg_input_tokens'] + stats['avg_output_tokens']:.1f}")
    print()
    
    print("Cost:")
    print(f"  Total: ${stats['total_cost_usd']:.4f}")
    if 'avg_cost_per_entry' in stats:
        print(f"  Per entry: ${stats['avg_cost_per_entry']:.4f}")
    print()
    
    print("Tiers Used:")
    for tier, count in stats['top_tiers']:
        pct = (count / stats['total_entries']) * 100 if stats['total_entries'] > 0 else 0
        print(f"  {tier:10} {count:6} ({pct:5.1f}%)")
    print()
    
    print("Models Used:")
    for model, count in stats['top_models']:
        pct = (count / stats['total_entries']) * 100 if stats['total_entries'] > 0 else 0
        print(f"  {model:25} {count:6} ({pct:5.1f}%)")
    print()
    
    print("Local vs Remote:")
    for location, count in stats['local_vs_remote'].items():
        pct = (count / stats['total_entries']) * 100 if stats['total_entries'] > 0 else 0
        print(f"  {location:8} {count:6} ({pct:5.1f}%)")
    print()
    
    if stats['errors']:
        print(f"Errors in ledger: {len(stats['errors'])}")
        for error in stats['errors'][:5]:
            print(f"  {error[:80]}")
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more")


if __name__ == '__main__':
    main()