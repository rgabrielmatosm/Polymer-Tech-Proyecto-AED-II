#!/usr/bin/env python3
"""Genera docs/final/diagramas/POLYMER-AWS-Terraform.drawio con iconos oficiales de AWS (mxgraph.aws4):

  1 · AWS · POLYMER desplegado      Nube → región us-east-2 → cuenta → VPC → subred → grupo de seguridad → EC2
                                    con Caddy y los 13 contenedores; S3, IAM, SSM, IP elástica; laptop con Terraform
                                    y túnel de Session Manager; servicios externos (Let's Encrypt, sslip.io, Google).
  2 · Terraform · recursos          Cada recurso/data source de infra/aws/terraform y sus dependencias.
  3 · Entidad-relación              Las 25 tablas de PostgreSQL (contenedor db), reutilizando generate_diagrams.er().

Todo lo que aparece sale del código: infra/compose.base.yml (redes, puertos, volúmenes) e infra/aws/terraform.
Uso: python tools/diagramas/generate_aws_diagram.py [--lang en]   (en inglés: docs/final/diagramas/en/)
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_diagrams as base  # noqa: E402  (página E-R compartida)

OUT = base.OUT / 'POLYMER-AWS-Terraform.drawio'

PUBLIC_IP = '18.189.49.9'
HOST = PUBLIC_IP.replace('.', '-') + '.sslip.io'

# Colores de categoría de AWS (los mismos de la paleta oficial de draw.io).
COMPUTE, STORAGE, SECURITY, MANAGEMENT, NETWORK, GENERAL = '#ED7100', '#7AA116', '#DD344C', '#E7157B', '#8C4FFF', '#232F3D'
PTS = ('points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],'
       '[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];')


def res_icon(name: str, color: str) -> str:
    return (f'sketch=0;{PTS}outlineConnect=0;fontColor=#232F3E;fillColor={color};strokeColor=#ffffff;dashed=0;'
            'verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;'
            f'shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{name};')


def shape_icon(name: str, color: str) -> str:
    return ('sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;strokeColor=none;dashed=0;'
            'verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;'
            f'pointerEvents=1;fillColor={color};shape=mxgraph.aws4.{name};')


def group(icon: str, stroke: str, font: str | None = None, fill: str = 'none', dashed: bool = False) -> str:
    return ('points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],'
            '[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=13;fontStyle=1;'
            'container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;'
            f'grIcon=mxgraph.aws4.{icon};strokeColor={stroke};fillColor={fill};verticalAlign=top;align=left;spacingLeft=30;'
            f'fontColor={font or stroke};dashed={1 if dashed else 0};')


def plain_group(stroke: str, fill: str, dashed: bool = True, font: str = '#0F172A') -> str:
    return (f'rounded=1;arcSize=3;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;fillColor={fill};'
            f'strokeColor={stroke};dashed={1 if dashed else 0};verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;'
            f'fontSize=13;fontStyle=1;fontColor={font};')


def card(fill: str, stroke: str, size: int = 12, align: str = 'center') -> str:
    return (f'rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize={size};'
            f'fontColor=#0F172A;align={align};verticalAlign=middle;spacing=6;')


TEXT = 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;fontColor=#0F172A;'


def edge(color: str, dashed: bool = False, width: int = 1, curved: bool = False) -> str:
    return (f'edgeStyle={"none" if curved else "orthogonalEdgeStyle"};rounded=1;orthogonalLoop=1;jettySize=auto;html=1;'
            f'strokeColor={color};strokeWidth={width};fontSize=11;fontColor={color};labelBackgroundColor=#FFFFFF;'
            f'endArrow=block;endFill=1;{"dashed=1;dashPattern=8 6;" if dashed else ""}')


class Diagram:
    def __init__(self, name: str, width: int, height: int, prefix: str):
        self.name, self.width, self.height, self.p = base.tr(name), width, height, prefix
        self.cells: list[str] = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
        self.ids: set[str] = set()
        self.labels: list[str] = [self.name]

    def _id(self, i: str) -> str:
        return f'{self.p}_{i}'

    def v(self, i: str, label: str, style: str, x: float, y: float, w: float, h: float, parent: str | None = None) -> str:
        assert i not in self.ids, i
        label = base.tr(label)
        self.labels.append(label)
        self.ids.add(i)
        par = self._id(parent) if parent else '1'
        self.cells.append(f'<mxCell id="{self._id(i)}" value="{html.escape(label, quote=True)}" style="{style}" vertex="1" '
                          f'parent="{par}"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return i

    def e(self, a: str, b: str, label: str, style: str, exit_: str = '', entry: str = '',
          points: list[tuple[int, int]] | None = None) -> None:
        assert a in self.ids and b in self.ids, (a, b)
        label = base.tr(label)
        self.labels.append(label)
        i = f'e{len(self.cells)}'
        pts = ''
        if points:
            pts = '<Array as="points">' + ''.join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points) + '</Array>'
        self.cells.append(f'<mxCell id="{self._id(i)}" value="{html.escape(label, quote=True)}" style="{style}{exit_}{entry}" '
                          f'edge="1" parent="1" source="{self._id(a)}" target="{self._id(b)}"><mxGeometry relative="1" '
                          f'as="geometry">{pts}</mxGeometry></mxCell>')

    def xml(self, index: int) -> str:
        model = (f'<mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
                 f'fold="1" page="1" pageScale="1" pageWidth="{self.width}" pageHeight="{self.height}" background="#FFFFFF" '
                 f'math="0" shadow="0"><root>{"".join(self.cells)}</root></mxGraphModel>')
        return f'<diagram id="polymer-aws-{index}" name="{html.escape(self.name)}">{model}</diagram>'


def X(side: str, x: float, y: float) -> str:
    """Punto de salida (exit) o entrada (entry) de una arista."""
    return f'{side}X={x};{side}Y={y};{side}Dx=0;{side}Dy=0;'


# ---------------------------------------------------------------------------------------------------------------
def aws_page() -> Diagram:
    d = Diagram('1 · AWS · POLYMER desplegado (Terraform)', 2640, 1720, 'a')
    d.v('title', f'<b style="font-size:26px">POLYMER en Amazon Web Services</b><br>'
                 f'<span style="font-size:15px">Una instancia EC2 con Docker Compose (13 contenedores) detrás de Caddy (HTTPS), '
                 f'creada con Terraform · <b>https://{HOST}</b></span>', TEXT, 30, 10, 1900, 70)

    # ---- Laptop del administrador
    d.v('laptop', 'Laptop del administrador (Windows)', plain_group('#475569', '#F8FAFC'), 30, 300, 340, 690)
    d.v('client', '', shape_icon('client', GENERAL), 131, 38, 78, 76, 'laptop')
    d.v('tf', '<b>Terraform CLI</b><br>terraform init · plan · apply · destroy<br><i>terraform.tfstate</i> local (privado)',
        card('#FFF7ED', COMPUTE), 20, 140, 300, 100, 'laptop')
    d.v('cli', '<b>AWS CLI + Session Manager plugin</b><br>usuario IAM terraform-admin<br>aws ssm start-session',
        card('#FDF2F8', MANAGEMENT), 20, 260, 300, 100, 'laptop')
    d.v('tunnel', '<b>Navegador por el túnel</b><br>localhost:3000 Grafana · :8025 Mailpit<br>'
                  ':15672 RabbitMQ · :9091 Prometheus', card('#FDF2F8', MANAGEMENT), 20, 380, 300, 100, 'laptop')
    d.v('local', '<b>Docker Desktop (POLYMER local)</b><br>http://localhost:8080 … :12345<br>'
                 'misma imagen, datos propios', card('#EFF6FF', '#1D4ED8'), 20, 500, 300, 100, 'laptop')
    d.v('laptopnote', '<i>Las claves de AWS y el JSON de Google<br>se quedan en este equipo.</i>',
        TEXT + 'align=center;fontSize=11;', 20, 615, 300, 50, 'laptop')

    d.v('users', 'Clientes de la tienda<br>(navegador o móvil)', shape_icon('users', GENERAL), 161, 1130, 78, 78)

    # ---- AWS Cloud → región → cuenta
    d.v('cloud', 'AWS Cloud', group('group_aws_cloud_alt', GENERAL, '#232F3E'), 430, 100, 1810, 1590)
    d.v('region', 'US East (Ohio) · us-east-2', group('group_region', '#00A4A6', '#147EBA', dashed=True), 20, 40, 1770, 1530, 'cloud')
    d.v('account', 'Cuenta del proyecto «Sunlit Server - Sagabella» · plan gratuito (créditos) · '
                   'la SCP de la organización solo permite us-east-2', group('group_account', '#CD2264'), 20, 40, 1730, 1470, 'region')

    # Servicios regionales (fuera de la VPC)
    d.v('ssm', '<b>Systems Manager</b><br>Session Manager<br>consola y túneles sin SSH',
        shape_icon('systems_manager_session_manager', MANAGEMENT), 1530, 70, 78, 78, 'account')
    d.v('iam', '<b>IAM</b> · rol polymer-ec2-*<br>+ perfil de instancia<br>SSM Core · s3:GetObject<br>ssm:GetParameter',
        res_icon('identity_and_access_management', SECURITY), 1530, 320, 78, 78, 'account')
    d.v('s3', '<b>S3</b> · polymer-deploy-*<br>ZIP del código sin secretos<br>privado · cifrado AES256',
        res_icon('s3', STORAGE), 1530, 560, 78, 78, 'account')
    d.v('param', '<b>SSM Parameter Store</b><br>/polymer/google-oauth-json<br>SecureString (clave aws/ssm)',
        shape_icon('parameter_store', MANAGEMENT), 1530, 800, 78, 78, 'account')
    d.v('budget', '<b>AWS Budgets</b> (opcional)<br>alerta de consumo de créditos', res_icon('budgets_2', STORAGE), 1530, 1030, 78, 78, 'account')
    d.v('tfnote', '<b>Todo esto lo crea Terraform</b><br>infra/aws/terraform<br>16 recursos (+1 opcional)<br>'
                  'ver la página «2 · Terraform»', card('#FFF7ED', COMPUTE, 12), 1440, 1260, 260, 110, 'account')

    # VPC → subred → grupo de seguridad → EC2
    d.v('vpc', 'VPC por defecto (data.aws_vpc.default)', group('group_vpc2', NETWORK), 60, 60, 1340, 1380, 'account')
    d.v('subnet', 'Subred pública por defecto', group('group_security_group', '#7AA116', '#248814', '#F2F6E8')
        .replace('fontStyle=1', 'fontStyle=1;grStroke=0'), 100, 50, 1210, 1300, 'vpc')
    d.v('igw', 'Internet<br>Gateway', shape_icon('internet_gateway', NETWORK), -39, 610, 78, 78, 'vpc')
    d.v('eip', f'IP elástica<br><b>{PUBLIC_IP}</b>', shape_icon('elastic_ip_address', NETWORK), -39, 560, 78, 78, 'subnet')
    d.v('sg', 'Grupo de seguridad polymer-web-* · entrada TCP 80 y 443 (0.0.0.0/0) · salida: todo · sin puerto 22',
        'fillColor=none;strokeColor=#DD3522;dashed=1;verticalAlign=top;fontStyle=1;fontColor=#DD3522;whiteSpace=wrap;html=1;'
        'container=1;collapsible=0;recursiveResize=0;align=left;spacingLeft=10;fontSize=13;', 80, 50, 1100, 1225, 'subnet')
    d.v('ec2', 'EC2 m7i-flex.large · Ubuntu 24.04 · 2 vCPU · 8 GiB · EBS gp3 30 GB cifrado · IMDSv2 · swap 4 GB',
        group('group_ec2_instance_contents', COMPUTE), 25, 45, 1050, 1160, 'sg')
    d.v('ec2icon', 'aws_instance<br>.polymer', res_icon('ec2', COMPUTE), 25, 45, 64, 64, 'ec2')
    d.v('caddy', '<b>Caddy 2.10</b> (contenedor, red del host)<br>:80 → :443 · certificado Let\'s Encrypt<br>'
                 'HSTS · /api/orders → 403', card('#ECFDF5', '#047857'), 130, 40, 320, 100, 'ec2')
    d.v('agent', '<b>Agente SSM</b> (conexión saliente 443)<br>consola · port forwarding a<br>127.0.0.1:3000 · 8025 · 15672 · 9091', card('#FDF2F8', MANAGEMENT),
        470, 40, 250, 100, 'ec2')
    d.v('init', '<b>cloud-init (user-data)</b><br>Docker · PowerShell · AWS CLI<br>ZIP de S3 → polymer.ps1 start<br>'
                'comando polymer-update', card('#FFF7ED', COMPUTE), 740, 40, 285, 100, 'ec2')

    d.v('compose', 'Docker Compose · proyecto «polymer» · modo full · 13 contenedores · puertos publicados solo en 127.0.0.1',
        plain_group('#2563EB', '#F8FBFF', dashed=False, font='#1D4ED8'), 20, 165, 1010, 975, 'ec2')
    app, data, obs = ('#EEF2FF', '#4F46E5'), ('#EFF6FF', '#1D4ED8'), ('#FEFCE8', '#A16207')
    d.v('frontend', '<b>frontend</b> · Nginx (gateway)<br>127.0.0.1:8080<br>redes: edge · gateway · telemetry',
        card(*app), 380, 40, 260, 85, 'compose')
    d.v('api', '<b>order-api</b> · Spring Boot 3.5 · Java 21<br>núcleo hexagonal · 127.0.0.1:8081<br>'
               'redes: gateway · data · compute · cache · messaging · telemetry · egress', card('#E0E7FF', '#4338CA'), 330, 170, 360, 100, 'compose')
    d.v('risk', '<b>risk-engine</b> · FastAPI (Python)<br>127.0.0.1:8000 · POST /score<br>redes: compute · telemetry · edge',
        card(*app), 745, 170, 245, 100, 'compose')
    d.v('db', '<b>db</b> · PostgreSQL 17<br>sin puerto en el host<br>red data (interna)<br>vol. postgres_data', card(*data), 20, 330, 225, 105, 'compose')
    d.v('redis', '<b>redis</b> 7.4 · caché y TTL<br>(catálogo 60 s, Yape 60 s)<br>red cache (interna)<br>vol. redis_data',
        card(*data), 265, 330, 220, 105, 'compose')
    d.v('rabbit', '<b>rabbitmq</b> · eventos AMQP<br>127.0.0.1:15672 (consola)<br>redes: messaging · edge<br>vol. rabbitmq_data',
        card('#FFF1F2', '#BE123C'), 505, 330, 230, 105, 'compose')
    d.v('mailpit', '<b>mailpit</b> · SMTP de prueba<br>127.0.0.1:8025<br>códigos de 6 dígitos y boletas<br>redes: messaging · edge',
        card('#FFF1F2', '#BE123C'), 755, 330, 235, 105, 'compose')

    d.v('obs', 'Observabilidad · red telemetry (interna)', plain_group('#A16207', '#FFFDF5', font='#A16207'), 20, 490, 970, 280, 'compose')
    d.v('prom', '<b>prometheus</b><br>127.0.0.1:9091<br>vol. prometheus_data', card(*obs), 20, 40, 215, 90, 'obs')
    d.v('graf', '<b>grafana</b><br>127.0.0.1:3000<br>vol. grafana_data', card(*obs), 255, 40, 215, 90, 'obs')
    d.v('loki', '<b>loki</b> · logs<br>vol. loki_data', card(*obs), 490, 40, 215, 90, 'obs')
    d.v('tempo', '<b>tempo</b> · trazas<br>vol. tempo_data', card(*obs), 725, 40, 225, 90, 'obs')
    d.v('otel', '<b>otel-collector</b> · OTLP<br>127.0.0.1:13133', card(*obs), 140, 170, 260, 85, 'obs')
    d.v('alloy', '<b>alloy</b> · recoge los logs de Docker<br>127.0.0.1:12345 · vol. alloy_data', card(*obs), 500, 170, 290, 85, 'obs')

    d.v('secrets', '<b>/opt/polymer/secrets</b> → Docker secrets<br>generados DENTRO de la instancia (nunca en Git, S3 ni Terraform)<br>'
                   'db · grafana · rabbitmq · demo · smtp · google-oauth.json', card('#FEF2F2', SECURITY, 12, 'left'), 20, 800, 475, 150, 'compose')
    d.v('vols', '<b>Volúmenes Docker en el disco EBS</b><br>postgres_data · redis_data · rabbitmq_data<br>prometheus_data · grafana_data · loki_data<br>'
                'tempo_data · alloy_data · polymer_caddy_data (certificados)', card('#F0FDF4', '#15803D', 12, 'left'), 515, 800, 475, 150, 'compose')

    # ---- Servicios externos
    d.v('internet', 'Internet · servicios externos', shape_icon('internet_alt2', GENERAL), 2392, 120, 78, 78)
    d.v('le', "<b>Let's Encrypt</b> (ACME HTTP-01 por :80)<br>certificado TLS gratis · se renueva solo", card('#F0FDF4', '#15803D'), 2280, 290, 320, 90)
    d.v('sslip', f'<b>sslip.io</b> (DNS público)<br>{HOST} → {PUBLIC_IP}', card('#F8FAFC', '#475569'), 2280, 420, 320, 90)
    d.v('google', f'<b>Google Identity (OIDC)</b><br>Iniciar sesión / Registrarse<br>redirect: https://{HOST}<br>/login/oauth2/code/google',
        card('#EFF6FF', '#1D4ED8'), 2280, 550, 320, 120)
    d.v('registry', '<b>Docker Hub · apt · snap</b><br>imágenes base y paquetes (solo salida)', card('#F8FAFC', '#475569'), 2280, 710, 320, 90)
    d.v('gmail', '<b>Gmail SMTP :587</b> (opcional)<br>códigos y boletas a correos reales', card('#F8FAFC', '#475569'), 2280, 840, 320, 90)
    d.v('legend', '<b>Leyenda</b><br><font color="#0F766E">━━</font> tráfico de clientes (HTTPS)<br>'
                  f'<font color="{COMPUTE}">╍╍</font> Terraform → API de AWS<br><font color="{MANAGEMENT}">╍╍</font> Session Manager (túnel)<br>'
                  '<font color="#4338CA">━━</font> red Docker interna<br><font color="#64748B">╍╍</font> salida a Internet<br>'
                  f'<font color="{SECURITY}">╍╍</font> permisos IAM / datos de arranque',
        card('#FFFFFF', '#94A3B8', 13, 'left'), 2280, 980, 320, 190)

    # ---- Aristas
    https, net, tfc, ssmc, out_ = edge('#0F766E', width=3), edge('#4338CA', width=2), edge(COMPUTE, True, 2), edge(MANAGEMENT, True, 2), edge('#64748B', True)
    d.e('users', 'igw', 'HTTPS 443', https, exit_=X('exit', 1, 0.5), entry=X('entry', 0, 0.5), points=[(420, 1169), (420, 889)])
    d.e('igw', 'eip', '', https, exit_=X('exit', 1, 0.5), entry=X('entry', 0, 0.5))
    d.e('eip', 'caddy', '443 / 80', https, exit_=X('exit', 1, 0.5), entry=X('entry', 0, 0.5), points=[(700, 889), (700, 475)])
    d.e('caddy', 'frontend', '127.0.0.1:8080', https, exit_=X('exit', 0.5, 1), entry=X('entry', 0.5, 0))
    d.e('frontend', 'api', 'red gateway', net, exit_=X('exit', 0.5, 1), entry=X('entry', 0.5, 0))
    d.e('api', 'risk', 'compute', net, exit_=X('exit', 1, 0.5), entry=X('entry', 0, 0.5))
    d.e('api', 'db', 'JDBC · data', net, exit_=X('exit', 0.1, 1), entry=X('entry', 0.5, 0))
    d.e('api', 'redis', 'cache', net, exit_=X('exit', 0.3, 1), entry=X('entry', 0.5, 0))
    d.e('api', 'rabbit', 'outbox → AMQP', net, exit_=X('exit', 0.8, 1), entry=X('entry', 0.5, 0))
    d.e('rabbit', 'mailpit', 'SMTP', net, exit_=X('exit', 1, 0.5), entry=X('entry', 0, 0.5))
    d.e('api', 'otel', 'OTLP', edge('#A16207', True), exit_=X('exit', 0.472, 1), entry=X('entry', 1, 0.5),
        points=[(1255, 1252)])
    d.e('otel', 'tempo', 'trazas', edge('#A16207'), exit_=X('exit', 0.5, 1), entry=X('entry', 1, 0.5), points=[(1045, 1310), (1737, 1310), (1737, 1125)])
    d.e('alloy', 'loki', 'logs', edge('#A16207'), exit_=X('exit', 0.5, 0), entry=X('entry', 0.5, 1))
    d.e('graf', 'prom', 'consulta', edge('#A16207'), exit_=X('exit', 0, 0.5), entry=X('entry', 1, 0.5))
    d.e('tf', 'account', 'terraform apply (API de AWS por HTTPS)', tfc, exit_=X('exit', 1, 0.3), entry=X('entry', 0, 0.06))
    d.e('cli', 'ssm', 'aws ssm start-session', ssmc, exit_=X('exit', 0, 0.5), entry=X('entry', 0.5, 0),
        points=[(15, 610), (15, 90), (2039, 90)])
    d.e('ssm', 'agent', 'canal cifrado', ssmc, exit_=X('exit', 0, 0.5), entry=X('entry', 0.5, 0), points=[(1330, 289)])
    d.e('agent', 'compose', 'túnel', ssmc, exit_=X('exit', 0.5, 1), entry=X('entry', 0.57, 0))
    d.e('iam', 'ec2', 'perfil de instancia', edge(SECURITY, True), exit_=X('exit', 0, 0.5), entry=X('entry', 1, 0.133))
    d.e('init', 's3', 'descarga el ZIP', edge(SECURITY, True), exit_=X('exit', 1, 0.3), entry=X('entry', 0, 0.5), points=[(1850, 455), (1850, 779)])
    d.e('init', 'param', 'lee el JSON de Google', edge(SECURITY, True), exit_=X('exit', 1, 0.7), entry=X('entry', 0, 0.5),
        points=[(1900, 495), (1900, 1019)])
    d.e('caddy', 'le', 'ACME (certificado)', out_, exit_=X('exit', 0.5, 0), entry=X('entry', 0, 0.5), points=[(1025, 230), (2260, 230), (2260, 335)])
    d.e('api', 'google', 'OIDC (red egress)', out_, exit_=X('exit', 0.8, 0), entry=X('entry', 0, 0.5), points=[(1373, 700), (2265, 700), (2265, 610)])
    d.e('init', 'registry', 'docker pull · apt', out_, exit_=X('exit', 1, 0.15), entry=X('entry', 0, 0.5), points=[(2250, 440), (2250, 755)])
    d.e('users', 'sslip', 'consulta DNS', out_, exit_=X('exit', 0, 0.5), entry=X('entry', 1, 0.5),
        points=[(120, 1169), (120, 1705), (2620, 1705), (2620, 465)])
    return d


# ---------------------------------------------------------------------------------------------------------------
def terraform_page() -> Diagram:
    d = Diagram('2 · Terraform · recursos y dependencias', 2200, 1360, 't')
    d.v('title', '<b style="font-size:24px">infra/aws/terraform · qué crea terraform apply</b><br>'
                 '<span style="font-size:14px">Proveedores aws 6.x y archive 2.x · región us-east-2 · '
                 'las flechas son dependencias (el origen se crea o se lee antes que el destino)</span>', TEXT, 30, 10, 1900, 70)
    for i, label, x, w, fill, stroke in [('cin', '1 · Entradas', 30, 300, '#F8FAFC', '#475569'),
                                         ('cdata', '2 · Data sources (solo lectura)', 360, 330, '#F5F3FF', NETWORK),
                                         ('cres', '3 · Recursos (16 + 1 opcional)', 720, 1050, '#FFFBF5', COMPUTE),
                                         ('cout', '4 · Salidas (terraform output)', 1800, 360, '#F0FDF4', '#15803D')]:
        d.v(i, label, plain_group(stroke, fill, font=stroke), x, 100, w, 1100)

    for i, label, y, h in [
            ('tfvars', '<b>terraform.tfvars</b> (privado)<br>region = "us-east-2"<br>instance_type = "m7i-flex.large"<br>mode = "full" · domain = ""', 140, 120),
            ('vars', '<b>variables.tf</b><br>region · instance_type · mode · domain<br>redirect_www · swap_gb · root_volume_gb<br>google_oauth_parameter · budget_*', 320, 120),
            ('ud', '<b>templates/user-data.sh.tftpl</b><br>arranque de la instancia (cloud-init)<br>→ user_data de aws_instance', 500, 100),
            ('caddyf', '<b>templates/Caddyfile.tftpl</b><br>HTTPS · HSTS · www → dominio<br>→ incluido en el user_data', 660, 100),
            ('test', '<b>tests/plan.tftest.hcl</b><br>terraform test con AWS simulado<br>(sin cuenta; también en el CI)', 820, 110)]:
        d.v(i, label, card('#FFFFFF', '#475569', 12), 50, y, 260, h)

    d.v('d_zip', '<b>data.archive_file.source</b><br>ZIP del repositorio SIN secrets/,<br>.env, .git ni estado de Terraform',
        card('#FFFFFF', NETWORK, 12), 380, 130, 290, 100)
    d.v('d_id', 'data.aws_caller_identity.current<br>(ID de la cuenta)', res_icon('identity_and_access_management', SECURITY), 492, 560, 66, 66)
    d.v('d_vpc', 'data.aws_vpc.default', res_icon('vpc', NETWORK), 492, 800, 66, 66)
    d.v('d_ami', 'data.aws_ssm_parameter.ubuntu_ami<br>(Ubuntu 24.04 de Canonical)', res_icon('systems_manager', MANAGEMENT), 492, 1070, 66, 66)

    s3i, rolei = shape_icon('bucket_with_objects', STORAGE), shape_icon('role', SECURITY)
    sgi, eipi = shape_icon('internet_gateway', NETWORK), shape_icon('elastic_ip_address', NETWORK)
    for i, label, style, x, y in [
            ('bucket', 'aws_s3_bucket.deploy', res_icon('s3', STORAGE), 780, 160),
            ('obj', 'aws_s3_object.source<br>source/polymer-&lt;md5&gt;.zip', s3i, 1120, 160),
            ('bud', 'aws_budgets_budget.monthly<br>(solo con budget_alert_email)', res_icon('budgets_2', STORAGE), 1600, 160),
            ('pab', 'aws_s3_bucket_<br>public_access_block', s3i, 780, 320),
            ('sse', 'aws_s3_bucket_server_side_<br>encryption_configuration', s3i, 950, 320),
            ('own', 'aws_s3_bucket_<br>ownership_controls', s3i, 1120, 320),
            ('role', 'aws_iam_role.instance', res_icon('identity_and_access_management', SECURITY), 780, 480),
            ('attach', 'aws_iam_role_policy_<br>attachment.ssm_core', rolei, 780, 640),
            ('policy', 'aws_iam_role_policy<br>.deploy_read (ZIP + 1 parámetro)', rolei, 950, 640),
            ('profile', 'aws_iam_instance_<br>profile.instance', rolei, 1120, 640),
            ('sgr', 'aws_security_group.web', res_icon('vpc', NETWORK), 780, 800),
            ('eipr', 'aws_eip.polymer', eipi, 1120, 800),
            ('http', 'ingress_rule.http<br>(TCP 80)', sgi, 780, 960),
            ('https', 'ingress_rule.https<br>(TCP 443)', sgi, 950, 960),
            ('egress', 'egress_rule.all', sgi, 1120, 960),
            ('inst', '<b>aws_instance.polymer</b><br>m7i-flex.large · gp3 30 GB · IMDSv2<br>user_data = user-data + Caddyfile', res_icon('ec2', COMPUTE), 1500, 640),
            ('assoc', 'aws_eip_association.polymer', eipi, 1500, 960)]:
        d.v(i, label, style, x, y, 66, 66)

    for n, (i, label) in enumerate([('o_url', f'<b>url</b><br>https://{HOST}'), ('o_ip', f'<b>public_ip</b><br>{PUBLIC_IP}'),
                                    ('o_dns', '<b>dns_records</b><br>registros A (solo con dominio propio)'),
                                    ('o_inst', '<b>instance_id</b> · ver_progreso<br>tunel_grafana (comandos SSM)'),
                                    ('o_g', '<b>google_redirect_uri</b><br>…/login/oauth2/code/google')]):
        d.v(i, label, card('#FFFFFF', '#15803D', 12), 1820, 160 + n * 190, 320, 90)

    d.v('flow', '<b>Arranque de la instancia (user-data, una sola vez):</b> 1) swap 4 GB → 2) Docker + Compose, PowerShell, AWS CLI → '
                '3) ZIP desde S3 → 4) .env público (POLYMER_PUBLIC_URL, URI de Google) → 5) JSON de Google desde SSM (si existe) → '
                "6) Caddy con Let's Encrypt → 7) polymer.ps1 start: genera las contraseñas, compila con las pruebas y espera 13 contenedores sanos.<br>"
                '<b>Actualizar:</b> terraform apply (sube un ZIP nuevo, no recrea la instancia) + <i>sudo polymer-update</i> en la instancia '
                '(conserva datos y secretos). <b>Borrar todo:</b> terraform destroy.',
        card('#FFF7ED', COMPUTE, 13, 'left'), 30, 1220, 2130, 110)

    dep, down, right = edge('#64748B'), (X('exit', 0.5, 1), X('entry', 0.5, 0)), (X('exit', 1, 0.5), X('entry', 0, 0.5))
    d.e('tfvars', 'vars', 'asigna', dep, *down)
    d.e('test', 'vars', 'mock_provider "aws"', edge('#475569', True), X('exit', 0, 0.5), X('entry', 0, 0.5), points=[(40, 875), (40, 380)])
    for child in ('pab', 'sse', 'own'):
        d.e('bucket', child, '', dep, *down)
    d.e('bucket', 'obj', '', dep, *right)
    for child in ('attach', 'policy', 'profile'):
        d.e('role', child, '', dep, *down)
    for child in ('http', 'https', 'egress'):
        d.e('sgr', child, '', dep, *down)
    d.e('d_zip', 'obj', 'archivo', dep, X('exit', 1, 0.5), X('entry', 0.5, 0), points=[(740, 180), (740, 140), (1153, 140)])
    d.e('d_id', 'policy', 'ARN del parámetro', dep, X('exit', 1, 0.8), X('entry', 0.5, 0), points=[(983, 613)])
    d.e('d_vpc', 'sgr', 'vpc_id', dep, *right)
    d.e('obj', 'inst', 'clave del ZIP', dep, X('exit', 1, 0.5), X('entry', 0.5, 0), points=[(1533, 193)])
    d.e('profile', 'inst', 'perfil', dep, X('exit', 1, 0.5), X('entry', 0, 0.4))
    d.e('eipr', 'inst', 'IP → dominio', dep, X('exit', 1, 0.5), X('entry', 0, 0.7), points=[(1460, 833), (1460, 686)])
    d.e('egress', 'inst', 'grupo de seguridad', dep, X('exit', 1, 0.5), X('entry', 0, 0.95), points=[(1420, 993), (1420, 703)])
    d.e('d_ami', 'inst', 'AMI', dep, X('exit', 1, 0.5), X('entry', 1, 0.2), points=[(1700, 1103), (1700, 653)])
    d.e('inst', 'assoc', '', dep, X('exit', 1, 0.8), X('entry', 1, 0.5), points=[(1640, 693), (1640, 993)])
    d.e('eipr', 'assoc', '', dep, X('exit', 1, 0.8), X('entry', 0.5, 0), points=[(1533, 853)])
    d.e('inst', 'cout', 'terraform output', edge('#15803D', width=2), X('exit', 1, 0.5), X('entry', 0, 0.52))
    return d


def er_page() -> str:
    xml, _ = base.drawio_page(base.er(), 3)
    return xml.replace(f'name="{base.tr("3 · Modelo de datos (E-R)")}"', f'name="{base.tr("3 · Entidad-relación (PostgreSQL · contenedor db)")}"', 1)


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    base.LANG = 'en' if argv[:2] == ['--lang', 'en'] else 'es'
    out = base.OUT / 'en' / OUT.name if base.LANG == 'en' else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    aws, tf = aws_page(), terraform_page()
    if base.LANG == 'en':
        er = base.er()
        base.diagram_i18n.check(aws.labels + tf.labels + [n['label'] for n in er.nodes] + [e['label'] for e in er.edges])
    pages = [aws.xml(1), tf.xml(2), er_page()]
    out.write_text('<mxfile host="app.diagrams.net" agent="POLYMER tools/diagramas/generate_aws_diagram.py">'
                   + ''.join(pages) + '</mxfile>\n', encoding='utf-8')
    print(f'OK: {out.relative_to(base.ROOT)} ({len(pages)} páginas)')


if __name__ == '__main__':
    main()
