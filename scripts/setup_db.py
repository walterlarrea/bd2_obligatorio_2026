#!/usr/bin/env python3
"""Create test table and populate rows for Postgres or MySQL (InnoDB).

Usage: python scripts/setup_db.py --engine postgres|mysql --host ... --user ... --password ... --db ... --rows 1000000
"""
import argparse
import random

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--engine', choices=('postgres','mysql'), required=True)
    p.add_argument('--host', required=True)
    p.add_argument('--port', type=int)
    p.add_argument('--user', required=True)
    p.add_argument('--password', required=True)
    p.add_argument('--db', required=True)
    p.add_argument('--table', default='mvcc_bench')
    p.add_argument('--rows', type=int, default=1000000)
    return p.parse_args()

def setup_postgres(conn, table, rows):
    cur = conn.cursor()
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {table} (
      id serial PRIMARY KEY,
      nombre text,
      contador bigint DEFAULT 0,
      updated_at timestamptz DEFAULT now()
    );
    """)
    # cur.execute(f"""
    # CREATE INDEX IF NOT EXISTS counters_index ON {table} (contador)
    # """)
    conn.commit()
    cur.execute(f"SELECT count(*) FROM {table}")
    existing = cur.fetchone()[0]
    if existing >= rows:
        print('Ya hay suficientes filas, saltando inserción')
        return
    batch = 5000
    to_insert = rows - existing
    print(f'Insertando {to_insert} filas en batches de {batch}...')
    for i in range(0, to_insert, batch):
        vals = [(f'usuario_{random.randint(1,rows)}', 0) for _ in range(min(batch, to_insert - i))]
        args_str = ','.join(['(%s,%s)'] * len(vals))
        flattened = [x for tup in vals for x in tup]
        cur.execute(f"INSERT INTO {table} (nombre, contador) VALUES " + 
                    ','.join(['(%s,%s)']*len(vals)), flattened)
        conn.commit()

def setup_mysql(conn, table, rows):
    cur = conn.cursor()
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {table} (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      nombre TEXT,
      contador BIGINT DEFAULT 0,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """)
    conn.commit()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    existing = cur.fetchone()[0]
    if existing >= rows:
        print('Ya hay suficientes filas, saltando inserción')
        return
    batch = 5000
    to_insert = rows - existing
    print(f'Insertando {to_insert} filas en batches de {batch}...')
    for i in range(0, to_insert, batch):
        vals = [(f'usuario_{random.randint(1,rows)}', 0) for _ in range(min(batch, to_insert - i))]
        cur.executemany(f"INSERT INTO {table} (nombre, contador) VALUES (%s,%s)", vals)
        conn.commit()

def main():
    args = parse_args()
    if args.engine == 'postgres':
        import psycopg2
        port = args.port or 5432
        conn = psycopg2.connect(host=args.host, port=port, user=args.user, password=args.password, dbname=args.db)
        setup_postgres(conn, args.table, args.rows)
        conn.close()
    else:
        import pymysql
        port = args.port or 3306
        conn = pymysql.connect(host=args.host, port=port, user=args.user, password=args.password, database=args.db, autocommit=False)
        setup_mysql(conn, args.table, args.rows)
        conn.close()

if __name__ == '__main__':
    main()
