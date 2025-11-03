#!/usr/bin/env python3
"""
Performance benchmark for ZeroLog Viewer optimizations.
Tests file parsing and search performance.
"""

import json
import time
import tempfile
import os
from datetime import datetime, timedelta


def generate_test_logs(count: int) -> list:
    """Generate test log entries."""
    logs = []
    base_time = datetime(2025, 10, 20, 17, 19, 16)
    
    levels = ['debug', 'info', 'warn', 'error', 'fatal']
    messages = [
        'Device found',
        'Connection established',
        'Processing request',
        'Database query executed',
        'Failed to authenticate',
        'Request completed',
        'Cache miss',
        'Configuration loaded'
    ]
    
    for i in range(count):
        log = {
            'level': levels[i % len(levels)],
            'time': (base_time + timedelta(seconds=i)).isoformat() + 'Z',
            'message': messages[i % len(messages)],
            'serialNumber': f'{910335 + i}',
            'organizationID': '67e59f3d11d57bb940742d07',
            'deviceID': f'68cd61eaadba4ed22ccdc{i:03d}',
            'duration': (i % 10) + 0.5,
            'git_revision': 'v0.9.0-3f5b689'
        }
        logs.append(log)
    
    return logs


def benchmark_file_parsing(log_count: int):
    """Benchmark file parsing performance."""
    print(f"\n=== Benchmarking file parsing with {log_count:,} logs ===")
    
    # Generate test data
    logs = generate_test_logs(log_count)
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_file = f.name
        for log in logs:
            f.write(json.dumps(log) + '\n')
    
    try:
        # Benchmark reading and parsing
        start_time = time.time()
        
        parsed_logs = []
        columns = set()
        
        # Simulate the optimized batch processing
        batch_size = 5000
        batch = []
        
        with open(temp_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    log_entry = json.loads(line)
                    batch.append(log_entry)
                    columns.update(log_entry.keys())
                    
                    if len(batch) >= batch_size:
                        parsed_logs.extend(batch)
                        batch = []
            
            if batch:
                parsed_logs.extend(batch)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"Parsed {len(parsed_logs):,} logs in {elapsed:.3f} seconds")
        print(f"Throughput: {len(parsed_logs) / elapsed:,.0f} logs/second")
        print(f"Found {len(columns)} unique columns")
        
    finally:
        os.unlink(temp_file)


def benchmark_search(log_count: int):
    """Benchmark search performance."""
    print(f"\n=== Benchmarking search with {log_count:,} logs ===")
    
    # Generate test data
    logs = generate_test_logs(log_count)
    
    # Test search with optimized concatenation
    search_term = 'error'
    
    start_time = time.time()
    results = []
    for log in logs:
        log_text = ' '.join(str(value).lower() for value in log.values())
        if search_term in log_text:
            results.append(log)
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"Searched {len(logs):,} logs for '{search_term}' in {elapsed:.3f} seconds")
    print(f"Found {len(results):,} matching logs")
    print(f"Throughput: {len(logs) / elapsed:,.0f} logs/second")


def benchmark_multi_search(log_count: int):
    """Benchmark multi-term search performance."""
    print(f"\n=== Benchmarking multi-term AND search with {log_count:,} logs ===")
    
    # Generate test data
    logs = generate_test_logs(log_count)
    
    # Test multi-term search with optimized early termination
    search_terms = ['error', 'failed']
    
    start_time = time.time()
    results = []
    for log in logs:
        log_text = ' '.join(str(value).lower() for value in log.values())
        if all(term in log_text for term in search_terms):
            results.append(log)
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"Searched {len(logs):,} logs for {len(search_terms)} terms (AND) in {elapsed:.3f} seconds")
    print(f"Found {len(results):,} matching logs")
    print(f"Throughput: {len(logs) / elapsed:,.0f} logs/second")


def main():
    """Run all benchmarks."""
    print("ZeroLog Viewer Performance Benchmarks")
    print("=" * 50)
    
    # Test with different data sizes
    sizes = [1000, 10000, 50000]
    
    for size in sizes:
        benchmark_file_parsing(size)
        benchmark_search(size)
        benchmark_multi_search(size)
    
    print("\n" + "=" * 50)
    print("Benchmarks complete!")


if __name__ == '__main__':
    main()
