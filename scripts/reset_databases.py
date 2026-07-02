#!/usr/bin/env python3
"""Reset/clear benchmark databases to clean state.

Usage:
  python scripts/reset_databases.py              # Resets both PostgreSQL and MySQL
  python scripts/reset_databases.py --engine postgres  # Reset only PostgreSQL
  python scripts/reset_databases.py --engine mysql     # Reset only MySQL

This script:
  1. Drops the mvcc_bench table from the specified database(s)
  2. Removes all benchmark data and metrics
  3. Leaves the database ready for fresh benchmark runs

WARNING: This is DESTRUCTIVE - all benchmark data will be permanently deleted.
"""
import argparse
import sys

def parse_args():
    p = argparse.ArgumentParser(description='Reset benchmark databases')
    p.add_argument('--engine', choices=('postgres', 'mysql', 'both'), default='both',
                   help='Which engine(s) to reset (default: both)')
    p.add_argument('--table', default='mvcc_bench',
                   help='Table name to drop (default: mvcc_bench)')
    p.add_argument('--force', action='store_true',
                   help='Skip confirmation prompt')
    return p.parse_args()

def reset_postgres(table_name, force=False):
    """Reset PostgreSQL database."""
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            dbname='mvcc_db'
        )
        cur = conn.cursor()
        
        # Check if table exists
        cur.execute(f"""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            )
        """)
        exists = cur.fetchone()[0]
        
        if not exists:
            print(f"ℹ️  PostgreSQL: Table '{table_name}' does not exist, nothing to reset")
            conn.close()
            return True
        
        if not force:
            response = input(f"⚠️  PostgreSQL: Drop table '{table_name}'? (type 'yes' to confirm): ")
            if response.lower() != 'yes':
                print("Cancelled PostgreSQL reset")
                conn.close()
                return False
        
        # Drop table
        cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        conn.commit()
        print(f"✅ PostgreSQL: Table '{table_name}' dropped successfully")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL Error: {e}")
        return False

def reset_mysql(table_name, force=False):
    """Reset MySQL database."""
    try:
        import pymysql
    except ImportError:
        print("ERROR: pymysql not installed. Install with: pip install pymysql")
        return False
    
    try:
        conn = pymysql.connect(
            host='localhost',
            port=3307,
            user='mvcc_user',
            password='mvcc_pass',
            database='mvcc_db',
            autocommit=False
        )
        cur = conn.cursor()
        
        # Check if table exists
        cur.execute(f"SHOW TABLES LIKE '{table_name}'")
        exists = cur.fetchone() is not None
        
        if not exists:
            print(f"ℹ️  MySQL: Table '{table_name}' does not exist, nothing to reset")
            conn.close()
            return True
        
        if not force:
            response = input(f"⚠️  MySQL: Drop table '{table_name}'? (type 'yes' to confirm): ")
            if response.lower() != 'yes':
                print("Cancelled MySQL reset")
                conn.close()
                return False
        
        # Drop table
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        print(f"✅ MySQL: Table '{table_name}' dropped successfully")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ MySQL Error: {e}")
        return False

def main():
    args = parse_args()
    
    print("\n" + "="*60)
    print("  DATABASE RESET UTILITY")
    print("="*60)
    
    success = True
    
    if args.engine in ('postgres', 'both'):
        if not reset_postgres(args.table, force=args.force):
            success = False
    
    if args.engine in ('mysql', 'both'):
        if not reset_mysql(args.table, force=args.force):
            success = False
    
    print("\n" + "="*60)
    if success:
        print("✅ Reset complete! Databases are ready for fresh benchmarks.")
    else:
        print("❌ Reset encountered errors. Please check above for details.")
    print("="*60 + "\n")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
