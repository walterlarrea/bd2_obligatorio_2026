Aquí tienes la unificación completa de las dimensiones arquitectónicas de **PostgreSQL**, estructurada para tu informe o apuntes de estudio. Cada concepto pone el foco principal en el funcionamiento de Postgres y añade un bloque de referencia comparativa con **MySQL (InnoDB)** para que puedas mapearlo directamente con lo que ya conoces.

---

## 📁 1. Catálogo, Seguridad y Autorización

### PostgreSQL (Enfoque Principal)

- **El Catálogo:** Se gestiona mediante el esquema especial `pg_catalog`. Toda la metadata (tablas, índices, columnas, funciones) reside en tablas del sistema SQL estándar como `pg_class`, `pg_attribute` o `pg_proc`. Puedes consultarlas directamente con `SELECT` como cualquier otra tabla.
- **Autenticación:** Es perimetral y externa al motor SQL. Se administra en el archivo de configuración `pg_hba.conf` (Host-Based Authentication), donde se mapean combinaciones estrictas de: _Base de datos + Usuario + Dirección IP de origen + Método de cifrado_ (ej. SCRAM-SHA-256 o MD5).
- **Autorización y Roles:** Implementa un modelo unificado de **Roles** (`CREATE ROLE`). Un rol puede ser un usuario (si tiene permiso de `LOGIN`) o un grupo de seguridad. Soporta **RLS (Row-Level Security)** nativo, lo que permite crear políticas para que ciertos usuarios solo visualicen o modifiquen filas específicas de una tabla bajo condiciones dadas.

### 🔍 Mapeo de referencia con MySQL

- **Catálogo:** MySQL expone metadatos en `information_schema`, pero la gestión interna reside en la base de datos `mysql` y el diccionario de datos de InnoDB.
- **Seguridad:** MySQL identifica a los usuarios mediante la sintaxis `'usuario'@'host'`. Aunque ya tiene roles (desde la v8.0), carece de Seguridad a Nivel de Fila (RLS) nativa en su versión comunitaria; requiere delegar esa lógica a la aplicación o a vistas complejas.

---

## 💾 2. Organización y Acceso a los Datos

### PostgreSQL (Enfoque Principal)

- **Almacenamiento Físico (Heap):** Guarda los registros en archivos del sistema operativo organizados en **Páginas (Bloques) fijas de 8 KB**. Las tablas son estructuras _Heap_ (montículos): las filas se insertan en cualquier espacio libre disponible de cualquier página, sin ningún orden físico intrínseco.
- **Mecanismo TOAST:** Debido a que una página mide estrictamente 8 KB, PostgreSQL no puede almacenar filas gigantescas en el flujo normal. Para solucionarlo, usa **TOAST** (_The Oversized-Attribute Storage Technique_), que intercepta valores grandes (textos largos, blobs, JSONs), los comprime y los mueve de forma invisible a tablas anexas de desbordamiento.
- **Métodos de Acceso (Índices):** Los índices secundarios apuntan directamente al identificador físico de la fila en el Heap (**TID - Tuple ID**, compuesto por el número de página y la posición dentro de ella). Soporta una enorme variedad nativa: `B-Tree` (por defecto), `Hash` (igualdades), `GiST/SP-GiST` (datos geométricos/búsquedas de texto complejas), `GIN` (ideal para arreglos y documentos JSONB) y `BRIN` (para tablas masivas ordenadas por tiempo/secuencia).

### 🔍 Mapeo de referencia con MySQL

- **Estructura:** MySQL utiliza **Tablas Organizadas por Índice (IOT)** mediante índices agrupados (_Clustered Indexes_). La tabla _es_ físicamente el índice de la Clave Primaria.
- **Índices:** Los índices secundarios de MySQL no apuntan a una dirección física de disco (TID), sino al valor de la Clave Primaria, lo que añade un paso extra de búsqueda (_lookup_). Sus páginas por defecto son de 16 KB y carece de la variedad de índices avanzados de Postgres (como GIN o BRIN).

---

## ⚙️ 3. Procedimientos Almacenados y Triggers

### PostgreSQL (Enfoque Principal)

- **Lenguajes Procedimentales:** Es altamente extensible. Su lenguaje nativo es **PL/pgSQL**, pero gracias a su arquitectura modular permite instalar y programar lógica de base de datos usando PL/Python, PL/Perl, PL/V8 (JavaScript) o PL/Tcl de forma nativa.
- **Funciones vs. Procedimientos:** \* `CREATE FUNCTION`: Corren dentro de la transacción que las invoca. No pueden realizar operaciones de control transaccional (`COMMIT`/`ROLLBACK`) en su interior.
- `CREATE PROCEDURE`: Soportan control de transacciones embebido; puedes iniciar, confirmar o abortar transacciones dentro del propio código secuencial.

- **Triggers (Disparadores):** Se ejecutan llamando a una función especial previamente declarada (`RETURNS TRIGGER`). PostgreSQL soporta disparadores tanto a nivel de fila (`FOR EACH ROW`) como a nivel de sentencia completa (`FOR EACH STATEMENT`), permitiendo optimizar lógica masiva. También incluye triggers `INSTEAD OF` para interceptar escrituras en vistas no modificables de forma nativa.

### 🔍 Mapeo de referencia con MySQL

- **Lenguaje:** MySQL usa la sintaxis estándar SQL/PSM y no permite alternar lenguajes de programación en sus rutinas.
- **Triggers:** El código se escribe directamente "ad-hoc" dentro del cuerpo del trigger (no requiere definir una función aparte). Además, MySQL **sólo soporta triggers a nivel de fila** y carece de opciones a nivel de sentencia o `INSTEAD OF`.

---

## 🔍 4. Procesamiento y Optimización de Consultas

### PostgreSQL (Enfoque Principal)

- **El Optimizador (CBO):** Utiliza un Optimizador Basado en Costos muy avanzado. Evalúa múltiples rutas de ejecución y les asigna un "costo estimado" basándose en las estadísticas recolectadas por el proceso `ANALYZE` (almacenadas en `pg_statistic`).
- **Algoritmos de Join y Ejecución:** Para resolver las consultas, dispone de tres algoritmos principales de Join: _Nested Loop_ (bucles anidados), _Hash Join_ (tablas hash en memoria) y _Merge Join_ (fusión de conjuntos previamente ordenados).
- **Paralelismo:** Cuenta con capacidades maduras de **Query Parallelism**. Ante consultas costosas (como agregaciones o escaneos masivos en data warehouses), el optimizador puede dividir automáticamente el trabajo entre múltiples hilos de CPU en paralelo.

### 🔍 Mapeo de referencia con MySQL

- **Joins:** Tradicionalmente MySQL estuvo muy limitado al algoritmo _Nested Loop_. Aunque las versiones recientes añadieron _Hash Joins_, sigue careciendo de _Merge Joins_.
- **Rendimiento:** MySQL destaca por su velocidad y ligereza en consultas transaccionales extremadamente simples (OLTP de un solo hilo), pero su optimizador sufre y carece de la robustez analítica de Postgres cuando se enfrentan a consultas complejas, subconsultas masivas o reportería pesada (OLAP).

---

## 🔄 5. Concurrencia (MVCC)

### PostgreSQL (Enfoque Principal)

- **Filosofía Append-Only:** PostgreSQL implementa MVCC escribiendo las nuevas versiones de los datos **directamente en la misma tabla**. Un `UPDATE` no sobrescribe el registro existente: marca la fila vieja como históricamente "muerta" e inserta una fila completamente nueva ("viva") en la primera página que tenga espacio.
- **Metadata de Fila (`xmin` / `xmax`):** Cada fila (_tuple_) posee campos ocultos. `xmin` guarda el ID de la transacción que la creó y `xmax` el ID de la transacción que la eliminó o modificó. Gracias a esto, los lectores nunca bloquean a los escritores y viceversa; cada uno ve un _snapshot_ (instantánea) consistente basado en su ID de transacción.
- **El Problema del Bloat y VACUUM:** Al acumular versiones viejas en las tablas, el espacio en disco se infla (**Bloat**). PostgreSQL depende críticamente del proceso **VACUUM** (usualmente automatizado por _Autovacuum_) para escanear las páginas, liberar el espacio ocupado por filas muertas para que pueda ser reutilizado, y actualizar las estadísticas del optimizador.

### 🔍 Mapeo de referencia con MySQL

- **Modificación In-Place y Undo Logs:** MySQL (InnoDB) maneja el MVCC de forma inversa. Cuando ejecutas un `UPDATE`, el motor modifica la fila **directamente en su sitio físico original** de la tabla. La versión anterior (el pasado) se desplaza a una estructura de archivos totalmente independiente llamada **Undo Log**.
- **Ventaja/Desventaja:** MySQL no sufre de _Bloat_ en las tablas principales ni requiere de un proceso equivalente a `VACUUM`. Sin embargo, bajo un estrés masivo de escrituras concurrentes, la cola de deshacer del Undo Log (_History List Length_) puede crecer descontroladamente, saturando el rendimiento del hilo de purga (_Purge Thread_).

---

## 🛡️ 6. Recuperación y Tolerancia a Fallos

### PostgreSQL (Enfoque Principal)

- **Estrategia WAL (Write-Ahead Logging):** PostgreSQL garantiza la durabilidad (la propiedad 'D' de ACID) obligando al sistema a escribir cualquier cambio estructural o de datos en un registro secuencial e indexado en disco llamado **WAL**, _antes_ de que las páginas modificadas en la memoria RAM (`shared_buffers`) se guarden en los archivos de datos definitivos.
- **Crash Recovery:** Si el servidor experimenta un corte de energía, al reiniciar, el motor lee el WAL desde el último punto seguro y aplica un proceso de _Redo_ (rehacer) para restaurar la consistencia exacta de todas las transacciones confirmadas.
- **Checkpoints:** Son operaciones periódicas controladas por el proceso _Checkpointer_. Su función es volcar de manera ordenada todas las páginas "sucias" de la memoria RAM hacia el almacenamiento físico definitivo. Esto permite recortar el tamaño del WAL, limitando el tiempo que tardaría el motor en recuperarse tras un fallo.

### 🔍 Mapeo de referencia con MySQL

- **Arquitectura de Logs:** En lugar de centralizar todo en un único flujo como el WAL de Postgres, MySQL divide su estrategia de recuperación en dos componentes:

1. **Redo Log:** Un archivo circular exclusivo del motor InnoDB encargado puramente del _Crash Recovery_ físico ante apagones.
2. **Binlog (Binary Log):** Un registro de transacciones a nivel lógico del servidor MySQL (independiente del motor), indispensable para realizar la replicación entre nodos y para la recuperación hacia un punto específico en el tiempo (PITR - Point-In-Time Recovery).
