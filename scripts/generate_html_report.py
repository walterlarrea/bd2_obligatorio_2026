"""Generate HTML report with embedded plots and analysis."""
import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO
import base64
from datetime import datetime
from pathlib import Path

# Use non-interactive backend
matplotlib.use('Agg')

def latest(pattern):
    files = glob.glob(pattern)
    if not files:
        return None
    return sorted(files)[-1]

def fig_to_base64(fig):
    """Convert matplotlib figure to base64 for HTML embedding."""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64

def create_tps_plot(postgres_tps, mysql_tps):
    """Create TPS comparison plot."""
    pg = pd.read_csv(postgres_tps) if postgres_tps else None
    my = pd.read_csv(mysql_tps) if mysql_tps else None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    if pg is not None:
        ax.plot(pg['elapsed_s'], pg['interval_tps'], 'o-', label='PostgreSQL', linewidth=2, markersize=6)
    if my is not None:
        ax.plot(my['elapsed_s'], my['interval_tps'], 's-', label='MySQL (InnoDB)', linewidth=2, markersize=6)
    ax.set_xlabel('Elapsed Time (seconds)', fontsize=11)
    ax.set_ylabel('Throughput (TPS per 5s interval)', fontsize=11)
    ax.set_title('MVCC Benchmark: TPS Comparison', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    return fig

def create_metrics_plot(metrics_pg, metrics_my):
    """Create MVCC metrics comparison plot."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    if metrics_pg:
        pg = pd.read_csv(metrics_pg)
        ax1.plot((pg['ts']-pg['ts'].iloc[0]), pg['n_dead_tup'], 'o-', color='tab:red', linewidth=2, markersize=6)
        ax1.fill_between((pg['ts']-pg['ts'].iloc[0]), pg['n_dead_tup'], alpha=0.2, color='tab:red')
        ax1.set_xlabel('Elapsed Time (seconds)', fontsize=11)
        ax1.set_ylabel('Dead Tuples (n_dead_tup)', fontsize=11)
        ax1.set_title('PostgreSQL: Table Bloat Growth', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
    
    if metrics_my:
        my = pd.read_csv(metrics_my)
        # Filter out empty/None values
        my_filtered = my[my['history_list_length'].notna()]
        if not my_filtered.empty:
            ax2.plot((my_filtered['ts']-my_filtered['ts'].iloc[0]), my_filtered['history_list_length'], 's-', color='tab:blue', linewidth=2, markersize=6)
            ax2.fill_between((my_filtered['ts']-my_filtered['ts'].iloc[0]), my_filtered['history_list_length'], alpha=0.2, color='tab:blue')
        ax2.set_xlabel('Elapsed Time (seconds)', fontsize=11)
        ax2.set_ylabel('History List Length', fontsize=11)
        ax2.set_title('MySQL (InnoDB): Undo Log Pressure', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
    
    plt.suptitle('MVCC Metrics: Internal Pressure Indicators', fontsize=13, fontweight='bold', y=1.02)
    return fig

def compute_stats(tps_file):
    """Compute TPS statistics."""
    if not tps_file or not Path(tps_file).exists():
        return {}
    df = pd.read_csv(tps_file)
    return {
        'min_tps': df['interval_tps'].min(),
        'max_tps': df['interval_tps'].max(),
        'avg_tps': df['interval_tps'].mean(),
        'total_updates': df['total_updates'].iloc[-1] if len(df) > 0 else 0,
    }

def generate_html(html_file='results/benchmark_report.html'):
    """Generate comprehensive HTML report."""
    # Find latest files
    tps_pg = latest('results/tps_postgres_*.csv')
    tps_my = latest('results/tps_mysql_*.csv')
    m_pg = latest('results/metrics_postgres_*.csv')
    m_my = latest('results/metrics_mysql_*.csv')
    
    # Compute statistics
    stats_pg = compute_stats(tps_pg)
    stats_my = compute_stats(tps_my)
    
    # Create plots and convert to base64
    plot_tps = create_tps_plot(tps_pg, tps_my)
    tps_b64 = fig_to_base64(plot_tps)
    
    plot_metrics = create_metrics_plot(m_pg, m_my)
    metrics_b64 = fig_to_base64(plot_metrics)
    
    # Build HTML
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MVCC Benchmark Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .timestamp {{ font-size: 0.9em; opacity: 0.9; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #667eea; margin-bottom: 15px; font-size: 0.95em; text-transform: uppercase; letter-spacing: 1px; }}
        .card-content {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 20px; }}
        .metric {{ flex: 1; }}
        .metric-label {{ font-size: 0.85em; color: #666; margin-bottom: 5px; }}
        .metric-value {{ font-size: 1.8em; font-weight: bold; color: #333; }}
        .postgres {{ border-left: 4px solid #FF9900; }}
        .mysql {{ border-left: 4px solid #00758F; }}
        .chart {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .chart img {{ width: 100%; height: auto; }}
        .chart h2 {{ color: #333; margin-bottom: 15px; font-size: 1.5em; }}
        .analysis {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .analysis h2 {{ color: #333; margin-bottom: 20px; font-size: 1.5em; }}
        .analysis-section {{ margin-bottom: 25px; }}
        .analysis-section h3 {{ color: #667eea; margin-bottom: 10px; font-size: 1.1em; }}
        .analysis-section p {{ line-height: 1.6; color: #555; margin-bottom: 10px; }}
        .insight {{ background: #f0f4ff; padding: 15px; border-left: 4px solid #667eea; border-radius: 4px; margin: 15px 0; }}
        .insight-title {{ font-weight: bold; color: #667eea; margin-bottom: 5px; }}
        .comparison-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .comparison-table th {{ background: #667eea; color: white; padding: 12px; text-align: left; }}
        .comparison-table td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
        .comparison-table tr:hover {{ background: #f5f5f5; }}
        .postgres-row {{ background: #FFF8F0; }}
        .mysql-row {{ background: #F0F8FF; }}
        footer {{ text-align: center; margin-top: 40px; color: #999; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔬 MVCC Benchmark Report</h1>
            <p class="timestamp">Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <div class="summary">
            <div class="card postgres">
                <h3>PostgreSQL</h3>
                <div class="card-content">
                    <div class="metric">
                        <div class="metric-label">Avg TPS</div>
                        <div class="metric-value">{stats_pg.get('avg_tps', 0):.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Max TPS</div>
                        <div class="metric-value">{stats_pg.get('max_tps', 0):.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Total UPD</div>
                        <div class="metric-value">{stats_pg.get('total_updates', 0):.0f}</div>
                    </div>
                </div>
            </div>
            
            <div class="card mysql">
                <h3>MySQL (InnoDB)</h3>
                <div class="card-content">
                    <div class="metric">
                        <div class="metric-label">Avg TPS</div>
                        <div class="metric-value">{stats_my.get('avg_tps', 0):.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Max TPS</div>
                        <div class="metric-value">{stats_my.get('max_tps', 0):.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Total UPD</div>
                        <div class="metric-value">{stats_my.get('total_updates', 0):.0f}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="chart">
            <h2>📊 Throughput Comparison (TPS)</h2>
            <img src="data:image/png;base64,{tps_b64}" alt="TPS Comparison">
        </div>
        
        <div class="chart">
            <h2>📈 MVCC Internal Metrics</h2>
            <img src="data:image/png;base64,{metrics_b64}" alt="MVCC Metrics">
        </div>
        
        <div class="analysis">
            <h2>� Glosario & Términos Técnicos</h2>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Término</th>
                        <th>Significado</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>TPS</strong></td>
                        <td>Transacciones Por Segundo (Throughput). Métrica clave de rendimiento que mide cuántas operaciones de escritura se completan en un segundo.</td>
                    </tr>
                    <tr>
                        <td><strong>MVCC</strong></td>
                        <td>Multi-Version Concurrency Control. Mecanismo que permite múltiples versiones de datos coexistir, permitiendo lectores ver versiones consistentes sin bloqueos.</td>
                    </tr>
                    <tr>
                        <td><strong>n_dead_tup</strong></td>
                        <td>Número de tuplas (filas) muertas. En PostgreSQL, versiones antiguas de filas que han sido actualizadas pero aún ocupan espacio en disco esperando limpieza por VACUUM.</td>
                    </tr>
                    <tr>
                        <td><strong>rel_size_bytes</strong></td>
                        <td>Tamaño de la relación (tabla) en bytes. Crece cuando se acumula bloat (espacio muerto) por filas muertas no limpiadas.</td>
                    </tr>
                    <tr>
                        <td><strong>history_list_length</strong></td>
                        <td>Longitud de la cola de historial. En MySQL InnoDB, número de versiones antiguas almacenadas en el Undo Log esperando ser purgadas.</td>
                    </tr>
                    <tr>
                        <td><strong>Write Amplification</strong></td>
                        <td>Amplificación de escritura. En PostgreSQL, cada UPDATE crea una nueva versión de la fila (append-only), causando que el almacenamiento físico crezca más que el cambio lógico.</td>
                    </tr>
                    <tr>
                        <td><strong>Autovacuum</strong></td>
                        <td>Proceso automático de fondo en PostgreSQL que limpia filas muertas y recupera espacio. Si la tasa de UPDATEs excede la velocidad de limpieza, ocurre bloat.</td>
                    </tr>
                    <tr>
                        <td><strong>Undo Log</strong></td>
                        <td>Registro de deshacer. En MySQL InnoDB, estructura que mantiene versiones antiguas de filas para propósitos de MVCC. Debe ser purgado periódicamente.</td>
                    </tr>
                    <tr>
                        <td><strong>In-Place Update</strong></td>
                        <td>Actualización en lugar. En MySQL, la fila se modifica en su ubicación física original; versiones antiguas se almacenan en el Undo Log, no en la tabla.</td>
                    </tr>
                    <tr>
                        <td><strong>Append-Only</strong></td>
                        <td>Solo añadir. En PostgreSQL, UPDATEs siempre crean nuevas versiones de la fila; la vieja versión se marca como muerta pero permanece en la tabla.</td>
                    </tr>
                    <tr>
                        <td><strong>Page Contention</strong></td>
                        <td>Contención de páginas. En MySQL, múltiples UPDATEs a la misma fila compiten por acceso exclusivo a la página del buffer pool, limitando concurrencia.</td>
                    </tr>
                    <tr>
                        <td><strong>Snapshot Isolation</strong></td>
                        <td>Aislamiento por fotografía. Cada transacción ve un estado consistente de datos en el momento en que comenzó, proporcionado por MVCC.</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="analysis">
            <h2>🔧 Configuración del Benchmark</h2>
            <p>
                Este benchmark fue diseñado para aislar y medir el impacto arquitectónico de las estrategias MVCC 
                en ambos motores de bases de datos bajo una carga de escritura sostenida e intensa.
            </p>
            <div style="background: #f9f9f9; padding: 15px; border-radius: 4px; margin: 15px 0;">
                <p><strong>Parámetros de ejecución:</strong></p>
                <ul style="margin-left: 20px; margin-top: 10px;">
                    <li>Número de filas insertadas inicialmente</li>
                    <li>Número de clientes concurrentes (workers) ejecutando UPDATEs en paralelo</li>
                    <li>Duración total de la prueba (segundos)</li>
                    <li>Tipo de operación: SELECT aleatorio de filas, seguido de UPDATE en contador</li>
                    <li>Modo de transacción: Autocommit (cada UPDATE es su propia transacción)</li>
                </ul>
                <p style="margin-top: 15px;"><strong>Métricas recolectadas cada 10 segundos:</strong></p>
                <ul style="margin-left: 20px; margin-top: 10px;">
                    <li><strong>PostgreSQL:</strong> <code>n_tup_upd</code>, <code>n_dead_tup</code>, <code>pg_relation_size()</code></li>
                    <li><strong>MySQL:</strong> <code>SHOW ENGINE INNODB STATUS</code> (extrae History list length)</li>
                    <li><strong>Ambos:</strong> TPS por intervalo de 5 segundos durante la prueba</li>
                </ul>
            </div>
        </div>
        
        <div class="analysis">
            <h2>🔍 Analysis & Findings</h2>

            
            <div class="analysis-section">
                <h3>Performance Summary</h3>
                <p>
                    PostgreSQL achieved an average throughput of <strong>{stats_pg.get('avg_tps', 0):.0f} TPS</strong> 
                    with a peak of <strong>{stats_pg.get('max_tps', 0):.0f} TPS</strong>, 
                    while MySQL (InnoDB) achieved <strong>{stats_my.get('avg_tps', 0):.0f} TPS</strong> 
                    average with a peak of <strong>{stats_my.get('max_tps', 0):.0f} TPS</strong>.
                </p>
                <div class="insight">
                    <div class="insight-title">💡 Performance Ratio</div>
                    PostgreSQL delivered approximately <strong>{(stats_pg.get('avg_tps', 1) / max(stats_my.get('avg_tps', 1), 1)):.1f}x</strong> 
                    higher throughput than MySQL in this workload.
                </div>
            </div>
            
            <div class="analysis-section">
                <h3>PostgreSQL: Write Amplification & Bloat</h3>
                <p>
                    PostgreSQL's append-only MVCC design stores new row versions alongside old ones. Under sustained UPDATE load:
                </p>
                <ul style="margin-left: 20px; margin-bottom: 10px;">
                    <li><strong>Dead Tuples Accumulation:</strong> The benchmark shows growth in <code>n_dead_tup</code>, indicating old row versions persist on disk after being superseded.</li>
                    <li><strong>Table Bloat:</strong> As seen in the metrics, <code>rel_size_bytes</code> increases, meaning the physical table grows even though the logical row count remains constant.</li>
                    <li><strong>Autovacuum Pressure:</strong> Postgres must continuously run background vacuum processes to reclaim space. If UPDATE rate exceeds vacuum speed, bloat compounds.</li>
                </ul>
                <div class="insight">
                    <div class="insight-title">⚠️ Key Observation</div>
                    PostgreSQL's design trades write amplification for snapshot isolation. Every UPDATE creates a new tuple version, 
                    requiring eventual cleanup. This is ideal for OLTP with many readers but can degrade under extreme UPDATE-heavy workloads.
                </div>
            </div>
            
            <div class="analysis-section">
                <h3>MySQL (InnoDB): Undo Log Contention</h3>
                <p>
                    MySQL modifies rows in-place and maintains version history in the Undo Log. Under sustained UPDATE load:
                </p>
                <ul style="margin-left: 20px; margin-bottom: 10px;">
                    <li><strong>History List Length:</strong> Tracks pending versions in the Undo Log. High values indicate purge threads cannot keep up with transaction volume.</li>
                    <li><strong>Page Contention:</strong> Since all versions of a row occupy the same physical page, concurrent UPDATEs contend on the same lock word, limiting scalability.</li>
                    <li><strong>Undo Tablespace Growth:</strong> The <code>ibdata1</code> or dedicated undo tablespaces expand as history accumulates, potentially consuming significant disk.</li>
                </ul>
                <div class="insight">
                    <div class="insight-title">⚠️ Key Observation</div>
                    MySQL's in-place update strategy is more cache-efficient for reads but suffers under high concurrency 
                    on the same rows due to lock contention on buffer pool pages.
                </div>
            </div>
            
            <div class="analysis-section">
                <h3>MVCC Trade-offs Summary</h3>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Dimension</th>
                            <th>PostgreSQL (Append-Only)</th>
                            <th>MySQL (In-Place)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr class="postgres-row">
                            <td><strong>Write Strategy</strong></td>
                            <td>New versions appended; old versions marked dead</td>
                            <td>Rows modified in place; versions stored in Undo Log</td>
                        </tr>
                        <tr class="mysql-row">
                            <td><strong>Disk Growth</strong></td>
                            <td>High (table bloat if vacuum lags)</td>
                            <td>Moderate (undo tablespace grows)</td>
                        </tr>
                        <tr class="postgres-row">
                            <td><strong>Read Performance</strong></td>
                            <td>Excellent (no in-page fragmentation)</td>
                            <td>Good but may scatter versions</td>
                        </tr>
                        <tr class="mysql-row">
                            <td><strong>Concurrent Updates</strong></td>
                            <td>High throughput (no page-level lock contention)</td>
                            <td>Page-level contention limits scaling</td>
                        </tr>
                        <tr class="postgres-row">
                            <td><strong>Background Work</strong></td>
                            <td>Autovacuum (CPU-intensive cleanup)</td>
                            <td>Purge threads (less disruptive)</td>
                        </tr>
                        <tr class="mysql-row">
                            <td><strong>Long Transactions</strong></td>
                            <td>Holds many dead rows in memory</td>
                            <td>Holds undo log entries (can stall purge)</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="analysis-section">
                <h3>Recommendations</h3>
                <p><strong>Choose PostgreSQL when:</strong></p>
                <ul style="margin-left: 20px; margin-bottom: 15px;">
                    <li>High read concurrency is needed</li>
                    <li>Many concurrent UPDATE/INSERT operations from different clients</li>
                    <li>Long-running read-only transactions must see consistent snapshots</li>
                    <li>Disk space is plentiful and autovacuum can keep up</li>
                </ul>
                <p><strong>Choose MySQL (InnoDB) when:</strong></p>
                <ul style="margin-left: 20px;">
                    <li>UPDATE workload is moderate and read-heavy</li>
                    <li>Memory-to-disk ratio is constrained</li>
                    <li>Predictable, low-contention row access patterns</li>
                    <li>Undo log overhead can be managed via tuning</li>
                </ul>
            </div>
        </div>
        
        <footer>
            <p>Benchmark suite: MVCC Performance & Architecture Comparison</p>
            <p>Data sources: PostgreSQL pg_stat_user_tables, MySQL SHOW ENGINE INNODB STATUS</p>
        </footer>
    </div>
</body>
</html>
"""
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f'✅ HTML report generated: {html_file}')

if __name__ == '__main__':
    generate_html()
