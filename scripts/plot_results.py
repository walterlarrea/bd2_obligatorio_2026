"""Plot TPS and MVCC metrics for Postgres and MySQL.

Usage: python scripts/plot_results.py
Auto-detects latest `tps_postgres_*.csv`, `tps_mysql_*.csv`, `metrics_postgres_*.csv`, `metrics_mysql_*.csv`.
Generates `comparison_tps.png` and `comparison_metrics.png`.
"""
import glob
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def latest(pattern):
    files = glob.glob(pattern)
    if not files:
        return None
    return sorted(files)[-1]

def plot_tps(postgres_tps, mysql_tps):
    pg = pd.read_csv(postgres_tps) if postgres_tps else None
    my = pd.read_csv(mysql_tps) if mysql_tps else None
    plt.figure(figsize=(10,5))
    if pg is not None:
        plt.plot(pg['elapsed_s'], pg['interval_tps'], label='Postgres TPS')
    if my is not None:
        plt.plot(my['elapsed_s'], my['interval_tps'], label='MySQL TPS')
    plt.xlabel('Elapsed seconds')
    plt.ylabel('TPS (per 5s interval)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('results/comparison_tps.png')
    print('Saved results/comparison_tps.png')

def plot_metrics(metrics_pg, metrics_my):
    fig, ax1 = plt.subplots(figsize=(10,5))
    if metrics_pg:
        pg = pd.read_csv(metrics_pg)
        ax1.plot((pg['ts']-pg['ts'].iloc[0]), pg['n_dead_tup'], color='tab:red', label='Postgres dead tuples')
        ax1.set_ylabel('n_dead_tup', color='tab:red')
    if metrics_my:
        my = pd.read_csv(metrics_my)
        ax2 = ax1.twinx()
        ax2.plot((my['ts']-my['ts'].iloc[0]), my['history_list_length'], color='tab:blue', label='MySQL history_list_length')
        ax2.set_ylabel('history_list_length', color='tab:blue')
    ax1.set_xlabel('Elapsed seconds')
    fig.tight_layout()
    plt.savefig('results/comparison_metrics.png')
    print('Saved results/comparison_metrics.png')

if __name__ == '__main__':
    tps_pg = latest('results/tps_postgres_*.csv')
    tps_my = latest('results/tps_mysql_*.csv')
    m_pg = latest('results/metrics_postgres_*.csv')
    m_my = latest('results/metrics_mysql_*.csv')
    print('Using:', tps_pg, tps_my, m_pg, m_my)
    plot_tps(tps_pg, tps_my)
    plot_metrics(m_pg, m_my)
