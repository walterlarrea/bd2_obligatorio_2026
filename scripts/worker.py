"""Worker module: runs UPDATE loops against a table.
"""
import random

def run_worker_postgres(conn, table, max_id, stop_event, counter_ref):
    cur = conn.cursor()
    conn.autocommit = True
    while not stop_event.is_set():
        rid = random.randint(1, max_id)
        cur.execute(f"UPDATE {table} SET contador = contador + 1, updated_at = now() WHERE id = %s", (rid,))
        counter_ref['count'] += 1

def run_worker_mysql(conn, table, max_id, stop_event, counter_ref):
    cur = conn.cursor()
    conn.autocommit(True)
    while not stop_event.is_set():
        rid = random.randint(1, max_id)
        cur.execute(f"UPDATE {table} SET contador = contador + 1 WHERE id = %s", (rid,))
        counter_ref['count'] += 1
