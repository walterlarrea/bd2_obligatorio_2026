"""Collect metrics periodically for Postgres and MySQL during benchmark."""
import time
import re
import csv

def collect_postgres(conn, table, interval, stop_event, out_csv):
    cur = conn.cursor()
    with open(out_csv, 'w', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(['ts','n_tup_upd','n_dead_tup','rel_size_bytes'])
        while not stop_event.is_set():
            cur.execute("SELECT n_tup_upd, n_dead_tup FROM pg_stat_user_tables WHERE relname = %s", (table,))
            row = cur.fetchone()
            cur.execute("SELECT pg_relation_size(%s)", (table,))
            size = cur.fetchone()[0]
            writer.writerow([int(time.time()), row[0], row[1], size])
            fh.flush()
            time.sleep(interval)

def _parse_history_list(innodb_status_text):
    m = re.search(r'History list length\s+(\d+)', innodb_status_text)
    if m:
        return int(m.group(1))
    return None

def collect_mysql(conn, interval, stop_event, out_csv):
    cur = conn.cursor()
    with open(out_csv, 'w', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(['ts','history_list_length'])
        while not stop_event.is_set():
            cur.execute('SHOW ENGINE INNODB STATUS')
            txt = '\n'.join([row[0] for row in cur.fetchall()])
            hll = _parse_history_list(txt)
            writer.writerow([int(time.time()), hll])
            fh.flush()
            time.sleep(interval)
