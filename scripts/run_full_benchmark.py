#!/usr/bin/env python3
"""Automated full benchmark orchestrator: Docker, DB setup, benchmarks, and plots.

Usage:
  python scripts/run_full_benchmark.py --rows 100000 --workers 8 --duration 300

This will:
1. Ensure docker-compose services are running
2. Create tables and populate rows in Postgres and MySQL
3. Run benchmarks on both engines
4. Generate comparison plots (comparison_tps.png, comparison_metrics.png)
"""
import argparse
import subprocess
import time
import sys
import os

def run_cmd(cmd, desc=''):
    """Run shell command and return success/failure."""
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def ensure_docker():
    """Ensure docker-compose services are running."""
    print("Checking docker-compose services...")
    result = subprocess.run('docker-compose ps --services --filter "status=running"', shell=True, capture_output=True, text=True)
    running = result.stdout.strip().split('\n') if result.stdout.strip() else []
    needed = {'postgres', 'mysql'}
    if not needed.issubset(set(running)):
        print("Starting docker-compose services...")
        if not run_cmd('docker-compose up -d', 'Starting Docker services'):
            return False
    print("Docker services are running.")
    # Small wait for DB readiness
    time.sleep(5)
    return True

def parse_args():
    p = argparse.ArgumentParser(description='Automated MVCC benchmark suite')
    p.add_argument('--rows', type=int, default=100000, help='Number of rows to insert (default 100000)')
    p.add_argument('--workers', type=int, default=8, help='Concurrent workers for benchmark (default 8)')
    p.add_argument('--duration', type=int, default=300, help='Benchmark duration in seconds (default 300)')
    p.add_argument('--engines', nargs='+', choices=['postgres', 'mysql'], default=['postgres', 'mysql'], help='Which engines to benchmark (default both)')
    p.add_argument('--no-plot', action='store_true', help='Skip plot generation')
    p.add_argument('--no-stop', action='store_true', help='Keep docker containers running after benchmark')
    return p.parse_args()

def run_benchmark_for_engine(engine, args):
    """Run setup and benchmark for a single engine."""
    if engine == 'postgres':
        host, port, user, password = 'localhost', 5432, 'postgres', 'postgres'
    else:
        host, port, user, password = 'localhost', 3307, 'mvcc_user', 'mvcc_pass'
    
    db = 'mvcc_db'
    
    # Setup DB
    setup_cmd = (
        f'python scripts/setup_db.py '
        f'--engine {engine} --host {host} --port {port} --user {user} --password {password} '
        f'--db {db} --rows {args.rows}'
    )
    if not run_cmd(setup_cmd, f'Setup {engine.upper()} (insert {args.rows} rows)'):
        print(f"Failed to setup {engine}", file=sys.stderr)
        return False
    
    # Run benchmark
    bench_cmd = (
        f'python scripts/benchmark_runner.py '
        f'--engine {engine} --host {host} --port {port} --user {user} --password {password} '
        f'--db {db} --workers {args.workers} --duration {args.duration} --rows {args.rows}'
    )
    if not run_cmd(bench_cmd, f'Benchmark {engine.upper()} ({args.workers} workers, {args.duration}s)'):
        print(f"Failed to benchmark {engine}", file=sys.stderr)
        return False
    
    return True

def main():
    args = parse_args()
    
    print("MVCC Benchmark Suite - Full Automation")
    print(f"  Rows: {args.rows}, Workers: {args.workers}, Duration: {args.duration}s")
    
    # Ensure Docker is running
    if not ensure_docker():
        print("Failed to start docker services", file=sys.stderr)
        return 1
    
    # Run benchmarks
    for engine in args.engines:
        if not run_benchmark_for_engine(engine, args):
            return 1
    
    # Plot results
    if not args.no_plot:
        if not run_cmd('python scripts/plot_results.py', 'Generating comparison plots'):
            print("Warning: plot generation failed", file=sys.stderr)
    
    # Generate HTML report
    if not run_cmd('python scripts/generate_html_report.py', 'Generating HTML report'):
        print("Warning: HTML report generation failed", file=sys.stderr)
    
    # Optionally stop containers
    if not args.no_stop:
        run_cmd('docker-compose down -v', 'Cleaning up docker containers')
    
    print("\n" + "="*60)
    print("  Benchmark complete!")
    print("  📊 Check: results/comparison_tps.png, results/comparison_metrics.png")
    print("  📄 Open: results/benchmark_report.html in your browser")
    print("="*60)
    return 0

if __name__ == '__main__':
    sys.exit(main())
