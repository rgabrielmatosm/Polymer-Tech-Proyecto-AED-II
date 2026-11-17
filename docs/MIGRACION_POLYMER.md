# Migración de HexaOrders v6 a POLYMER

Esta guía es para quien ya tenía **HexaOrders v6** funcionando en Docker y pasa a **POLYMER**. La
migración **no borra datos**: pedidos, usuarios, productos, métricas y dashboards se conservan. La
decisión técnica está en la [ADR 0017](adr/0017-polymer-technical-identity-and-safe-volume-migration.md).

## 1. Por qué fallaba `start` al descomprimir el ZIP en otra carpeta

| Síntoma | Causa | Qué NO hacer |
| --- | --- | --- |
| «Existe el volumen hexaorders_postgres_data pero falta secrets\db_password.txt» (y lo mismo con `hexaorders_grafana_data` y `grafana_password.txt`) | El ZIP **no incluye** `secrets\`: las contraseñas nunca se distribuyen. Tus datos siguen en los volúmenes de Docker, creados con las contraseñas de la carpeta `secrets\` de tu instalación anterior. Sin ellas, PostgreSQL y Grafana no dejarían entrar a la aplicación | No ejecutes `docker compose down -v`, no borres volúmenes y no generes contraseñas nuevas: perderías el acceso a tus datos |

## 2. Pasos en Windows (PowerShell)

1. Descomprime POLYMER **junto a** la carpeta anterior, por ejemplo:

   ```
   C:\Users\TU_USUARIO\Downloads\HexaOrders-v6\...      ← la instalación anterior (con su carpeta secrets\)
   C:\Users\TU_USUARIO\Downloads\POLYMER\...            ← la carpeta nueva
   ```

2. Abre Docker Desktop y espera a que indique **Engine running**.
3. En PowerShell, dentro de la carpeta nueva:

   ```powershell
   .\polymer.cmd start
   ```

   El script hace lo siguiente:

   - **Detecta los datos** de HexaOrders (volúmenes `hexaorders_*`) y que faltan sus contraseñas.
   - **Busca la carpeta `secrets\` anterior** en las carpetas vecinas y te muestra su ruta, nunca su contenido.
   - Si escribes `SI`, **copia solo los archivos que faltan**.
   - **Detiene, sin borrar,** los contenedores de HexaOrders, que usan los mismos puertos.
   - **Copia cada volumen** `hexaorders_*` a `polymer_*` y verifica que todos los archivos sean idénticos (SHA-256). Los volúmenes originales **no se tocan**: quedan como copia de seguridad. El registro queda en `polymer-migration.log`.
   - **Construye y arranca los 13 contenedores**. PostgreSQL aplica la migración V9, que no es destructiva.

4. **Si la carpeta anterior está en otro sitio**, indícala:

   ```powershell
   .\polymer.cmd import-secrets -SecretsFrom "C:\ruta\de\HexaOrders-v6"
   ```

   ```powershell
   .\polymer.cmd start
   ```

   Si borraste la carpeta anterior pero guardaste sus archivos, cópialos a mano en `secrets\`: `db_password.txt`, `grafana_password.txt`, `demo_password.txt` y `rabbitmq_password.txt`.
5. Comprueba que todo esté en marcha:

   ```powershell
   .\polymer.cmd status
   ```

   Deben aparecer 13 contenedores `polymer-…` en estado *running* / *healthy*. Abre http://localhost:8080 e inicia sesión con tus cuentas y la contraseña de siempre (`secrets\demo_password.txt`).

**Si ya no tienes ninguna copia de `db_password.txt`**, `.\polymer.cmd repair-db-password` cambia la contraseña de PostgreSQL al valor del archivo nuevo **sin borrar datos**, previa confirmación. Para Grafana, la contraseña del usuario `admin` puede cambiarse desde su propia interfaz.

### Desde versiones anteriores a la v6 (v4 o v5)

El procedimiento es el mismo: los volúmenes también se llaman `hexaorders_*`. Al arrancar, Flyway aplica **una sola vez** las migraciones pendientes (V6 y V7: catálogo tecnológico, promociones, carrito y checkout; V8 y V9: identidad POLYMER) y conserva usuarios, contraseñas y pedidos.

### Comprobación completa después de migrar (opcional)

```powershell
.\polymer.cmd smoke
```

Ejecuta las pruebas HTTP contra tu entorno en marcha: pedidos, roles, tienda y, en modo completo, Redis, RabbitMQ, Mailpit, Loki, Tempo y Grafana. Requiere Python.

Para el personal: la documentación técnica y el laboratorio están en **Monitoreo → Documentación técnica**, con las cuentas `observador` o `admin`.

## 3. Volver a HexaOrders v6 (si lo necesitas)

Los volúmenes `hexaorders_*` siguen intactos, en el estado en que estaban antes de copiarlos.

1. Detén POLYMER:

   ```powershell
   .\polymer.cmd stop
   ```

2. En la carpeta de la v6, arranca de nuevo:

   ```powershell
   .\hexaorders.cmd start
   ```

Los cambios hechos después en POLYMER (volúmenes `polymer_*`) no se ven en la v6.

## 4. Liberar espacio (opcional y manual)

La migración ocupa el doble de disco mientras se conservan los originales. Cuando hayas comprobado
durante unos días que POLYMER tiene todos tus datos, puedes borrar los volúmenes antiguos. Este paso
**es irreversible** y ningún script lo hace por ti:

```powershell
docker volume ls --filter name=hexaorders_
```

```powershell
docker volume rm hexaorders_postgres_data hexaorders_prometheus_data hexaorders_grafana_data hexaorders_redis_data hexaorders_rabbitmq_data hexaorders_loki_data hexaorders_tempo_data hexaorders_alloy_data
```

## 5. Identificadores heredados que se conservan a propósito

| Identificador | Dónde | Por qué no se renombra |
| --- | --- | --- |
| Migraciones `V1`–`V8` (comentarios y datos con el nombre anterior) y `tools/catalog_v6_data.py` / `generate_catalog.py`, que generan V7 | `db/migration/` | Flyway guarda la suma de comprobación de cada migración aplicada; editarlas impediría arrancar sobre una base existente. V8 y V9 renombran los **datos** visibles |
| Volúmenes `hexaorders_*` | Docker | Copia de seguridad de la migración (sección 4) |
| Métricas `hexaorders_*` anteriores a la migración | Prometheus (volumen) | Es historia guardada; las métricas nuevas se llaman `polymer_*` |
| Nombre del repositorio de GitHub | GitHub | Se cambia desde la configuración del repositorio, no desde el código |

### RabbitMQ: renombrado con migración automática (v12)

Hasta la v11, RabbitMQ conservaba el usuario `hexaorders` y el exchange y las colas `hexaorders.*`, porque viven
dentro de su volumen. Desde la v12 todo se llama POLYMER y la migración ocurre sola al arrancar, sin perder nada:

| Qué | Antes | Ahora | Cómo se migra |
| --- | --- | --- | --- |
| Usuario | `hexaorders` | `polymer` | `infra/rabbitmq/polymer-entrypoint.sh` crea `polymer` con **la misma contraseña** de `secrets/rabbitmq_password.txt` (no cambia ninguna credencial). Borra `hexaorders` solo después de comprobar que `polymer` se autentica. El healthcheck no da a RabbitMQ por sano hasta que `polymer` existe |
| Exchange | `hexaorders.events` (y `.dlx`) | `polymer.events` (y `.dlx`) | order-api declara los nuevos y `LegacyTopologyMigration` borra los viejos |
| Colas | `hexaorders.notifications` (y `.dlq`) | `polymer.notifications` (y `.dlq`) | `LegacyTopologyMigration` traslada cada mensaje pendiente **directamente a la cola nueva** (sin depender de su clave de enrutamiento) con confirmación del broker y solo entonces lo confirma en la cola vieja (si algo falla, vuelve a la cola vieja y se reintenta). Las colas viejas se borran cuando quedan vacías |

El job del CI `migrate-from-v6` lo comprueba desde una instalación v6 real: usuario `polymer` presente y `hexaorders`
eliminado, colas `polymer.*` presentes y ninguna `hexaorders.*`.

La guía de Windows de la versión anterior se conserva en [`historial/WINDOWS_DOCKER_GUIDE-hexaorders-v6.md`](historial/WINDOWS_DOCKER_GUIDE-hexaorders-v6.md).

Todo lo demás usa POLYMER: paquete `com.polymer`, proyecto de Compose `polymer`, imágenes `polymer/*`,
métricas, dashboards, alertas, etiquetas de logs, configuración, caché, claves del navegador, scripts,
documentación e interfaz. El cambio se hizo con `tools/migration/rename_to_polymer.py`, que documenta
las reglas y las excepciones.
