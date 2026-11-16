variable "region" {
  description = "Región de AWS. us-east-1 suele ser la más barata; sa-east-1 (São Paulo) tiene menos latencia desde Perú."
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = <<-EOT
    Tipo de instancia. POLYMER completo (13 contenedores) necesita ~4,5 GB de RAM más la compilación:
      m7i-flex.large (2 vCPU, 8 GiB)  -> modo full.  Elegible en el plan gratuito de cuentas creadas desde el 15/07/2025.
      c7i-flex.large (2 vCPU, 4 GiB)  -> modo basic. Elegible en el plan gratuito de cuentas creadas desde el 15/07/2025.
      t3.micro / t2.micro (1 GiB)     -> NO alcanza para POLYMER (ni en modo basic).
    Comprueba la etiqueta «Free tier eligible» en la consola de EC2 de TU cuenta antes de aplicar.
  EOT
  type        = string
  default     = "m7i-flex.large"
}

variable "mode" {
  description = "Modo de POLYMER: full (13 contenedores: Redis, RabbitMQ, Mailpit, observabilidad) o basic (6 contenedores)."
  type        = string
  default     = "full"

  validation {
    condition     = contains(["full", "basic"], var.mode)
    error_message = "mode debe ser \"full\" o \"basic\"."
  }
}

variable "domain" {
  description = <<-EOT
    Dominio público de la tienda (registro A hacia la IP elástica, que muestra el output public_ip).
    Vacío = se usa <ip-con-guiones>.sslip.io, un nombre gratuito que apunta a la IP sin configurar DNS.
  EOT
  type        = string
  default     = ""

  validation {
    condition     = var.domain == "" || can(regex("^([a-z0-9]([a-z0-9-]*[a-z0-9])?\\.)+[a-z]{2,}$", var.domain))
    error_message = "domain debe ser un nombre de dominio en minúsculas (p. ej. tienda.midominio.com) o quedar vacío."
  }
}

variable "letsencrypt_email" {
  description = "Correo opcional para los avisos de Let's Encrypt (caducidad del certificado). Vacío = sin correo."
  type        = string
  default     = ""
}

variable "root_volume_gb" {
  description = "Disco raíz gp3 en GB. El plan gratuito incluye 30 GB de EBS."
  type        = number
  default     = 30

  validation {
    condition     = var.root_volume_gb >= 20
    error_message = "POLYMER necesita al menos 20 GB (imágenes Docker, volúmenes y compilación)."
  }
}

variable "swap_gb" {
  description = "Archivo de intercambio (swap) en GB; protege la compilación de Maven de quedarse sin memoria."
  type        = number
  default     = 4
}

variable "google_oauth_parameter" {
  description = <<-EOT
    Nombre del parámetro SecureString de SSM con el JSON de Google (opcional). Créalo TÚ con la AWS CLI
    (ver la guía) para que el secreto nunca pase por Terraform ni por su archivo de estado.
    Si el parámetro no existe, POLYMER arranca sin «Continuar con Google».
  EOT
  type        = string
  default     = "/polymer/google-oauth-json"
}

variable "budget_alert_email" {
  description = "Correo para una alerta de presupuesto de AWS (gratis). Vacío = no se crea la alerta (recomendado ponerlo)."
  type        = string
  default     = ""
}

variable "budget_limit_usd" {
  description = "Límite mensual en USD de la alerta. Mide el consumo ANTES de créditos: así ves cuánto crédito gastas."
  type        = number
  default     = 20
}
