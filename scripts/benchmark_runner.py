"""Orchestrator: launches worker threads and metrics collectors."""
import argparse
import threading
import time
import importlib
import os
import sys

# Ensure local `scripts` folder is on sys.path so sibling modules import correctly
sys.path.insert(0, os.path.dirname(__file__))

from worker import run_worker_postgres, run_worker_mysql
from collect_metrics import collect_postgres, collect_mysql

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--engine', choices=('postgres','mysql'), required=True)
    p.add_argument('--host', required=True)
    p.add_argument('--port', type=int)
    p.add_argument('--user', required=True)
    p.add_argument('--password', required=True)
    p.add_argument('--db', required=True)
    p.add_argument('--table', default='mvcc_bench')
    p.add_argument('--workers', type=int, default=8)
    p.add_argument('--duration', type=int, default=300)
    p.add_argument('--rows', type=int, default=1000000)
    p.add_argument('--metrics_interval', type=int, default=10)
    return p.parse_args()

def connect_postgres(host, port, user, password, db):
    import psycopg2
    port = port or 5432
    conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=db)
    return conn

def connect_mysql(host, port, user, password, db):
    import pymysql
    port = port or 3306
    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db, autocommit=True)
    return conn

def main():
    args = parse_args()
    stop_event = threading.Event()
    counter = {'count': 0}
    workers = []
    if args.engine == 'postgres':
        # create separate connections per thread
        for _ in range(args.workers):
            conn = connect_postgres(args.host, args.port, args.user, args.password, args.db)
            t = threading.Thread(target=run_worker_postgres, args=(conn, args.table, args.rows, stop_event, counter), daemon=True)
            workers.append((t, conn))
        metrics_conn = connect_postgres(args.host, args.port, args.user, args.password, args.db)
        metrics_thread = threading.Thread(target=collect_postgres, args=(metrics_conn, args.table, args.metrics_interval, stop_event, f'results/metrics_postgres_{int(time.time())}.csv'), daemon=True)
    else:
        for _ in range(args.workers):
            conn = connect_mysql(args.host, args.port, args.user, args.password, args.db)
            t = threading.Thread(target=run_worker_mysql, args=(conn, args.table, args.rows, stop_event, counter), daemon=True)
            workers.append((t, conn))
        metrics_conn = connect_mysql(args.host, args.port, args.user, args.password, args.db)
        metrics_thread = threading.Thread(target=collect_mysql, args=(metrics_conn, args.metrics_interval, stop_event, f'results/metrics_mysql_{int(time.time())}.csv'), daemon=True)

    # start workers
    for t, _ in workers:
        t.start()
    metrics_thread.start()

    print(f'Starting benchmark: engine={args.engine} workers={args.workers} duration={args.duration}s')
    start = time.time()
    last_count = 0
    tps_csv = f'results/tps_{args.engine}_{int(start)}.csv'
    # write header for TPS CSV
    try:
        tfh = open(tps_csv, 'w', newline='')
        import csv as _csv
        tw = _csv.writer(tfh)
        tw.writerow(['ts','elapsed_s','total_updates','interval_tps'])
    except Exception:
        tfh = None
        tw = None
    try:
        while time.time() - start < args.duration:
            time.sleep(5)
            now = time.time()
            elapsed = now - start
            total = counter['count']
            tps = (total - last_count) / 5.0
            last_count = total
            print(f'[{int(elapsed)}s] total_updates={total} last_5s_tps={tps:.1f}')
            if tw:
                tw.writerow([int(now), int(elapsed), total, round(tps,1)])
                tfh.flush()
    except KeyboardInterrupt:
        print('Interrupted, stopping...')
    finally:
        stop_event.set()
        # allow threads to finish
        time.sleep(1)
        # close connections
        for _, conn in workers:
            try:
                conn.close()
            except Exception:
                pass
        try:
            metrics_conn.close()
        except Exception:
            pass
        print('Benchmark finished')

if __name__ == '__main__':
    main()
