# Benchmark MVCC: PostgreSQL vs MySQL (InnoDB)

Resumen y scripts para reproducir un benchmark que expone diferencias de MVCC entre PostgreSQL e InnoDB.

Requisitos:

- Python 3.8+
- Instalar dependencias:

```bash
python -m pip install -r scripts/requirements.txt
```

Archivos principales:

- `setup_db.py`: crea la tabla de prueba e inserta filas.
- `benchmark_runner.py`: orquesta clientes concurrentes que ejecutan `UPDATE` durante un tiempo.
- `worker.py`: lógica de cliente que realiza los `UPDATE`.
- `collect_metrics.py`: recoge métricas de Postgres y MySQL durante la prueba.
- `plot_results.py`: genera gráficas PNG comparativas.
- `generate_html_report.py`: genera reporte HTML interactivo con análisis.
- `run_full_benchmark.py`: orquestador automatizado (Docker + DB + benchmark + reportes).

Uso (ejemplo rápido):

1. Crear la tabla e insertar filas (ajusta `--rows` si no quieres 1M en desarrollo):

```bash
python scripts/setup_db.py --engine postgres --host localhost --port 5432 --user tu_usuario --password tu_pass --db tu_db --rows 1000000
```

2. Ejecutar benchmark (5 minutos por defecto):

```bash
python scripts/benchmark_runner.py --engine postgres --host localhost --port 5432 --user tu_usuario --password tu_pass --db tu_db --workers 16 --duration 300
```

3. Revisar logs CSV generados en el directorio actual.

Notas:

- Los scripts usan transacciones cortas (autocommit) para forzar muchas versiones en MVCC.
- Ajusta `--workers` y `--rows` según tu máquina.

## Docker (levantar contenedores de bases de datos)

Puedes levantar instancias locales de PostgreSQL y MySQL con Docker usando el `docker-compose.yml` incluido en la raíz del proyecto.

1. Levantar los servicios en background:

```bash
docker-compose up -d
```

2. Las credenciales por defecto (definidas en `docker-compose.yml`):

- PostgreSQL: `user=postgres`, `password=postgres`, `db=mvcc_db`, puerto `5432`
- MySQL: `user=mvcc_user`, `password=mvcc_pass`, `db=mvcc_db`, puerto `3306`

3. Después de arrancar los contenedores, ejecuta los scripts de preparación y benchmark desde tu host (ejemplo Postgres):

```bash
python scripts/setup_db.py --engine postgres --host localhost --port 5432 --user postgres --password postgres --db mvcc_db --rows 1000000
python scripts/benchmark_runner.py --engine postgres --host localhost --port 5432 --user postgres --password postgres --db mvcc_db --workers 16 --duration 300
```

4. Para parar y eliminar contenedores y volúmenes:

```bash
docker-compose down -v
```

## Quick Start (Automatizado)

Si prefieres ejecutar todo en un solo comando:

```bash
python scripts/run_full_benchmark.py --rows 100000 --workers 8 --duration 300
```

Esto lanzará:

1. Docker (Postgres + MySQL)
2. Población de tablas (100k filas en cada motor)
3. Benchmarks concurrentes (8 workers, 5 minutos)
4. Generación de gráficas de comparación
5. Limpieza de contenedores

Opciones disponibles:

```bash
python scripts/run_full_benchmark.py --help
```

Ejemplos:

- Smoke test (10k filas, 4 workers, 60s): `python scripts/run_full_benchmark.py --rows 10000 --workers 4 --duration 60`
- Benchmark pesado (1M filas, 16 workers, 10 min): `python scripts/run_full_benchmark.py --rows 1000000 --workers 16 --duration 600`
- Solo un motor: `python scripts/run_full_benchmark.py --engines postgres --rows 100000`
- Sin parar contenedores al final: `python scripts/run_full_benchmark.py --no-stop`

## Resetear Bases de Datos

Antes de ejecutar un nuevo benchmark, es recomendable resetear las bases de datos para asegurar que empiezan en un estado limpio sin datos residuales.

```bash
python scripts/reset_databases.py
```

Este script:

1. ✅ Inicia los servicios Docker si no están corriendo
2. ✅ Elimina la tabla `mvcc_bench` de PostgreSQL y MySQL
3. ✅ Limpia los contenedores Docker después del reset

**Opciones disponibles:**

```bash
# Resetear ambas bases de datos (default)
python scripts/reset_databases.py

# Resetear solo PostgreSQL
python scripts/reset_databases.py --engine postgres

# Resetear solo MySQL
python scripts/reset_databases.py --engine mysql

# Saltarse la confirmación (útil en automatización)
python scripts/reset_databases.py --force

# Mantener contenedores corriendo después del reset
python scripts/reset_databases.py --no-stop
```

**Flujo recomendado:**

```bash
# 1. Resetear bases de datos limpias
python scripts/reset_databases.py

# 2. Ejecutar benchmark en estado limpio
python scripts/run_full_benchmark.py --rows 100000 --workers 8 --duration 300

# 3. Revisar resultados en results/benchmark_report.html
```

**Archivos de salida:**

Los resultados de los benchmarks se guardan en la carpeta `results/`:

- `results/tps_postgres_*.csv` - Throughput de PostgreSQL
- `results/tps_mysql_*.csv` - Throughput de MySQL
- `results/metrics_postgres_*.csv` - Métricas MVCC de PostgreSQL
- `results/metrics_mysql_*.csv` - Métricas MVCC de MySQL
- `results/comparison_tps.png` - Gráfica comparativa de TPS
- `results/comparison_metrics.png` - Gráfica comparativa de métricas MVCC
- `results/benchmark_report.html` - Reporte HTML interactivo

## Resultados y Análisis

Los scripts generan los siguientes archivos:

- `tps_postgres_<timestamp>.csv`: TPS por intervalo (Postgres)
- `tps_mysql_<timestamp>.csv`: TPS por intervalo (MySQL)
- `metrics_postgres_<timestamp>.csv`: Métricas MVCC (Postgres): `n_tup_upd`, `n_dead_tup`, `rel_size_bytes`
- `metrics_mysql_<timestamp>.csv`: Métricas MVCC (MySQL): `history_list_length`
- `comparison_tps.png`: Gráfica comparativa de TPS
- `comparison_metrics.png`: Gráfica comparativa de métricas internas MVCC
- **`benchmark_report.html`**: Reporte interactivo con gráficas incrustadas, estadísticas y análisis detallado

### Reporte HTML

Después de ejecutar `run_full_benchmark.py`, abre `benchmark_report.html` en tu navegador para ver:

- **Resumen visual** con KPIs clave (Avg TPS, Max TPS, Total Updates)
- **Gráficas comparativas** incrustadas en PNG
- **Análisis profundo** de diferencias MVCC:
  - Write Amplification en PostgreSQL (table bloat)
  - Undo Log contention en MySQL (history list length)
  - Tabla comparativa de trade-offs arquitectónicos
  - Recomendaciones de uso basadas en workload

### Interpretación de Resultados

**PostgreSQL:**

- `n_dead_tup` (filas muertas): crece durante la prueba si el Autovacuum no da abasto
- `rel_size_bytes` (tamaño de la tabla): tiende a crecer por Write Amplification

**MySQL (InnoDB):**

- `history_list_length`: número de versiones viejas en el Undo Log. Idealmente cercano a 0. Si crece mucho durante la prueba, indica contención.
