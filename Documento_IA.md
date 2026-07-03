# Entregable Obligatorio Bases de Datos II

## Objetivos de la Investigación

### Objetivo General

- Analizar la arquitectura interna del SGBD PostgreSQL a través de sus dimensiones fundamentales, contrastando sus soluciones de diseño con las de MySQL (InnoDB) mediante pruebas de rendimiento orientadas al control de concurrencia (MVCC) para determinar el impacto del almacenamiento físico en la degradación de la performance.

### Objetivos Específicos

- Mapear los componentes del motor de PostgreSQL en las dimensiones de Catálogo/Seguridad, Organización de Datos, Rutinas Almacenadas, Optimización, Concurrencia y Recuperación.
- Exponer las diferencias críticas entre la estrategia _Append-Only_ de PostgreSQL y la estrategia _In-Place + Undo Logs_ de MySQL.
- Diseñar y ejecutar un benchmark de estrés enfocado en operaciones de actualización masiva (`UPDATE`) concurrentes para medir la generación de _Bloat_ (filas muertas) en PostgreSQL y la saturación del _Undo Log_ en MySQL.
- Evaluar el comportamiento post-prueba de los procesos de mantenimiento de fondo (_Autovacuum_ en PostgreSQL y _Purge Threads_ en MySQL) en términos de consumo de recursos y recuperación de espacio.

---

## Marco Teórico (Conceptos Clave a Desarrollar)

- **SGBD Relacionales y ACID:** Principios de aislamiento (Isolation) y durabilidad (Durability) en entornos multiusuario.
- **Mecanismo MVCC (Multi-Version Concurrency Control):** Estrategias para evitar bloqueos de lectura/escritura mediante el manejo de instantáneas (_snapshots_).
- **Estructuras de Almacenamiento Físico:** Comparativa entre tablas organizadas como _Heap_ (PostgreSQL) frente a Tablas Organizadas por Índice o _Clustered Indexes_ (MySQL InnoDB).
- **Efecto Write Amplification y Bloat:** La problemática del engrosamiento de archivos de datos derivado de la persistencia de versiones muertas de filas en el mismo espacio físico.
- **Estrategia de Bitácoras de Recuperación:** Análisis del almacenamiento secuencial preventivo mediante WAL (_Write-Ahead Logging_) frente al esquema dual de _Redo Log_ y _Binlog_.

---

## Metodología

Para el desarrollo de este estudio se aplicará un enfoque experimental y comparativo dividido en las siguientes fases cronológicas:

1. **Fase 1: Configuración de Entornos Base:** Aislamiento.
   Instalar instancias limpias de PostgreSQL 16+ y MySQL 8.0+ en contenedores independientes con la misma asignación estricta de hardware (CPU, RAM y tipo de almacenamiento SSD) y configuraciones de memoria por defecto.

2. **Fase 2: Población de Datos:** Volumen Inicial.
   Crear una estructura de tabla idéntica en ambos motores e insertar un dataset controlado de 1,000,000 de registros iniciales para asegurar un punto de partida equitativo.

3. **Fase 3: Inyección de Estrés (Ejecución del Benchmark):** Concurrencia masiva.
   Ejecutar scripts automatizados de pruebas concurrentes (utilizando `pgbench`/`sysbench` o scripts multihilo dedicados) lanzando ráfagas continuas de sentencias `UPDATE` aleatorias durante un intervalo fijo de 5 minutos.

4. **Fase 4: Recolección de Métricas Internas:** Monitoreo de motores.
   Consultar los diccionarios de datos de control de ambos motores en tiempo real y diferido, abstrayendo variables como `n_dead_tup` (Postgres), `History list length` (MySQL) y las tasas de Transacciones por Segundo (TPS).

5. **Fase 5: Análisis Comparativo y Conclusiones:** Evaluación final.
   Contrastar las curvas de rendimiento y el crecimiento físico en disco de los archivos de base de datos para validar las hipótesis del marco teórico.

---

## Conceptos

### 1. Catálogo, Seguridad y Autorización

#### PostgreSQL

- **El Catálogo:** Se gestiona mediante el esquema especial `pg_catalog`. Toda la metadata (tablas, índices, columnas, funciones) reside en tablas del sistema SQL estándar como `pg_class`, `pg_attribute` o `pg_proc`. Puedes consultarlas directamente con `SELECT` como cualquier otra tabla.

```
SELECT *
  FROM information_schema.columns
  WHERE table_name = 'mvcc_bench';
```

#### Comparación con MySQL

- **Catálogo:** MySQL expone metadatos en `information_schema`, pero la gestión interna reside en la base de datos `mysql` y el diccionario de datos de InnoDB.

```
SELECT *
  FROM information_schema.columns
  WHERE table_name = 'mvcc_bench';
```

---

## Conceptos

### 2. Seguridad y Autorización

#### PostgreSQL

- **Autenticación:** Es perimetral y externa al motor SQL. Se administra en el archivo de configuración `pg_hba.conf` (Host-Based Authentication), donde se mapean combinaciones estrictas de: _Base de datos + Usuario + Dirección IP de origen + Método de cifrado_ (ej. SCRAM-SHA-256 o MD5).
- **Autorización y Roles:** Implementa un modelo unificado de **Roles** (`CREATE ROLE`). Un rol puede ser un usuario (si tiene permiso de `LOGIN`) o un grupo de seguridad. Soporta **RLS (Row-Level Security)** nativo, lo que permite crear políticas para que ciertos usuarios solo visualicen o modifiquen filas específicas de una tabla bajo condiciones dadas.

#### Comparación con MySQL

- **Seguridad:** MySQL identifica a los usuarios mediante la sintaxis `'usuario'@'host'`. Aunque ya tiene roles (desde la v8.0), carece de Seguridad a Nivel de Fila (RLS) nativa en su versión comunitaria; requiere delegar esa lógica a la aplicación o a vistas complejas.

---

### 3. Organización y Acceso a los Datos

#### PostgreSQL

- **Almacenamiento Físico (Heap):** Guarda los registros en archivos del sistema operativo organizados en **Páginas (Bloques) fijas de 8 KB**. Las tablas son estructuras _Heap_ (montículos): las filas se insertan en cualquier espacio libre disponible de cualquier página, sin ningún orden físico intrínseco.
- **Mecanismo TOAST:** Debido a que una página mide estrictamente 8 KB, PostgreSQL no puede almacenar filas gigantescas en el flujo normal. Para solucionarlo, usa **TOAST** (_The Oversized-Attribute Storage Technique_), que intercepta valores grandes (textos largos, blobs, JSONs), los comprime y los mueve de forma invisible a tablas anexas de desbordamiento.
- **Métodos de Acceso (Índices):** Los índices secundarios apuntan directamente al identificador físico de la fila en el Heap (**TID - Tuple ID**, compuesto por el número de página y la posición dentro de ella). Soporta una enorme variedad nativa: `B-Tree` (por defecto), `Hash` (igualdades), `GiST/SP-GiST` (datos geométricos/búsquedas de texto complejas), `GIN` (ideal para arreglos y documentos JSONB) y `BRIN` (para tablas masivas ordenadas por tiempo/secuencia).

#### Comparación con MySQL

- **Estructura:** MySQL utiliza **Tablas Organizadas por Índice (IOT)** mediante índices agrupados (_Clustered Indexes_). La tabla _es_ físicamente el índice de la Clave Primaria.
- **Índices:** Los índices secundarios de MySQL no apuntan a una dirección física de disco (TID), sino al valor de la Clave Primaria, lo que añade un paso extra de búsqueda (_lookup_). Sus páginas por defecto son de 16 KB y carece de la variedad de índices avanzados de Postgres (como GIN o BRIN).

---

### 4. Procedimientos Almacenados y Triggers

#### PostgreSQL

- **Lenguajes Procedimentales:** Es altamente extensible. Su lenguaje nativo es **PL/pgSQL**, pero gracias a su arquitectura modular permite instalar y programar lógica de base de datos usando PL/Python, PL/Perl, PL/V8 (JavaScript) o PL/Tcl de forma nativa.
- **Funciones vs. Procedimientos:** \* `CREATE FUNCTION`: Corren dentro de la transacción que las invoca. No pueden realizar operaciones de control transaccional (`COMMIT`/`ROLLBACK`) en su interior.
- `CREATE PROCEDURE`: Soportan control de transacciones embebido; puedes iniciar, confirmar o abortar transacciones dentro del propio código secuencial.

- **Triggers (Disparadores):** Se ejecutan llamando a una función especial previamente declarada (`RETURNS TRIGGER`). PostgreSQL soporta disparadores tanto a nivel de fila (`FOR EACH ROW` Permite acceder a los datos específicos de la fila usando las variables NEW y OLD) como a nivel de sentencia completa (`FOR EACH STATEMENT` no tiene acceso a los valores individuales NEW y OLD), permitiendo optimizar lógica masiva. También incluye triggers `INSTEAD OF` para interceptar escrituras en vistas no modificables de forma nativa.

#### Comparación con MySQL

- **Lenguaje:** MySQL usa la sintaxis estándar SQL/PSM y no permite alternar lenguajes de programación en sus rutinas.
- **Triggers:** El código se escribe directamente "ad-hoc" dentro del cuerpo del trigger (no requiere definir una función aparte). Además, MySQL **sólo soporta triggers a nivel de fila** y carece de opciones a nivel de sentencia o `INSTEAD OF`.

> [`FOR EACH STATEMENT`]
> Imagina que quieres llevar un registro (logs) cada vez que se realiza una actualización masiva en la tabla de empleados, sin importar si la consulta afectó a 1 o 1,000 registros.

---

### 5. Procesamiento y Optimización de Consultas

#### PostgreSQL

- **El Optimizador (CBO):** Utiliza un Optimizador Basado en Costos muy avanzado. Evalúa múltiples rutas de ejecución y les asigna un "costo estimado" basándose en las estadísticas recolectadas por el proceso `ANALYZE` (almacenadas en `pg_statistic`).
- **Algoritmos de Join y Ejecución:** Para resolver las consultas, dispone de tres algoritmos principales de Join: _Nested Loop_ (bucles anidados), _Hash Join_ (tablas hash en memoria) y _Merge Join_ (fusión de conjuntos previamente ordenados).
- **Paralelismo:** Cuenta con capacidades maduras de **Query Parallelism**. Ante consultas costosas (como agregaciones o escaneos masivos en data warehouses), el optimizador puede dividir automáticamente el trabajo entre múltiples hilos de CPU en paralelo.

#### Comparación con MySQL

- **Joins:** Tradicionalmente MySQL estuvo muy limitado al algoritmo _Nested Loop_. Aunque las versiones recientes añadieron _Hash Joins_, sigue careciendo de _Merge Joins_.
- **Rendimiento:** MySQL destaca por su velocidad y ligereza en consultas transaccionales extremadamente simples (OLTP de un solo hilo), pero su optimizador sufre y carece de la robustez analítica de Postgres cuando se enfrentan a consultas complejas, subconsultas masivas o reportería pesada (OLAP).

---

### 6. Concurrencia (MVCC)

#### PostgreSQL

- **Filosofía Append-Only:** PostgreSQL implementa MVCC escribiendo las nuevas versiones de los datos **directamente en la misma tabla**. Un `UPDATE` no sobrescribe el registro existente: marca la fila vieja como históricamente "muerta" e inserta una fila completamente nueva ("viva") en la primera página que tenga espacio.
- **Metadata de Fila (`xmin` / `xmax`):** Cada fila (_tuple_) posee campos ocultos. `xmin` guarda el ID de la transacción que la creó y `xmax` el ID de la transacción que la eliminó o modificó. Gracias a esto, los lectores nunca bloquean a los escritores y viceversa; cada uno ve un _snapshot_ (instantánea) consistente basado en su ID de transacción.
- **El Problema del Bloat y VACUUM:** Al acumular versiones viejas en las tablas, el espacio en disco se infla (**Bloat**). PostgreSQL depende críticamente del proceso **VACUUM** (usualmente automatizado por _Autovacuum_) para escanear las páginas, liberar el espacio ocupado por filas muertas para que pueda ser reutilizado, y actualizar las estadísticas del optimizador.

#### Comparación con MySQL

- **Modificación In-Place y Undo Logs:** MySQL (InnoDB) maneja el MVCC de forma inversa. Cuando ejecutas un `UPDATE`, el motor modifica la fila **directamente en su sitio físico original** de la tabla. La versión anterior (el pasado) se desplaza a una estructura de archivos totalmente independiente llamada **Undo Log**.
- **Ventaja/Desventaja:** MySQL no sufre de _Bloat_ en las tablas principales ni requiere de un proceso equivalente a `VACUUM`. Sin embargo, bajo un estrés masivo de escrituras concurrentes, la cola de deshacer del Undo Log (_History List Length_) puede crecer descontroladamente, saturando el rendimiento del hilo de purga (_Purge Thread_).

> ##### XMIN / XMAX:
>
> - Ventajas
>   - **Auditoría de bajo costo:** Permiten rastrear qué transacción creó o modificó un registro sin necesidad de agregar columnas dedicadas, ahorrando espacio.
>   - **Control de concurrencia optimista:** Se pueden usar xmin y xmax en sentencias UPDATE para evitar condiciones de carrera (ej. vender un producto si nadie más lo modificó desde que fue leído).
>   - **Diferenciación en operaciones Upsert:** Al usar INSERT ... ON CONFLICT DO UPDATE, evaluar xmax permite detectar fácilmente si una fila acaba de ser insertada (xmax = 0) o actualizada (xmax > 0).
> - Desventajas:
>   - **Riesgo de ciclo de los IDs de Transacción:** Los identificadores de transacciones (XID) son finitos (32 bits, unos 4.000 millones). Si no se ejecuta correctamente el proceso de mantenimiento, el sistema se detendrá para prevenir la pérdida de datos (daño por "wraparound").
>   - **Sin garantías de tiempo real:** Son identificadores monótonos crecientes de transacciones, no marcas de tiempo (timestamps). No indican directamente cuándo ocurrió un cambio.
>   - **Degradación del planificador de consultas:** Las consultas que filtran grandes volúmenes de datos basándose estrictamente en xmin o xmax suelen generar lecturas secuenciales costosas, ya que PostgreSQL carece de estadísticas de distribución para estos campos internos.

---

### 7. Recuperación y Tolerancia a Fallos

#### PostgreSQL

- **Estrategia WAL (Write-Ahead Logging):** PostgreSQL garantiza la durabilidad (la propiedad 'D' de ACID) obligando al sistema a escribir cualquier cambio estructural o de datos en un registro secuencial e indexado en disco llamado **WAL**, _antes_ de que las páginas modificadas en la memoria RAM (`shared_buffers`) se guarden en los archivos de datos definitivos.
- **Crash Recovery:** Si el servidor experimenta un corte de energía, al reiniciar, el motor lee el WAL desde el último punto seguro y aplica un proceso de _Redo_ (rehacer) para restaurar la consistencia exacta de todas las transacciones confirmadas.
- **Checkpoints:** Son operaciones periódicas controladas por el proceso _Checkpointer_. Su función es volcar de manera ordenada todas las páginas "sucias" de la memoria RAM hacia el almacenamiento físico definitivo. Esto permite recortar el tamaño del WAL, limitando el tiempo que tardaría el motor en recuperarse tras un fallo.

#### Comparación con MySQL

- **Arquitectura de Logs:** En lugar de centralizar todo en un único flujo como el WAL de Postgres, MySQL divide su estrategia de recuperación en dos componentes:

1. **Redo Log:** Un archivo circular exclusivo del motor InnoDB encargado puramente del _Crash Recovery_ físico ante apagones.
2. **Binlog (Binary Log):** Un registro de transacciones a nivel lógico del servidor MySQL (independiente del motor), indispensable para realizar la replicación entre nodos y para la recuperación hacia un punto específico en el tiempo (PITR - Point-In-Time Recovery).

---

## Fuentes Bibliográficas y Bibliografía Sugerida

### Documentación Oficial (Fuentes Primarias)

- **The PostgreSQL Global Development Group.** _PostgreSQL Documentation (Chapter 13: Concurrency Control & Chapter 30: Reliability and the WAL)_. Documentación oficial de postgresql.org.
- **Oracle Corporation.** _MySQL Reference Manual (Chapter 15: The InnoDB Storage Engine)_. Documentación oficial de dev.mysql.com.

### Libros de Texto y Referencias

- **Silberschatz, A., Korth, H. F., & Sudarshan, S.** (2019). _Database System Concepts_ (7th ed.). McGraw-Hill. _(Ideal para el sustento teórico de MVCC, Checkpoints, WAL y costos de optimización)_.
- **Riggs, S., & Cordeiro, G.** (2021). _PostgreSQL 14 Administration Cookbook_. Packt Publishing. _(Guía práctica para el análisis de catálogos internos, pg_stat_user_tables y sintonización de Autovacuum)_.
- **Van Steen, M., & Tanenbaum, A. S.** (2017). _Distributed Systems_ (3rd ed.). _(Útil si extiendes el benchmark hacia arquitecturas replicadas usando el Binlog de MySQL o el Streaming Replication de Postgres)_.
- **Schwartz, B.** (2022). _High Performance MySQL: Optimization, Backups, and Replication_ (4th ed.). O'Reilly Media. _(La referencia definitiva para comprender a fondo los entresijos de los Undo Logs de InnoDB y la purga de páginas)_.

### Sitions web

- "for each statement" tipo de Trigger
  - https://www.datacamp.com/doc/postgresql/statement-level-triggers

- xmin / xmax
  - https://medium.com/@ysrgozudeli/unveiling-postgresqls-hidden-system-columns-ctid-xmin-xmax-and-more-9bcc7c25c55a
  - https://www.postgresql.org/message-id/MWHPR2201MB15651B320A20EB2F1E6F4A0C8C5E0%40MWHPR2201MB1565.namprd22.prod.outlook.com
  - https://stackoverflow.com/questions/39058213/differentiate-inserted-and-updated-rows-in-upsert-using-system-columns
  - https://www.highgo.ca/2020/05/20/phoney-table-columns-in-postgresql/
  - https://www.linkedin.com/posts/chetansj27_in-postgres-every-single-row-secretly-carries-share-7417127920445386752-qvnH/
  - https://stackoverflow.com/questions/76518779/xmin-queries-in-postgres-not-using-parallel-sequential-scans

---

## Citas Clave

> "PostgreSQL prioriza la inmutabilidad de los datos en disco bajo el diseño append-only; un enfoque elegante que simplifica la recuperación ante fallos y las lecturas concurrentes, pero que transfiere el costo operativo al recolector de basura (VACUUM)."

> "InnoDB (MySQL) intercambia el costo de limpiar el almacenamiento principal por una estructura de punteros hacia el pasado (Undo Logs). Esto mantiene las tablas compactas, pero delega una inmensa presión de entrada/salida (I/O) al subsistema de logs bajo escenarios extremos de escritura."

---
