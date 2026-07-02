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
