1. Naturaleza y Propósito de un SGBD frente a otras herramientas
   - Diferencia funcional entre Hoja de Cálculo (Excel) y SGBD: Orientación a operaciones de cálculo en filas/columnas individuales vs. gestión de relaciones entre conjuntos de datos que reflejan una realidad evolutiva.
   - Diferencia entre SGBD y Sistemas de Archivos del SO: Limitaciones del software tradicional en el manejo manual de archivos grandes, falta de lenguajes de consulta nativos y deficiencias en la gestión de accesos simultáneos.
   - Criterio de selección de arquitectura: Identificación del escenario del problema (ej. contabilidad compleja con programación vs. control de stock simple en planilla) para elegir la herramienta adecuada.
2. Características y Mecanismos Core de un SGBD
   - Transaccionalidad: Propiedad que dota de robustez y permite validaciones avanzadas para asegurar que las operaciones se completen correctamente o no se apliquen en absoluto.
   - Controles de Integridad: Mecanismos que garantizan que los datos almacenados cumplan con las restricciones lógicas y de negocio del sistema.
   - Lenguajes del SGBD:
     - DDL (Data Definition Language): Lenguaje para definir la estructura de los datos.
     - DQL / DML (Query / Data Manipulation Language): Lenguajes para consultar y manipular los datos.
3. Concurrencia y Consistencia
   - Gestión de Concurrencia y Sincronización: Capacidad del SGBD para arbitrar el acceso simultáneo de múltiples usuarios a los mismos recursos.
   - Acceso Simultáneo No Controlado: Problema que genera inconsistencias en los datos cuando dos procesos modifican el mismo recurso a la vez (ej. el caso de la última unidad en stock).
   - Serialización de Accesos: Solución del SGBD que obliga a los usuarios/procesos a acceder "en fila" o de forma secuencial para evitar conflictos.
4. Seguridad Multicapa
   - Seguridad Física y del Sistema Operativo: Dependencia base de la infraestructura (permisos del file system del servidor, control de acceso físico a la máquina) para evitar la exposición del archivo crudo de la base de datos.
   - Seguridad Propia del SGBD: Esquema de seguridad de grano fino que complementa al SO, permitiendo asignar permisos y privilegios específicos a nivel de usuarios o grupos sobre objetos concretos (tablas, vistas, bases de datos completas).
5. Teoría Relacional y Lenguajes de Consulta
   - Modelo Relacional: Modelo teórico basado en la existencia de conjuntos y relaciones matemáticos.
   - Álgebra Relacional: Lenguaje formal y teórico compuesto por operaciones como la Proyección ($\Pi$) y la Selección ($\sigma$).
   - SQL (Structured Query Language): Lenguaje comercial y práctico utilizado para interactuar con los SGBD relacionales.
   - Poder Expresivo: Capacidad de un lenguaje para representar operaciones. Se establece que el poder expresivo de SQL es mayor que el del álgebra relacional debido a capacidades de ordenamiento, agrupación y agregación (ej. GROUP BY, ORDER BY, COUNT) que no existen en el álgebra pura.
6. Optimización de Rendimiento
   - Índices: Estructuras auxiliares que funcionan como punteros o atajos directos a los elementos almacenados. Permiten el acceso aleatorio y evitan la secuenciación (recorrido línea por línea) de tablas gigantes.
   - Compromiso de Recursos (Trade-off): El costo o "precio" en espacio de almacenamiento que se paga voluntariamente a cambio de una ganancia en el tiempo de ejecución y eficiencia de las búsquedas.
7. Automatización y Lógica de Negocio en la BD
   - Triggers (Disparadores): Bloques de código que se ejecutan automáticamente ante eventos específicos en la base de datos (AFTER UPDATE, AFTER INSERT, AFTER DELETE).
   - Casos de uso de Triggers:
     - Creación de logs de auditoría (guardar valores viejos y nuevos tras una modificación).
     - Ejecución de algoritmos de validación complejos que exceden las restricciones (constraints) estándar del SGBD.

   **Mapeo a PostgreSQL**
   - **Naturaleza y propósito**: PostgreSQL es un SGBD relacional ACID, orientado a integridad y extensibilidad. Soporta SQL estándar ampliado y ofrece herramientas para integrar lógica avanzada en la BD (extensiones, tipos y funciones).

   - **Transaccionalidad (BEGIN/COMMIT/ROLLBACK)**: PostgreSQL implementa transacciones ACID. Uso típico:

   ```
   BEGIN;
   UPDATE productos SET stock = stock - 1 WHERE id = 42;
   COMMIT;
   -- o ROLLBACK en caso de error
   ```

   - **MVCC y niveles de aislamiento**: PostgreSQL usa MVCC para concurrencia sin bloquear lecturas. Soporta los niveles de aislamiento SQL: `Read Committed` (por defecto) y `Serializable` (implementado con Serializable Snapshot Isolation). Para `Serializable`:

   ```
   SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
   ```

   - **Bloqueos y concurrencia**: además de MVCC, existen locks explícitos (`FOR UPDATE`, `LOCK TABLE`) y funciones para detectar conflictos. PostgreSQL resuelve deadlocks y reporta errores cuando ocurren.

   - **Controles de integridad**: PostgreSQL soporta `PRIMARY KEY`, `UNIQUE`, `CHECK`, `FOREIGN KEY`, `NOT NULL` y restricciones avanzadas (exclusion constraints con índices GiST/GiN). También se pueden implementar reglas complejas con `CHECK` o triggers.

   - **DDL / DML / DQL**: PostgreSQL implementa el estándar SQL con extensiones (CTE recursivas, `RETURNING`, `UPSERT` mediante `ON CONFLICT`). Ejemplo de `UPSERT`:

   ```
   INSERT INTO usuarios(id,email) VALUES(1,'a@x')
   ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email;
   ```

   - **Índices y optimización**: PostgreSQL ofrece varios tipos de índices: `BTREE` (por defecto), `HASH` (mejorado en versiones recientes), `GIN` (para arrays/JSONB/text search), `GiST` (geometría/PostGIS), `BRIN` (tablas muy grandes con correlación de orden). Ejemplo:

   ```
   CREATE INDEX ON docs USING GIN (content gin_trgm_ops);
   ```

   Además, `ANALYZE`/estadísticas y el optimizador usan estas estadísticas; `EXPLAIN ANALYZE` muestra el plan real.
   - **VACUUM / autovacuum / bloat**: MVCC genera tuplas muertas; `VACUUM` (y `autovacuum`) las limpia. `VACUUM FULL` compacta, pero requiere bloqueo. Mantener autovacuum configurado es clave.

   - **Particionamiento**: PostgreSQL soporta particiones declarativas (`PARTITION BY RANGE/LIST/HASH`) y herencia histórica; permite consultas y mantenimiento más eficientes en tablas grandes.

   - **Replicación y WAL / PITR**: PostgreSQL usa WAL para durabilidad; soporta replicación física (streaming replication) y replicación lógica (publicación/suscripción). PITR (Point-In-Time Recovery) se realiza con WAL + base backups.

   - **Roles, permisos y autenticación**: Sistema de roles/grupos, privilegios por objeto (`GRANT`/`REVOKE`), autenticación configurable (`md5`, `scram-sha-256`, LDAP, Kerberos). Ejemplo:

   ```
   CREATE ROLE readonly NOINHERIT;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
   ```

   - **Tipos de dato avanzados**: `JSONB` (indexable y eficiente), `ARRAY`, `UUID`, `INET/CIDR` para redes, `hstore`, `range types`, geométricos y cualquier tipo definido por extensiones.

   - **Secuencias, SERIAL y IDENTITY**: PostgreSQL usa `SEQUENCE`. `SERIAL` es sintaxis azucarada; `IDENTITY` (SQL standard) está disponible desde versiones recientes.

   - **Vistas y vistas materializadas**: `VIEW` y `MATERIALIZED VIEW` (estas últimas requieren `REFRESH MATERIALIZED VIEW` para actualizar los datos cacheados).

   - **Triggers y funciones**: Soporta triggers `BEFORE/AFTER/INSTEAD OF` y funciones en `plpgsql` y otros lenguajes (PL/Python, PL/Perl, etc.). Ejemplo mínimo en `plpgsql`:

   ```
   CREATE FUNCTION log_update() RETURNS trigger AS $$
   BEGIN
      INSERT INTO audit(table_name, row_id, changed_at) VALUES (TG_TABLE_NAME, NEW.id, now());
      RETURN NEW;
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER trg_audit AFTER UPDATE ON productos
   FOR EACH ROW EXECUTE FUNCTION log_update();
   ```

   - **Foreign Data Wrappers (FDW)**: Permiten acceder a datos externos (otras Postgres, MySQL, CSV, APIs) como si fueran tablas remotas.

   - **Full-text search**: Integrado con tipos `tsvector`/`tsquery`, índices GIN optimizados, diccionarios y ranking (`ts_rank`).

   - **Extensiones**: PostgreSQL es extensible: `PostGIS`, `pg_trgm`, `pg_buffercache`, `timescaledb`, etc. Se instalan con `CREATE EXTENSION`.

   - **Tablespaces**: Permiten colocar objetos en diferentes ubicaciones físicas del disco.

   - **Row-Level Security (RLS)**: Políticas por fila para filtrar/permitir acceso a datos sensibles usando `CREATE POLICY`.

   - **Backups y restauración**: Herramientas comunes: `pg_dump`/`pg_restore` (lógica), `pg_basebackup` + WAL para copias físicas y PITR.

   - **Estadísticas de rendimiento**: `EXPLAIN ANALYZE`, `pg_stat_activity`, `pg_stat_statements` (extensión) y vistas del sistema ayudan a diagnosticar rendimiento.

   - **Conceptos no aplicables o que difieren**:
     - **MyISAM / motores de almacenamiento MySQL**: No aplican; PostgreSQL gestiona almacenamiento internamente y no usa motores alternativos por tabla.
     - **Clustered index (auto-implícito como en SQL Server)**: PostgreSQL no tiene un índice clustered automático; existe el comando `CLUSTER` que ordena físicamente una tabla por un índice pero no se mantiene en inserciones futuras.
     - **FILESTREAM (SQL Server)** y mecanismos específicos de otros SGBD no aplican; en PostgreSQL se usan `tablespaces` o almacenamiento externo/FDW.

   - **Recursos y comandos útiles**:
     - `EXPLAIN (ANALYZE, BUFFERS) <consulta>` — ver plan y consumo real.
     - `VACUUM`, `VACUUM FULL`, `ANALYZE` — mantenimiento.
     - `CREATE EXTENSION postgis;` — ejemplo de extensión.
     - `pg_dump -Fc -f backup.dump dbname` y `pg_restore -d dbname backup.dump` — backup/restore.

   Si quieres, puedo:
   - Añadir ejemplos psql más detallados para `EXPLAIN ANALYZE` y VACUUM.
   - Incluir recomendaciones de configuración de `postgresql.conf` para `autovacuum`, `shared_buffers` y `work_mem`.

## Summary

- **Naturaleza y propósito**
- **Transaccionalidad (BEGIN/COMMIT/ROLLBACK)**
- **MVCC y niveles de aislamiento**
- **Bloqueos y concurrencia**
- **Controles de integridad**
- **DDL / DML / DQL**
- **Índices y optimización**
- **Particionamiento**
- **Replicación y WAL / PITR**
- **Roles, permisos y autenticación**
  - **Row-Level Security (RLS)** (Nuevo)
- **Secuencias, SERIAL y IDENTITY**
- **Vistas y vistas materializadas**
- **Triggers y funciones**
- **Backups y restauración**
- **Estadísticas de rendimiento**
- **ACID**

- **Conceptos no aplicables o que difieren**:
  - **MyISAM / motores de almacenamiento MySQL**
  - **Clustered index (auto-implícito como en SQL Server)**
  - **FILESTREAM (SQL Server)**

- **Características y mejoras específicas de PostgreSQL (colocadas abajo porque representan avances o diferencias frente a MySQL)**
  - **Tipos de dato avanzados**
  - **VACUUM / autovacuum / bloat**
  - **Foreign Data Wrappers (FDW)**
  - **Full-text search**
  - **Extensiones**
  - **Tablespaces**
  - **Row-Level Security (RLS)** (^Mencionado arriba)

- **Recursos y comandos útiles**
