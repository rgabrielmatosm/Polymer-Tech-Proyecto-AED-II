#!/bin/sh
# Lee la contraseña del secreto de Docker y genera la configuración de credenciales en un tmpfs
# (/etc/rabbitmq/conf.d), porque el sistema de archivos del contenedor es de solo lectura.
set -eu
secret=/run/secrets/rabbitmq_password
if [ ! -f "$secret" ]; then
  echo "Falta el secreto $secret (genera secrets\\rabbitmq_password.txt con .\\polymer.cmd secrets)" >&2
  exit 1
fi
password=$(tr -d '\r\n' < "$secret")
user="${RABBITMQ_USER:-polymer}"
legacy="${RABBITMQ_LEGACY_USER:-hexaorders}"
umask 027
mkdir -p /etc/rabbitmq/conf.d
printf 'default_user = %s\ndefault_pass = %s\ndefault_vhost = /\n' "$user" "$password" > /etc/rabbitmq/conf.d/20-credentials.conf
chown rabbitmq:rabbitmq /etc/rabbitmq/conf.d/20-credentials.conf

# Migración del usuario de versiones anteriores (HexaOrders): default_user solo se aplica a un nodo NUEVO, así
# que en un volumen existente se crea «polymer» con la MISMA contraseña del secreto (no cambia ninguna
# credencial) y el usuario heredado se elimina solo después de comprobar que «polymer» se autentica.
# Cada paso deja una línea «POLYMER:» en el log del contenedor (también los errores).
migrate_user() {
  log() { echo "POLYMER: $*"; }
  log "esperando a que RabbitMQ arranque para revisar el usuario «$user»"
  if ! rabbitmqctl await_startup --timeout 600 >/dev/null; then
    log "RabbitMQ no terminó de arrancar; no se revisan los usuarios" >&2
    return 1
  fi
  existing=$(rabbitmqctl -q list_users --no-table-headers | cut -f1) || return 1
  if ! printf '%s\n' "$existing" | grep -qx "$user"; then
    # La contraseña solo aparece en la lista de procesos de este contenedor aislado, durante el comando.
    rabbitmqctl -q add_user "$user" "$password" >/dev/null || return 1
    rabbitmqctl -q set_user_tags "$user" administrator >/dev/null || return 1
    rabbitmqctl -q set_permissions -p / "$user" '.*' '.*' '.*' >/dev/null || return 1
    log "usuario «$user» creado con la contraseña de secrets/rabbitmq_password.txt"
  fi
  if [ "$legacy" != "$user" ] && printf '%s\n' "$existing" | grep -qx "$legacy"; then
    if rabbitmqctl -q authenticate_user "$user" "$password" >/dev/null; then
      rabbitmqctl -q delete_user "$legacy" >/dev/null || return 1
      log "usuario heredado «$legacy» eliminado (migrado a «$user»)"
    else
      log "«$user» no se pudo autenticar; se conserva el usuario heredado «$legacy»" >&2
    fi
  fi
  log "usuarios de RabbitMQ revisados"
}
( migrate_user || echo "POLYMER: la revisión del usuario de RabbitMQ falló (ver el error anterior)" >&2 ) &

exec docker-entrypoint.sh "$@"
