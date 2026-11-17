# Prueba SIN cuenta de AWS (proveedor simulado): `terraform test`. Comprueba el nombre HTTPS, la URI de
# Google, el user-data y que el ZIP del código no lleve secretos. No crea ningún recurso real.
mock_provider "aws" {
  override_data {
    target = data.aws_ssm_parameter.ubuntu_ami
    values = { value = "ami-0123456789abcdef0" }
  }
  override_data {
    target = data.aws_vpc.default
    values = { id = "vpc-0123456789abcdef0" }
  }
  override_data {
    target = data.aws_caller_identity.current
    values = { account_id = "123456789012" }
  }
  override_resource {
    target = aws_eip.polymer
    values = { public_ip = "203.0.113.10", id = "eipalloc-0123456789abcdef0" }
  }
  override_resource {
    target = aws_s3_bucket.deploy
    values = { id = "polymer-deploy-test", arn = "arn:aws:s3:::polymer-deploy-test" }
  }
}

run "sslip_por_defecto" {
  command = apply

  assert {
    condition     = output.url == "https://203-0-113-10.sslip.io"
    error_message = "Sin dominio debe usarse <ip>.sslip.io por HTTPS"
  }
  assert {
    condition     = !strcontains(aws_instance.polymer.user_data, "redir ")
    error_message = "Sin dominio propio no hay redirección www"
  }
  assert {
    condition     = output.google_redirect_uri == "https://203-0-113-10.sslip.io/login/oauth2/code/google"
    error_message = "URI de retorno de Google incorrecta"
  }
  assert {
    condition     = strcontains(aws_instance.polymer.user_data, "POLYMER_PUBLIC_URL=https://203-0-113-10.sslip.io")
    error_message = "El .env de producción debe llevar la URL pública HTTPS"
  }
  assert {
    condition     = strcontains(aws_instance.polymer.user_data, "tools/polymer.ps1 start -Mode full -AssumeYes")
    error_message = "Debe arrancar POLYMER en modo full"
  }
  assert {
    condition     = strcontains(aws_instance.polymer.user_data, "203-0-113-10.sslip.io {") && strcontains(aws_instance.polymer.user_data, "reverse_proxy 127.0.0.1:8080")
    error_message = "Caddy debe servir el dominio y apuntar al gateway local"
  }
  assert {
    condition     = length(aws_instance.polymer.credit_specification) == 0
    error_message = "Los tipos *-flex no llevan credit_specification"
  }
  assert {
    condition     = aws_instance.polymer.metadata_options[0].http_tokens == "required"
    error_message = "IMDSv2 obligatorio"
  }
  # AWS solo admite a-zA-Z0-9. _-:/()#,@[]+=&;{}!$* en las descripciones (sin apóstrofos ni tildes).
  assert {
    condition = alltrue([for d in [aws_security_group.web.description, aws_vpc_security_group_ingress_rule.http.description,
      aws_vpc_security_group_ingress_rule.https.description, aws_vpc_security_group_egress_rule.all.description] :
    can(regex("^[a-zA-Z0-9. _:/()#,@\\[\\]+=&;{}!$*-]{0,255}$", d))])
    error_message = "Descripción de grupo de seguridad con caracteres que AWS rechaza"
  }
  assert {
    condition     = length(aws_budgets_budget.monthly) == 0
    error_message = "Sin correo no se crea la alerta"
  }
}

run "dominio_propio_basic" {
  command   = apply
  state_key = "dominio_propio" # estado aparte: user_data se ignora en cambios (no recrea la instancia)

  variables {
    domain             = "tienda.midominio.com"
    mode               = "basic"
    instance_type      = "t3.small"
    letsencrypt_email  = "avisos@midominio.com"
    budget_alert_email = "avisos@midominio.com"
  }

  assert {
    condition     = output.url == "https://tienda.midominio.com"
    error_message = "Debe usar el dominio indicado"
  }
  assert {
    condition     = strcontains(aws_instance.polymer.user_data, "www.tienda.midominio.com {") && strcontains(aws_instance.polymer.user_data, "redir https://tienda.midominio.com{uri} permanent")
    error_message = "www.<dominio> debe redirigir al dominio principal"
  }
  assert {
    condition     = output.dns_records == "A  tienda.midominio.com  ->  203.0.113.10  |  A  www.tienda.midominio.com  ->  203.0.113.10"
    error_message = "Los registros DNS a crear deben incluir el dominio y www"
  }
  assert {
    condition     = strcontains(aws_instance.polymer.user_data, "-Mode basic") && strcontains(aws_instance.polymer.user_data, "email avisos@midominio.com")
    error_message = "Modo basic y correo de Let's Encrypt"
  }
  assert {
    condition     = aws_instance.polymer.credit_specification[0].cpu_credits == "standard"
    error_message = "Los t3 deben ir en modo standard (sin cargos de CPU extra)"
  }
  assert {
    condition     = length(aws_budgets_budget.monthly) == 1
    error_message = "Con correo se crea la alerta de presupuesto"
  }
}

run "modo_invalido" {
  command = plan
  variables {
    mode = "todo"
  }
  expect_failures = [var.mode]
}
