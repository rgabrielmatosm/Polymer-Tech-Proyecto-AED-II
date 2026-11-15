#!/usr/bin/env python3
"""Genera los diagramas de POLYMER desde UNA sola definición:

  docs/final/diagramas/POLYMER-arquitectura.drawio   (3 páginas editables en draw.io / diagrams.net)
  docs/final/diagramas/*.svg                          (las mismas páginas como imagen vectorial)
  docs/final/diagramas/ENLACE_DRAWIO.md               (enlace de diagrams.net que abre la arquitectura)

Uso: python tools/diagramas/generate_diagrams.py  (los PNG se obtienen de los SVG con tools/diagramas/render_png.js)
"""
from __future__ import annotations

import base64
import html
import urllib.parse
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs' / 'final' / 'diagramas'

# Paleta (tema claro: se imprime bien y se lee en un proyector).
C = {
    'core': ('#EEF2FF', '#4F46E5'), 'domain': ('#ECFEFF', '#0E7490'), 'in': ('#F0FDF4', '#15803D'),
    'out': ('#FFF7ED', '#C2410C'), 'port': ('#FFFFFF', '#4F46E5'), 'cfg': ('#F8FAFC', '#475569'),
    'ext': ('#FDF4FF', '#A21CAF'), 'data': ('#EFF6FF', '#1D4ED8'), 'obs': ('#FEFCE8', '#A16207'),
    'msg': ('#FFF1F2', '#BE123C'), 'title': ('#FFFFFF', '#FFFFFF'), 'tbl': ('#FFFFFF', '#334155'), 'tblh': ('#E2E8F0', '#334155'),
}


class Page:
    def __init__(self, name: str, width: int, height: int):
        self.name, self.width, self.height = name, width, height
        self.nodes: list[dict] = []
        self.edges: list[dict] = []

    def box(self, nid, label, x, y, w, h, kind, shape='rect', size=13, bold=False, align='center', valign='middle'):
        self.nodes.append(dict(id=nid, label=label, x=x, y=y, w=w, h=h, kind=kind, shape=shape, size=size, bold=bold, align=align, valign=valign))

    def edge(self, a, b, label='', dashed=False, color='#334155', horizontal=False):
        self.edges.append(dict(a=a, b=b, label=label, dashed=dashed, color=color, horizontal=horizontal))


# ---------------------------------------------------------------- página 1: arquitectura hexagonal
def hexagonal() -> Page:
    p = Page('1 · Arquitectura hexagonal', 1700, 1080)
    p.box('t', 'POLYMER · Arquitectura hexagonal (puertos y adaptadores, Alistair Cockburn 2005)', 40, 16, 1620, 40, 'title', size=22, bold=True)
    p.box('sub', 'Las dependencias del código apuntan HACIA DENTRO. El núcleo no conoce Spring, SQL, Redis, RabbitMQ ni HTTP: solo interfaces (puertos).',
          40, 56, 1620, 26, 'title', size=13)
    # Actores
    p.box('act', 'Cliente · Operador · Logística\nAdministrador · Observador\n(navegador, HTTP)', 40, 112, 250, 70, 'ext', shape='actor')
    # Adaptadores de entrada
    p.box('inG', 'ADAPTADORES DE ENTRADA  (adapter/in)', 40, 220, 330, 640, 'in', size=14, bold=True, valign='top')
    ins = [
        ('in1', 'frontend · Nginx (gateway :8080)\ninfra/frontend/nginx.conf'),
        ('in2', 'Controladores REST (adapter/in/web)\nShopController · PaymentController\nAuthController · AdminController\nOperationsController · LogisticsController\nTestimonialController · StoreController…'),
        ('in3', 'Google OpenID Connect\nsecurity/GoogleSignInHandlers'),
        ('in4', 'Oyente de RabbitMQ\nmessaging/BusinessEventListener'),
        ('in5', 'Planificador (cada 2 s)\nscheduling/EventRelayScheduler'),
    ]
    y = 262
    for nid, label in ins:
        h = 128 if nid == 'in2' else 88
        p.box(nid, label, 60, y, 290, h, 'in', size=12)
        y += h + 14
    # Núcleo
    p.box('core', '', 430, 120, 840, 860, 'core', shape='hexagon')
    p.box('coreT', 'NÚCLEO  (application + domain)  ·  Java puro, sin frameworks', 560, 150, 580, 30, 'title', size=15, bold=True)
    p.box('uc', 'CASOS DE USO  (application/service · 17)\nCommerceService · PaymentService · SignInService · CatalogService\nCartService · OperationsService · LogisticsService · TestimonialService\nNotificationService · EventRelayService · StoreService · …',
          560, 196, 580, 112, 'core', size=12)
    p.box('pin', 'PUERTOS DE ENTRADA\n(application/port/in · 17)\n\nCommerceUseCases\nPaymentUseCases\nSignInUseCases\nCatalogUseCases\nCartUseCases\nOperationsUseCases\nLogisticsUseCases\nTestimonialUseCases\nNotificationUseCases\n…', 500, 340, 190, 400, 'port', size=12)
    p.box('dom', 'DOMINIO  (domain/)\n\nOrder · OrderStatus (≥70 → revisión)\nTransitionPolicy (grafo de estados)\nCommerceOrder · CheckoutSummary\nPaymentPolicy (TTL Yape 60 s, IGV 18 %)\nCardDetails (Luhn) · Receipt\nDelivery (choque de intervalos)\nCatalogSearch · PriceTag · Category\nVerificationPolicy (6 dígitos, 10 min)\nBusinessHours · PeruHolidays (Pascua)\nTestimonial · BusinessEvent',
          700, 340, 300, 400, 'domain', shape='hexagon', size=11)
    p.box('pout', 'PUERTOS DE SALIDA\n(application/port/out · 34)\n\nCommerceOrderRepository\nCatalogRepository\nCatalogCache\nRiskAssessmentPort\nPaymentWindow\nCardGateway · WalletGateway\nEventOutbox · EventPublisher\nMailSender\nBusinessTelemetry\nMonitoringPort …', 1010, 340, 190, 400, 'port', size=12)
    p.box('rules', 'Verificado por ArchUnit (8 reglas, HexagonalArchitectureTest): si el núcleo importa una tecnología, la imagen Docker no se construye',
          560, 770, 580, 54, 'cfg', size=11)
    # Adaptadores de salida
    p.box('outG', 'ADAPTADORES DE SALIDA  (adapter/out)', 1330, 120, 340, 860, 'out', size=14, bold=True, valign='top')
    outs = [
        ('o1', 'JDBC → PostgreSQL 17\npersistence/Jdbc*Repository (21)', 'db'),
        ('o2', 'Redis (TTL)\ncache/RedisCatalogCache (60 s)\ncache/RedisPaymentWindow (60 s)', 'redis'),
        ('o3', 'HTTP → risk-engine (Python)\nhttp/HttpRiskAssessmentAdapter\n(o fixed/FixedRiskAssessmentAdapter)', 'risk'),
        ('o4', 'RabbitMQ (AMQP)\nmessaging/RabbitMqEventPublisher', 'mq'),
        ('o5', 'SMTP → Mailpit / Gmail\nmail/SmtpMailSender', 'mail'),
        ('o6', 'Micrometer → Prometheus\nmetrics/Micrometer*Telemetry', 'prom'),
        ('o7', 'Pasarelas de PRUEBA\npayment/SandboxCardGateway\npayment/SandboxWalletGateway', None),
        ('o8', 'Prometheus (lectura)\nmonitoring/PrometheusMonitoringAdapter', None),
    ]
    y = 162
    for nid, label, _ in outs:
        p.box(nid, label, 1350, y, 300, 86, 'out', size=12)
        y += 98
    # Raíz de composición
    p.box('cfg', 'RAÍZ DE COMPOSICIÓN  (config/)  ·  HexagonalConfiguration · IntegrationConfiguration · PlatformConfiguration · SecurityConfiguration\nÚnico lugar que conoce ambos lados: elige el adaptador (p. ej. polymer.risk.adapter = http | fixed)',
          430, 1000, 1240, 56, 'cfg', size=12)
    # Flechas
    p.edge('act', 'in1')
    for nid in ('in2', 'in3', 'in4', 'in5'):
        p.edge(nid, 'pin', 'llama a', color='#15803D', horizontal=True)
    p.edge('in1', 'in2', '/api', color='#15803D')
    p.edge('uc', 'pin', 'implementa', dashed=True, color='#4F46E5')
    p.edge('uc', 'dom', 'usa', color='#0E7490')
    p.edge('uc', 'pout', 'usa', color='#4F46E5')
    for nid in ('o1', 'o2', 'o3', 'o4', 'o5', 'o6', 'o7', 'o8'):
        p.edge(nid, 'pout', 'implementa' if nid == 'o1' else '', dashed=True, color='#C2410C', horizontal=True)
    return p


# ---------------------------------------------------------------- página 2: contenedores
def containers() -> Page:
    p = Page('2 · Contenedores Docker', 1700, 1000)
    p.box('t', 'POLYMER · 13 contenedores de Docker Compose (enlaces solo en 127.0.0.1)', 40, 16, 1620, 40, 'title', size=22, bold=True)
    lanes = [
        ('L1', 'ENTRADA', 40, 'in'), ('L2', 'NEGOCIO (2 servicios)', 360, 'core'), ('L3', 'DATOS', 700, 'data'),
        ('L4', 'MENSAJERÍA', 1010, 'msg'), ('L5', 'OBSERVABILIDAD', 1320, 'obs'),
    ]
    for lid, label, x, kind in lanes:
        p.box(lid, label, x, 80, 300, 880, kind, size=15, bold=True, valign='top')
    p.box('nav', 'Navegador\n(cliente, personal)', 70, 130, 240, 70, 'ext', shape='actor')
    p.box('fe', 'frontend · Nginx\n:8080 → tienda y /api', 70, 260, 240, 80, 'in')
    p.box('api', 'order-api\nJava 21 · Spring Boot 3.5\nNÚCLEO HEXAGONAL\n:8081 (directo) · gestión :9090', 390, 240, 240, 120, 'core')
    p.box('risk', 'risk-engine\nPython 3.12 · FastAPI\nmicroservicio hexagonal\n:8000 (/docs)', 390, 460, 240, 110, 'core')
    p.box('db', 'db · PostgreSQL 17\n25 tablas (Flyway V1…V13)\nfuente de verdad · privado', 730, 560, 240, 100, 'data')
    p.box('redis', 'redis 7\ncaché catálogo (TTL 60 s)\nQR Yape/Plin (TTL 60 s)\nLRU 48 MB · privado', 730, 760, 240, 110, 'data')
    p.box('mq', 'rabbitmq\nexchange hexaorders.events\ncola notifications + DLQ\nconsola :15672', 1040, 240, 240, 110, 'msg')
    p.box('mail', 'mailpit\nSMTP de pruebas\n:8025', 1040, 420, 240, 90, 'msg')
    p.box('gmail', 'Gmail (opcional)\nsmtp.gmail.com:587', 1040, 580, 240, 70, 'ext')
    p.box('google', 'Google OpenID Connect\n(«Continuar con Google»)', 70, 640, 240, 70, 'ext')
    p.box('prom', 'prometheus · :9091\nlee cada 10 s: order-api :9090,\nrisk-engine /metrics, rabbitmq,\nnginx, loki, tempo, alloy\n9 reglas de alerta', 1350, 120, 240, 120, 'obs')
    p.box('graf', 'grafana\n8 dashboards\n:3000', 1350, 280, 240, 80, 'obs')
    p.box('loki', 'loki\nlogs', 1350, 390, 240, 60, 'obs')
    p.box('alloy', 'alloy\nlee logs de Docker → Loki\n:12345', 1350, 490, 240, 80, 'obs')
    p.box('tempo', 'tempo\ntrazas', 1350, 610, 240, 60, 'obs')
    p.box('otel', 'otel-collector\nOTLP → Tempo · Nginx → Prometheus\n:13133', 1350, 710, 240, 90, 'obs')
    p.box('net', 'Redes: edge · gateway · data (solo order-api ↔ PostgreSQL) · compute · cache · messaging · telemetry · egress (salida a Internet solo para order-api)',
          40, 970, 1620, 24, 'title', size=12)
    p.edge('nav', 'fe', 'HTTP :8080')
    p.edge('fe', 'api', '/api (proxy)')
    p.edge('api', 'risk', 'POST /score (HTTP síncrono)')
    p.edge('api', 'db', 'JDBC (transacciones)')
    p.edge('api', 'redis', 'GET/SET con TTL')
    p.edge('api', 'mq', 'publica (outbox) · consume (idempotente)')
    p.edge('api', 'mail', 'SMTP')
    p.edge('api', 'gmail', 'SMTP (si se configura)', dashed=True)
    p.edge('api', 'google', 'OIDC', dashed=True)
    p.edge('graf', 'prom', 'PromQL', color='#A16207')
    p.edge('graf', 'loki', 'LogQL', color='#A16207')
    p.edge('alloy', 'loki', 'logs', color='#A16207')
    p.edge('otel', 'tempo', 'trazas', color='#A16207')
    return p


# ---------------------------------------------------------------- página 3: modelo de datos
TABLES = {
    'app_users': ['id PK', 'username UK', 'email', 'password_hash', 'email_verified', 'two_factor'],
    'app_user_roles': ['user_id PK,FK', 'role PK'],
    'user_preferences': ['user_id PK,FK', 'language'],
    'user_identities': ['provider PK', 'subject PK', 'user_id FK', 'email'],
    'verification_challenges': ['id PK', 'user_id FK', 'purpose', 'code_hash', 'expires_at (TTL 10 min)', 'attempts_left'],
    'device_tokens': ['kind PK', 'series PK', 'token_hash', 'user_id FK', 'expires_at (30 días)'],
    'categories': ['id PK', 'slug UK', 'name', 'parent_id FK (árbol)', 'position'],
    'products': ['id PK', 'sku UK', 'name', 'brand · model', 'category_id FK', 'price · stock'],
    'promotions': ['id PK', 'slug UK', 'discount_percent', 'starts_at · ends_at'],
    'promotion_targets': ['promotion_id FK', 'category_id FK', 'product_id FK'],
    'cart_items': ['user_id PK,FK', 'product_id PK,FK', 'quantity'],
    'orders': ['id PK (uuid)', 'order_number UK', 'user_id FK', 'amount · risk_score', 'status · fulfillment_status', 'idempotency_key UK'],
    'order_lines': ['order_id PK,FK', 'line_no PK', 'product_id FK', 'unit_price · quantity', 'promotion_id FK'],
    'order_status_history': ['id PK', 'order_id FK', 'from_status → to_status', 'actor · changed_at'],
    'order_shipping': ['order_id PK,FK', 'recipient · address · city'],
    'order_checkout': ['order_id PK,FK', 'delivery_method', 'payment_method', 'subtotal · total'],
    'payments': ['id PK (uuid)', 'order_id FK', 'method · status', 'expires_at (TTL 60 s)', 'card_brand · card_last4', 'receipt_series · number'],
    'deliveries': ['id PK', 'order_id FK', 'assignee_id FK', 'window_start · window_end'],
    'delivery_changes': ['id PK', 'delivery_id FK', 'action · old/new window'],
    'incidents': ['id PK', 'order_id FK', 'category · status'],
    'testimonials': ['id PK', 'kind (TEAM/CUSTOMER)', 'user_id FK UK', 'comment · rating', 'linkedin_url · visible'],
    'audit_events': ['id PK', 'actor · action', 'target · details'],
    'contact_messages': ['id PK', 'name · email', 'topic · message'],
    'outbox_published': ['event_id PK'],
    'processed_events': ['event_id PK', 'consumer PK'],
}
LAYOUT = {
    'app_user_roles': (40, 90), 'user_preferences': (40, 210), 'user_identities': (40, 310), 'verification_challenges': (40, 450),
    'device_tokens': (40, 630), 'app_users': (330, 330), 'cart_items': (330, 560), 'testimonials': (330, 90),
    'orders': (640, 330), 'order_lines': (640, 600), 'order_status_history': (640, 90), 'order_shipping': (940, 90),
    'order_checkout': (940, 210), 'payments': (940, 330), 'deliveries': (940, 560), 'delivery_changes': (940, 700),
    'incidents': (330, 900), 'products': (1240, 560), 'categories': (1240, 330), 'promotions': (1240, 90),
    'promotion_targets': (1240, 760), 'audit_events': (330, 760), 'contact_messages': (40, 830),
    'outbox_published': (1240, 900), 'processed_events': (940, 860),
}
RELATIONS = [
    ('app_user_roles', 'app_users'), ('user_preferences', 'app_users'), ('user_identities', 'app_users'),
    ('verification_challenges', 'app_users'), ('device_tokens', 'app_users'), ('cart_items', 'app_users'), ('cart_items', 'products'),
    ('testimonials', 'app_users'), ('orders', 'app_users'), ('order_lines', 'orders'), ('order_lines', 'products'),
    ('order_status_history', 'orders'), ('order_shipping', 'orders'), ('order_checkout', 'orders'), ('payments', 'orders'),
    ('deliveries', 'orders'), ('deliveries', 'app_users'), ('delivery_changes', 'deliveries'), ('incidents', 'orders'),
    ('products', 'categories'), ('categories', 'categories'), ('promotion_targets', 'promotions'), ('promotion_targets', 'products'),
]


def er() -> Page:
    p = Page('3 · Modelo de datos (E-R)', 1540, 1070)
    p.box('t', 'POLYMER · Modelo de datos en PostgreSQL (25 tablas, migraciones Flyway V1…V13)', 40, 16, 1460, 40, 'title', size=22, bold=True)
    for name, cols in TABLES.items():
        x, y = LAYOUT[name]
        h = 26 + 18 * len(cols)
        p.box(name, name + '\n' + '\n'.join(cols), x, y, 260, h, 'tbl', shape='table', size=11, align='left', valign='top')
    for a, b in RELATIONS:
        if a != b:
            p.edge(a, b, 'N:1', color='#64748B')
    p.box('leg', 'Mensajería: outbox_published (eventos publicados) y processed_events (eventos ya consumidos: idempotencia). Las FK apuntan del hijo (N) al padre (1). order_lines.promotion_id → promotions (promoción aplicada).',
          40, 1035, 1460, 24, 'title', size=12)
    return p


PAGES = [hexagonal, containers, er]

# ---------------------------------------------------------------- draw.io (mxGraph XML)
def style_of(n) -> str:
    fill, stroke = C[n['kind']]
    common = f"whiteSpace=wrap;html=0;fontSize={n['size']};fontColor=#0F172A;align={n['align']};verticalAlign={n['valign']};"
    if n['bold']:
        common += 'fontStyle=1;'
    if n['kind'] == 'title':
        return common + 'text;strokeColor=none;fillColor=none;'
    if n['shape'] == 'hexagon':
        return common + f'shape=hexagon;perimeter=hexagonPerimeter2;size={0.12 if n["id"] == "core" else 0.06};fillColor={fill};strokeColor={stroke};strokeWidth=2;'
    if n['shape'] == 'actor':
        return common + f'rounded=1;arcSize=40;fillColor={fill};strokeColor={stroke};dashed=1;'
    if n['shape'] == 'table':
        return common + f'rounded=0;fillColor={fill};strokeColor={stroke};spacingLeft=6;spacingTop=4;'
    return common + f'rounded=1;arcSize=8;fillColor={fill};strokeColor={stroke};spacing=6;'


def drawio_page(page: Page, index: int) -> str:
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for n in page.nodes:
        cells.append(f'<mxCell id="p{index}_{n["id"]}" value="{html.escape(n["label"], quote=True).replace(chr(10), "&#xa;")}" '
                     f'style="{style_of(n)}" vertex="1" parent="1"><mxGeometry x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" as="geometry"/></mxCell>')
    for i, e in enumerate(page.edges):
        st = f"endArrow=block;endFill={'0' if e['dashed'] else '1'};html=0;strokeColor={e['color']};fontSize=11;fontColor=#334155;" \
             f"{'dashed=1;' if e['dashed'] else ''}edgeStyle=orthogonalEdgeStyle;rounded=1;labelBackgroundColor=#FFFFFF;"
        cells.append(f'<mxCell id="p{index}_e{i}" value="{html.escape(e["label"], quote=True)}" style="{st}" edge="1" parent="1" '
                     f'source="p{index}_{e["a"]}" target="p{index}_{e["b"]}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    model = (f'<mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" '
             f'pageScale="1" pageWidth="{page.width}" pageHeight="{page.height}" background="#FFFFFF"><root>{"".join(cells)}</root></mxGraphModel>')
    return f'<diagram id="polymer-{index}" name="{html.escape(page.name)}">{model}</diagram>', model


# ---------------------------------------------------------------- SVG (misma geometría)
def svg_page(page: Page) -> str:
    by_id = {n['id']: n for n in page.nodes}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{page.width}" height="{page.height}" viewBox="0 0 {page.width} {page.height}" '
           f'font-family="Segoe UI, Arial, sans-serif">',
           '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
           '<path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>',
           f'<rect width="{page.width}" height="{page.height}" fill="#FFFFFF"/>']

    def clip(n, tx, ty):
        cx, cy = n['x'] + n['w'] / 2, n['y'] + n['h'] / 2
        dx, dy = tx - cx, ty - cy
        if dx == 0 and dy == 0:
            return cx, cy
        sx = (n['w'] / 2) / abs(dx) if dx else float('inf')
        sy = (n['h'] / 2) / abs(dy) if dy else float('inf')
        s = min(sx, sy)
        return cx + dx * s, cy + dy * s

    # contenedores grandes primero (los que contienen a otros), luego el resto
    order = sorted(page.nodes, key=lambda n: -(n['w'] * n['h']))
    for n in order:
        fill, stroke = C[n['kind']]
        x, y, w, h = n['x'], n['y'], n['w'], n['h']
        if n['kind'] == 'title':
            pass
        elif n['shape'] == 'hexagon':
            k = w * (0.12 if n['id'] == 'core' else 0.06)
            pts = f'{x + k},{y} {x + w - k},{y} {x + w},{y + h / 2} {x + w - k},{y + h} {x + k},{y + h} {x},{y + h / 2}'
            out.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        elif n['shape'] == 'table':
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}"/>')
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="22" fill="{C["tblh"][0]}" stroke="{stroke}"/>')
        else:
            dash = ' stroke-dasharray="6 4"' if n['shape'] == 'actor' else ''
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash}/>')
    for e in page.edges:
        a, b = by_id[e['a']], by_id[e['b']]
        bx, by_ = b['x'] + b['w'] / 2, b['y'] + b['h'] / 2
        ax, ay = a['x'] + a['w'] / 2, a['y'] + a['h'] / 2
        if e['horizontal']:
            y1 = y2 = min(max(ay, b['y'] + 24), b['y'] + b['h'] - 24)
            left = a['x'] > b['x']
            x1 = a['x'] if left else a['x'] + a['w']
            x2 = b['x'] + b['w'] if left else b['x']
            if not (a['y'] <= y1 <= a['y'] + a['h']):
                y1 = ay
        else:
            x1, y1 = clip(a, bx, by_)
            x2, y2 = clip(b, ax, ay)
        dash = ' stroke-dasharray="7 5"' if e['dashed'] else ''
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{e["color"]}" stroke-width="1.6"{dash} marker-end="url(#a)"/>')
        if e['label']:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            tw = 6.2 * len(e['label']) + 8
            out.append(f'<rect x="{mx - tw / 2:.1f}" y="{my - 9:.1f}" width="{tw:.1f}" height="16" rx="4" fill="#FFFFFF" opacity="0.92"/>')
            out.append(f'<text x="{mx:.1f}" y="{my + 3:.1f}" font-size="11" fill="#334155" text-anchor="middle">{html.escape(e["label"])}</text>')
    for n in order:
        lines = n['label'].split('\n')
        size = n['size']
        lh = size * 1.32
        x, y, w, h = n['x'], n['y'], n['w'], n['h']
        if n['valign'] == 'top':
            ty = y + size + 8
        else:
            ty = y + h / 2 - (len(lines) - 1) * lh / 2 + size * 0.35
        anchor, tx = ('start', x + 10) if n['align'] == 'left' else ('middle', x + w / 2)
        for i, line in enumerate(lines):
            weight = 'bold' if (n['bold'] or (n['shape'] == 'table' and i == 0) or (i == 0 and n['kind'] in ('port', 'domain', 'core') and n['id'] != 'core')) else 'normal'
            out.append(f'<text x="{tx:.1f}" y="{ty + i * lh:.1f}" font-size="{size}" font-weight="{weight}" fill="#0F172A" text-anchor="{anchor}">{html.escape(line)}</text>')
    out.append('</svg>')
    return '\n'.join(out)


def compressed(model: str) -> str:
    """Formato de diagrams.net: base64(deflateRaw(encodeURIComponent(xml)))."""
    encoded = urllib.parse.quote(model, safe="-_.!~*'()")
    raw = zlib.compressobj(9, zlib.DEFLATED, -15)
    data = raw.compress(encoded.encode('utf-8')) + raw.flush()
    return base64.b64encode(data).decode('ascii')


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    diagrams, models = [], []
    for i, factory in enumerate(PAGES, 1):
        page = factory()
        diagram, model = drawio_page(page, i)
        diagrams.append(diagram)
        models.append(model)
        slug = ['arquitectura-hexagonal', 'contenedores', 'modelo-datos'][i - 1]
        (OUT / f'POLYMER-{slug}.svg').write_text(svg_page(page), encoding='utf-8')
    xml = f'<mxfile host="POLYMER" agent="tools/diagramas/generate_diagrams.py" version="24.0.0">{"".join(diagrams)}</mxfile>\n'
    (OUT / 'POLYMER-arquitectura.drawio').write_text(xml, encoding='utf-8')
    link = 'https://app.diagrams.net/#R' + urllib.parse.quote(compressed(models[0]), safe='')
    (OUT / 'ENLACE_DRAWIO.md').write_text(f"""# Abrir los diagramas en draw.io (diagrams.net)

**Forma recomendada (los 3 diagramas, editables):**

1. Entra a https://app.diagrams.net
2. *Archivo → Abrir desde → Dispositivo* y elige `docs/final/diagramas/POLYMER-arquitectura.drawio`.
3. Abajo hay 3 pestañas: **1 · Arquitectura hexagonal**, **2 · Contenedores Docker**, **3 · Modelo de datos (E-R)**.
   Para la PPT: *Archivo → Exportar como → PNG* (o usa los PNG ya generados en esta carpeta).

En **VS Code**: instala la extensión *Draw.io Integration* (hediet.vscode-drawio) y abre el archivo `.drawio`.

**Enlace directo** (abre solo el diagrama 1 en el navegador, sin descargar nada; el diagrama viaja dentro del enlace):

{link}

> Si el enlace no abre en tu navegador por su longitud, usa la forma recomendada de arriba.
""", encoding='utf-8')
    print(f'OK: {OUT.relative_to(ROOT)} (drawio con {len(PAGES)} páginas, {len(PAGES)} SVG, enlace de {len(link)} caracteres)')


if __name__ == '__main__':
    main()
