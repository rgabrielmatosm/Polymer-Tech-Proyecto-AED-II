output "url" {
  description = "Tienda POLYMER por HTTPS (disponible ~15-25 min después del apply: compila y prueba las imágenes)."
  value       = local.public_url
}

output "public_ip" {
  description = "IP elástica. Si usas tu dominio, crea un registro A con esta IP."
  value       = aws_eip.polymer.public_ip
}

output "domain" {
  value = local.domain
}

output "instance_id" {
  value = aws_instance.polymer.id
}

output "google_redirect_uri" {
  description = "Añádela en Google Cloud → Credenciales → tu cliente OAuth → URI de redireccionamiento autorizados."
  value       = "${local.public_url}/login/oauth2/code/google"
}

output "ver_progreso" {
  description = "Progreso del despliegue dentro de la instancia (requiere AWS CLI + Session Manager plugin)."
  value       = "aws ssm start-session --region ${var.region} --target ${aws_instance.polymer.id}   # luego: sudo tail -f /var/log/polymer-deploy.log"
}

output "tunel_grafana" {
  description = "Grafana (y del mismo modo 8025 Mailpit, 15672 RabbitMQ, 9091 Prometheus) por túnel SSM, sin abrir puertos."
  value       = "aws ssm start-session --region ${var.region} --target ${aws_instance.polymer.id} --document-name AWS-StartPortForwardingSession --parameters portNumber=3000,localPortNumber=3000"
}
