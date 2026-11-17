"""English text for the POLYMER diagrams (generate_diagrams.py and generate_aws_diagram.py with --lang en).

Each diagram label is translated LINE BY LINE (lines separated by a newline or <br>): a line found in EN is
replaced; technical lines (class names, ports, table columns) stay as they are. check() fails if any Spanish is
left, so a new Spanish label cannot slip into the English files unnoticed.
"""
from __future__ import annotations

import re

EN = {
    # ---------------------------------------------------------------- page 1: hexagonal architecture
    '1 · Arquitectura hexagonal': '1 · Hexagonal architecture',
    'POLYMER · Arquitectura hexagonal (puertos y adaptadores, Alistair Cockburn 2005)':
        'POLYMER · Hexagonal architecture (ports and adapters, Alistair Cockburn 2005)',
    'Las dependencias del código apuntan HACIA DENTRO. El núcleo no conoce Spring, SQL, Redis, RabbitMQ ni HTTP: solo interfaces (puertos).':
        'Code dependencies point INWARD. The core knows nothing about Spring, SQL, Redis, RabbitMQ or HTTP: only interfaces (ports).',
    'Cliente · Operador · Logística': 'Customer · Operator · Logistics',
    'Administrador · Observador': 'Administrator · Observer',
    '(navegador, HTTP)': '(browser, HTTP)',
    'ADAPTADORES DE ENTRADA  (adapter/in)': 'INPUT ADAPTERS  (adapter/in)',
    'Controladores REST (adapter/in/web)': 'REST controllers (adapter/in/web)',
    'Oyente de RabbitMQ': 'RabbitMQ listener',
    'Planificador (cada 2 s)': 'Scheduler (every 2 s)',
    'NÚCLEO  (application + domain)  ·  Java puro, sin frameworks': 'CORE  (application + domain)  ·  plain Java, no frameworks',
    'CASOS DE USO  (application/service · 17)': 'USE CASES  (application/service · 17)',
    'PUERTOS DE ENTRADA': 'INPUT PORTS',
    'DOMINIO  (domain/)': 'DOMAIN  (domain/)',
    'Order · OrderStatus (≥70 → revisión)': 'Order · OrderStatus (≥70 → review)',
    'TransitionPolicy (grafo de estados)': 'TransitionPolicy (state graph)',
    'Delivery (choque de intervalos)': 'Delivery (interval overlap)',
    'VerificationPolicy (6 dígitos, 10 min)': 'VerificationPolicy (6 digits, 10 min)',
    'BusinessHours · PeruHolidays (Pascua)': 'BusinessHours · PeruHolidays (Easter)',
    'PUERTOS DE SALIDA': 'OUTPUT PORTS',
    'Verificado por ArchUnit (8 reglas, HexagonalArchitectureTest): si el núcleo importa una tecnología, la imagen Docker no se construye':
        'Verified by ArchUnit (8 rules, HexagonalArchitectureTest): if the core imports a technology, the Docker image does not build',
    'ADAPTADORES DE SALIDA  (adapter/out)': 'OUTPUT ADAPTERS  (adapter/out)',
    '(o fixed/FixedRiskAssessmentAdapter)': '(or fixed/FixedRiskAssessmentAdapter)',
    'Pasarelas de PRUEBA': 'TEST payment gateways',
    'Prometheus (lectura)': 'Prometheus (read)',
    'RAÍZ DE COMPOSICIÓN  (config/)  ·  HexagonalConfiguration · IntegrationConfiguration · PlatformConfiguration · SecurityConfiguration':
        'COMPOSITION ROOT  (config/)  ·  HexagonalConfiguration · IntegrationConfiguration · PlatformConfiguration · SecurityConfiguration',
    'Único lugar que conoce ambos lados: elige el adaptador (p. ej. polymer.risk.adapter = http | fixed)':
        'The only place that knows both sides: it picks the adapter (e.g. polymer.risk.adapter = http | fixed)',
    'llama a': 'calls',
    'implementa': 'implements',
    'usa': 'uses',
    # ---------------------------------------------------------------- page 2: containers
    '2 · Contenedores Docker': '2 · Docker containers',
    'POLYMER · 13 contenedores de Docker Compose (enlaces solo en 127.0.0.1)': 'POLYMER · 13 Docker Compose containers (links only on 127.0.0.1)',
    'ENTRADA': 'ENTRY',
    'NEGOCIO (2 servicios)': 'BUSINESS (2 services)',
    'DATOS': 'DATA',
    'MENSAJERÍA': 'MESSAGING',
    'OBSERVABILIDAD': 'OBSERVABILITY',
    'Navegador': 'Browser',
    '(cliente, personal)': '(customer, staff)',
    ':8080 → tienda y /api': ':8080 → store and /api',
    'NÚCLEO HEXAGONAL': 'HEXAGONAL CORE',
    ':8081 (directo) · gestión :9090': ':8081 (direct) · management :9090',
    'microservicio hexagonal': 'hexagonal microservice',
    '25 tablas (Flyway V1…V13)': '25 tables (Flyway V1…V13)',
    'fuente de verdad · privado': 'source of truth · private',
    'caché catálogo (TTL 60 s)': 'catalog cache (TTL 60 s)',
    'LRU 48 MB · privado': 'LRU 48 MB · private',
    'cola notifications + DLQ': 'notifications queue + DLQ',
    'consola :15672': 'console :15672',
    'SMTP de pruebas': 'test SMTP server',
    'Gmail (opcional)': 'Gmail (optional)',
    '(«Continuar con Google»)': '(«Continue with Google»)',
    'lee cada 10 s: order-api :9090,': 'scrapes every 10 s: order-api :9090,',
    '9 reglas de alerta': '9 alert rules',
    'trazas': 'traces',
    'lee logs de Docker → Loki': 'reads Docker logs → Loki',
    'Redes: edge · gateway · data (solo order-api ↔ PostgreSQL) · compute · cache · messaging · telemetry · egress (salida a Internet solo para order-api)':
        'Networks: edge · gateway · data (only order-api ↔ PostgreSQL) · compute · cache · messaging · telemetry · egress (Internet access only for order-api)',
    'POST /score (HTTP síncrono)': 'POST /score (synchronous HTTP)',
    'JDBC (transacciones)': 'JDBC (transactions)',
    'GET/SET con TTL': 'GET/SET with TTL',
    'publica (outbox) · consume (idempotente)': 'publishes (outbox) · consumes (idempotent)',
    'SMTP (si se configura)': 'SMTP (if configured)',
    # ---------------------------------------------------------------- page 3: data model
    '3 · Modelo de datos (E-R)': '3 · Data model (E-R)',
    '3 · Entidad-relación (PostgreSQL · contenedor db)': '3 · Entity-relationship (PostgreSQL · db container)',
    'POLYMER · Modelo de datos en PostgreSQL (25 tablas, migraciones Flyway V1…V13)':
        'POLYMER · PostgreSQL data model (25 tables, Flyway migrations V1…V13)',
    'expires_at (30 días)': 'expires_at (30 days)',
    'parent_id FK (árbol)': 'parent_id FK (tree)',
    'Mensajería: outbox_published (eventos publicados) y processed_events (eventos ya consumidos: idempotencia). Las FK apuntan del hijo (N) al padre (1). order_lines.promotion_id → promotions (promoción aplicada).':
        'Messaging: outbox_published (published events) and processed_events (already consumed events: idempotency). FKs point from child (N) to parent (1). order_lines.promotion_id → promotions (applied promotion).',
    # ---------------------------------------------------------------- AWS page
    '1 · AWS · POLYMER desplegado (Terraform)': '1 · AWS · POLYMER deployed (Terraform)',
    '<b style="font-size:26px">POLYMER en Amazon Web Services</b>': '<b style="font-size:26px">POLYMER on Amazon Web Services</b>',
    '<span style="font-size:15px">Una instancia EC2 con Docker Compose (13 contenedores) detrás de Caddy (HTTPS), creada con Terraform · <b>https://18-189-49-9.sslip.io</b></span>':
        '<span style="font-size:15px">One EC2 instance running Docker Compose (13 containers) behind Caddy (HTTPS), created with Terraform · <b>https://18-189-49-9.sslip.io</b></span>',
    'Laptop del administrador (Windows)': 'Administrator laptop (Windows)',
    '<i>terraform.tfstate</i> local (privado)': 'local <i>terraform.tfstate</i> (private)',
    'usuario IAM terraform-admin': 'IAM user terraform-admin',
    '<b>Navegador por el túnel</b>': '<b>Browser through the tunnel</b>',
    'misma imagen, datos propios': 'same image, its own data',
    '<i>Las claves de AWS y el JSON de Google': '<i>The AWS keys and the Google JSON',
    'se quedan en este equipo.</i>': 'stay on this computer.</i>',
    'Clientes de la tienda': 'Store customers',
    '(navegador o móvil)': '(browser or phone)',
    'Cuenta del proyecto «Sunlit Server - Sagabella» · plan gratuito (créditos) · la SCP de la organización solo permite us-east-2':
        'Project account «Sunlit Server - Sagabella» · free plan (credits) · the organization SCP only allows us-east-2',
    'consola y túneles sin SSH': 'console and tunnels without SSH',
    '<b>IAM</b> · rol polymer-ec2-*': '<b>IAM</b> · role polymer-ec2-*',
    '+ perfil de instancia': '+ instance profile',
    'ZIP del código sin secretos': 'source ZIP without secrets',
    'privado · cifrado AES256': 'private · AES256 encrypted',
    'SecureString (clave aws/ssm)': 'SecureString (aws/ssm key)',
    '<b>AWS Budgets</b> (opcional)': '<b>AWS Budgets</b> (optional)',
    'alerta de consumo de créditos': 'credit usage alert',
    '<b>Todo esto lo crea Terraform</b>': '<b>Terraform creates all of this</b>',
    '16 recursos (+1 opcional)': '16 resources (+1 optional)',
    'ver la página «2 · Terraform»': 'see page «2 · Terraform»',
    'VPC por defecto (data.aws_vpc.default)': 'Default VPC (data.aws_vpc.default)',
    'Subred pública por defecto': 'Default public subnet',
    'IP elástica': 'Elastic IP',
    'Grupo de seguridad polymer-web-* · entrada TCP 80 y 443 (0.0.0.0/0) · salida: todo · sin puerto 22':
        'Security group polymer-web-* · inbound TCP 80 and 443 (0.0.0.0/0) · outbound: all · no port 22',
    'EC2 m7i-flex.large · Ubuntu 24.04 · 2 vCPU · 8 GiB · EBS gp3 30 GB cifrado · IMDSv2 · swap 4 GB':
        'EC2 m7i-flex.large · Ubuntu 24.04 · 2 vCPU · 8 GiB · encrypted EBS gp3 30 GB · IMDSv2 · 4 GB swap',
    '<b>Caddy 2.10</b> (contenedor, red del host)': '<b>Caddy 2.10</b> (container, host network)',
    ":80 → :443 · certificado Let's Encrypt": ":80 → :443 · Let's Encrypt certificate",
    '<b>Agente SSM</b> (conexión saliente 443)': '<b>SSM agent</b> (outbound connection 443)',
    'consola · port forwarding a': 'console · port forwarding to',
    'ZIP de S3 → polymer.ps1 start': 'ZIP from S3 → polymer.ps1 start',
    'comando polymer-update': 'polymer-update command',
    'Docker Compose · proyecto «polymer» · modo full · 13 contenedores · puertos publicados solo en 127.0.0.1':
        'Docker Compose · project «polymer» · full mode · 13 containers · ports published only on 127.0.0.1',
    'redes: edge · gateway · telemetry': 'networks: edge · gateway · telemetry',
    'núcleo hexagonal · 127.0.0.1:8081': 'hexagonal core · 127.0.0.1:8081',
    'redes: gateway · data · compute · cache · messaging · telemetry · egress': 'networks: gateway · data · compute · cache · messaging · telemetry · egress',
    'redes: compute · telemetry · edge': 'networks: compute · telemetry · edge',
    'sin puerto en el host': 'no port on the host',
    'red data (interna)': 'data network (internal)',
    '<b>redis</b> 7.4 · caché y TTL': '<b>redis</b> 7.4 · cache and TTL',
    '(catálogo 60 s, Yape 60 s)': '(catalog 60 s, Yape 60 s)',
    'red cache (interna)': 'cache network (internal)',
    '<b>rabbitmq</b> · eventos AMQP': '<b>rabbitmq</b> · AMQP events',
    '127.0.0.1:15672 (consola)': '127.0.0.1:15672 (console)',
    'redes: messaging · edge': 'networks: messaging · edge',
    '<b>mailpit</b> · SMTP de prueba': '<b>mailpit</b> · test SMTP',
    'códigos de 6 dígitos y boletas': '6-digit codes and receipts',
    'Observabilidad · red telemetry (interna)': 'Observability · telemetry network (internal)',
    '<b>tempo</b> · trazas': '<b>tempo</b> · traces',
    '<b>alloy</b> · recoge los logs de Docker': '<b>alloy</b> · collects the Docker logs',
    'generados DENTRO de la instancia (nunca en Git, S3 ni Terraform)': 'generated INSIDE the instance (never in Git, S3 or Terraform)',
    '<b>Volúmenes Docker en el disco EBS</b>': '<b>Docker volumes on the EBS disk</b>',
    'tempo_data · alloy_data · polymer_caddy_data (certificados)': 'tempo_data · alloy_data · polymer_caddy_data (certificates)',
    'Internet · servicios externos': 'Internet · external services',
    "<b>Let's Encrypt</b> (ACME HTTP-01 por :80)": "<b>Let's Encrypt</b> (ACME HTTP-01 on :80)",
    'certificado TLS gratis · se renueva solo': 'free TLS certificate · renews itself',
    '<b>sslip.io</b> (DNS público)': '<b>sslip.io</b> (public DNS)',
    'Iniciar sesión / Registrarse': 'Sign in / Sign up',
    'imágenes base y paquetes (solo salida)': 'base images and packages (outbound only)',
    '<b>Gmail SMTP :587</b> (opcional)': '<b>Gmail SMTP :587</b> (optional)',
    'códigos y boletas a correos reales': 'codes and receipts to real mailboxes',
    '<b>Leyenda</b>': '<b>Legend</b>',
    '<font color="#0F766E">━━</font> tráfico de clientes (HTTPS)': '<font color="#0F766E">━━</font> customer traffic (HTTPS)',
    '<font color="#ED7100">╍╍</font> Terraform → API de AWS': '<font color="#ED7100">╍╍</font> Terraform → AWS API',
    '<font color="#E7157B">╍╍</font> Session Manager (túnel)': '<font color="#E7157B">╍╍</font> Session Manager (tunnel)',
    '<font color="#4338CA">━━</font> red Docker interna': '<font color="#4338CA">━━</font> internal Docker network',
    '<font color="#64748B">╍╍</font> salida a Internet': '<font color="#64748B">╍╍</font> outbound to the Internet',
    '<font color="#DD344C">╍╍</font> permisos IAM / datos de arranque': '<font color="#DD344C">╍╍</font> IAM permissions / boot data',
    'red gateway': 'gateway network',
    'consulta': 'query',
    'terraform apply (API de AWS por HTTPS)': 'terraform apply (AWS API over HTTPS)',
    'canal cifrado': 'encrypted channel',
    'túnel': 'tunnel',
    'perfil de instancia': 'instance profile',
    'descarga el ZIP': 'downloads the ZIP',
    'lee el JSON de Google': 'reads the Google JSON',
    'ACME (certificado)': 'ACME (certificate)',
    'OIDC (red egress)': 'OIDC (egress network)',
    'consulta DNS': 'DNS lookup',
    # ---------------------------------------------------------------- Terraform page
    '2 · Terraform · recursos y dependencias': '2 · Terraform · resources and dependencies',
    '<b style="font-size:24px">infra/aws/terraform · qué crea terraform apply</b>': '<b style="font-size:24px">infra/aws/terraform · what terraform apply creates</b>',
    '<span style="font-size:14px">Proveedores aws 6.x y archive 2.x · región us-east-2 · las flechas son dependencias (el origen se crea o se lee antes que el destino)</span>':
        '<span style="font-size:14px">Providers aws 6.x and archive 2.x · region us-east-2 · arrows are dependencies (the source is created or read before the target)</span>',
    '1 · Entradas': '1 · Inputs',
    '2 · Data sources (solo lectura)': '2 · Data sources (read only)',
    '3 · Recursos (16 + 1 opcional)': '3 · Resources (16 + 1 optional)',
    '4 · Salidas (terraform output)': '4 · Outputs (terraform output)',
    '<b>terraform.tfvars</b> (privado)': '<b>terraform.tfvars</b> (private)',
    'arranque de la instancia (cloud-init)': 'instance boot script (cloud-init)',
    '→ user_data de aws_instance': '→ user_data of aws_instance',
    'HTTPS · HSTS · www → dominio': 'HTTPS · HSTS · www → domain',
    '→ incluido en el user_data': '→ included in the user_data',
    'terraform test con AWS simulado': 'terraform test with a mocked AWS',
    '(sin cuenta; también en el CI)': '(no account needed; also in CI)',
    'ZIP del repositorio SIN secrets/,': 'repository ZIP WITHOUT secrets/,',
    '.env, .git ni estado de Terraform': '.env, .git or Terraform state',
    '(ID de la cuenta)': '(account ID)',
    '(Ubuntu 24.04 de Canonical)': '(Ubuntu 24.04 by Canonical)',
    '(solo con budget_alert_email)': '(only with budget_alert_email)',
    '.deploy_read (ZIP + 1 parámetro)': '.deploy_read (ZIP + 1 parameter)',
    'registros A (solo con dominio propio)': 'A records (only with your own domain)',
    'tunel_grafana (comandos SSM)': 'tunel_grafana (SSM commands)',
    '<b>Arranque de la instancia (user-data, una sola vez):</b> 1) swap 4 GB → 2) Docker + Compose, PowerShell, AWS CLI → 3) ZIP desde S3 → 4) .env público (POLYMER_PUBLIC_URL, URI de Google) → 5) JSON de Google desde SSM (si existe) → 6) Caddy con Let\'s Encrypt → 7) polymer.ps1 start: genera las contraseñas, compila con las pruebas y espera 13 contenedores sanos.':
        '<b>Instance boot (user-data, once):</b> 1) 4 GB swap → 2) Docker + Compose, PowerShell, AWS CLI → 3) ZIP from S3 → 4) public .env (POLYMER_PUBLIC_URL, Google URI) → 5) Google JSON from SSM (if present) → 6) Caddy with Let\'s Encrypt → 7) polymer.ps1 start: generates the passwords, builds with the tests and waits for 13 healthy containers.',
    '<b>Actualizar:</b> terraform apply (sube un ZIP nuevo, no recrea la instancia) + <i>sudo polymer-update</i> en la instancia (conserva datos y secretos). <b>Borrar todo:</b> terraform destroy.':
        '<b>Update:</b> terraform apply (uploads a new ZIP, does not recreate the instance) + <i>sudo polymer-update</i> on the instance (keeps data and secrets). <b>Delete everything:</b> terraform destroy.',
    'asigna': 'sets',
    'archivo': 'file',
    'ARN del parámetro': 'parameter ARN',
    'clave del ZIP': 'ZIP key',
    'perfil': 'profile',
    'IP → dominio': 'IP → domain',
    'grupo de seguridad': 'security group',
}

_SPLIT = re.compile(r'(\n|<br>)')
# Spanish leftovers: accented letters/ñ/¿¡ or frequent Spanish words.
_SPANISH = re.compile(r'[áéíóúñÁÉÍÓÚÑ¿¡]|\b(de|del|la|las|los|el|en|con|sin|solo|cada|para|por|una|un|y|o|que|se|su|ver|lee|red|redes)\b')


def tr(text: str) -> str:
    """Translates a label line by line; unknown lines are returned unchanged."""
    return ''.join(EN.get(part, part) for part in _SPLIT.split(text))


def check(texts) -> None:
    """Fails if any English label still contains Spanish."""
    left = sorted({t for text in texts for t in _SPLIT.split(text) if _SPANISH.search(re.sub(r'<[^>]+>', ' ', t))})
    if left:
        raise SystemExit('Spanish text left in the English diagrams (add it to diagram_i18n.EN):\n  ' + '\n  '.join(left))
