# ---------------------------------------------------------------------------------------------------------
# POLYMER en una sola instancia EC2: Docker Compose (13 contenedores) + Caddy como borde HTTPS.
#   Internet ─443/80─► Caddy (Let's Encrypt, HTTP→HTTPS, HSTS) ─► 127.0.0.1:8080 gateway POLYMER
# Lo ÚNICO público son los puertos 80 y 443. Sin SSH: la administración es por SSM Session Manager.
# ---------------------------------------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

data "aws_vpc" "default" {
  default = true
}

# Ubuntu 24.04 LTS (x86_64) oficial de Canonical: incluye el agente de SSM.
data "aws_ssm_parameter" "ubuntu_ami" {
  name = "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id"
}

locals {
  name        = "polymer"
  repo_root   = abspath("${path.module}/../../..")
  domain      = var.domain != "" ? var.domain : "${replace(aws_eip.polymer.public_ip, ".", "-")}.sslip.io"
  public_url  = "https://${local.domain}"
  ssm_param   = trimprefix(var.google_oauth_parameter, "/")
  archive_key = "source/polymer-${data.archive_file.source.output_md5}.zip"
}

# --- Código fuente: un ZIP del proyecto SIN secretos ------------------------------------------------------
# Se excluyen secrets/, .env, Git, el estado de Terraform y artefactos de compilación. Las contraseñas se
# generan DENTRO de la instancia (tools/init-env.ps1) y nunca salen de ella.
data "archive_file" "source" {
  type        = "zip"
  source_dir  = local.repo_root
  output_path = "${path.module}/.build/polymer-source.zip"
  excludes = [
    ".git/**", ".env", ".env.*", "secrets/**", "artifacts/**", ".tools/**", ".idea/**", ".vscode/**",
    "infra/aws/terraform/.terraform/**", "infra/aws/terraform/.build/**",
    "infra/aws/terraform/.terraform.lock.hcl", "infra/aws/terraform/*.tfstate", "infra/aws/terraform/*.tfstate.*", "infra/aws/terraform/*.tfvars",
    "**/node_modules/**", "**/target/**", "**/.venv/**", "**/__pycache__/**", "**/.pytest_cache/**",
    "tools/ui-e2e/screenshots/**", "**/*.zip", "**/*.pem", "**/*.key",
    "**/google-oauth*.json", "**/client_secret*.json", "**/*.apps.googleusercontent.com.json",
  ]
}

resource "aws_s3_bucket" "deploy" {
  bucket_prefix = "${local.name}-deploy-"
  force_destroy = true # solo guarda el ZIP del código: `terraform destroy` puede vaciarlo
}

resource "aws_s3_bucket_public_access_block" "deploy" {
  bucket                  = aws_s3_bucket.deploy.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "deploy" {
  bucket = aws_s3_bucket.deploy.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_ownership_controls" "deploy" {
  bucket = aws_s3_bucket.deploy.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_object" "source" {
  bucket = aws_s3_bucket.deploy.id
  key    = local.archive_key
  source = data.archive_file.source.output_path
  etag   = data.archive_file.source.output_md5
}

# --- Identidad de la instancia (sin claves de acceso) -----------------------------------------------------
resource "aws_iam_role" "instance" {
  name_prefix = "${local.name}-ec2-"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# Session Manager: consola y túneles a Grafana/RabbitMQ/Mailpit sin abrir el puerto 22.
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "deploy_read" {
  name = "${local.name}-deploy-read"
  role = aws_iam_role.instance.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadSourceArchive"
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.deploy.arn}/source/*"
      },
      {
        Sid      = "ListSourceArchives"
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.deploy.arn
      },
      {
        # Solo ESTE parámetro (cifrado con la clave administrada aws/ssm).
        Sid      = "ReadGoogleOAuthJson"
        Effect   = "Allow"
        Action   = ["ssm:GetParameter"]
        Resource = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/${local.ssm_param}"
      },
    ]
  })
}

resource "aws_iam_instance_profile" "instance" {
  name_prefix = "${local.name}-ec2-"
  role        = aws_iam_role.instance.name
}

# --- Red: solo HTTP (redirige a HTTPS y valida Let's Encrypt) y HTTPS ------------------------------------
resource "aws_security_group" "web" {
  name_prefix = "${local.name}-web-"
  description = "POLYMER: solo 80/443 publicos; sin SSH (se usa SSM)"
  vpc_id      = data.aws_vpc.default.id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.web.id
  description       = "HTTP: redireccion a HTTPS y desafio ACME de Lets Encrypt"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "https" {
  security_group_id = aws_security_group.web.id
  description       = "HTTPS: tienda POLYMER"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.web.id
  description       = "Salida: paquetes, imagenes Docker, Lets Encrypt, Google, SMTP 587"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# IP fija: el nombre (dominio o sslip.io) y la URI de retorno de Google no cambian al reiniciar la instancia.
resource "aws_eip" "polymer" {
  domain = "vpc"
  tags   = { Name = "${local.name}-ip" }
}

resource "aws_instance" "polymer" {
  ami                    = data.aws_ssm_parameter.ubuntu_ami.value
  instance_type          = var.instance_type
  iam_instance_profile   = aws_iam_instance_profile.instance.name
  vpc_security_group_ids = [aws_security_group.web.id]

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_gb
    encrypted             = true
    delete_on_termination = true
  }

  # IMDSv2 obligatorio (las credenciales del rol no se pueden robar con un SSRF simple).
  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  # Tipos t2/t3/t4g: modo «standard» para no pagar créditos de CPU extra (los *-flex no lo usan).
  dynamic "credit_specification" {
    for_each = can(regex("^t[0-9]", var.instance_type)) ? [1] : []
    content {
      cpu_credits = "standard"
    }
  }

  user_data = templatefile("${path.module}/templates/user-data.sh.tftpl", {
    region            = var.region
    bucket            = aws_s3_bucket.deploy.id
    archive_key       = aws_s3_object.source.key
    domain            = local.domain
    public_url        = local.public_url
    mode              = var.mode
    swap_gb           = var.swap_gb
    letsencrypt_email = var.letsencrypt_email
    google_parameter  = var.google_oauth_parameter
    caddyfile = templatefile("${path.module}/templates/Caddyfile.tftpl", {
      domain            = local.domain
      letsencrypt_email = var.letsencrypt_email
    })
  })
  # Un ZIP nuevo NO recrea la instancia (perderías la base de datos): se actualiza con `polymer-update`.
  user_data_replace_on_change = false

  lifecycle {
    ignore_changes = [ami, user_data]
  }

  tags = { Name = local.name }
}

resource "aws_eip_association" "polymer" {
  instance_id   = aws_instance.polymer.id
  allocation_id = aws_eip.polymer.id
}

# --- Alerta de presupuesto (opcional, gratis) -------------------------------------------------------------
resource "aws_budgets_budget" "monthly" {
  count        = var.budget_alert_email == "" ? 0 : 1
  name         = "${local.name}-mensual"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_limit_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_types {
    include_credit = false # muestra el consumo real aunque lo paguen los créditos del plan gratuito
    include_refund = false
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_alert_email]
  }
}
