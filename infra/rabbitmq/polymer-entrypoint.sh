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
# La contraseña viaja por la entrada estándar, nunca en la línea de comandos.
users() { rabbitmqctl -q list_users --no-table-headers 2>/dev/null | cut -f1; }
(
  tries=0
  until rabbitmq-diagnostics -q check_running >/dev/null 2>&1; do
    tries=$((tries + 1)); [ "$tries" -gt 150 ] && exit 0; sleep 2
  done
  if ! users | grep -qx "$user"; then
    printf '%s' "$password" | rabbitmqctl -q add_user "$user" >/dev/null \
      && rabbitmqctl -q set_user_tags "$user" administrator >/dev/null \
      && rabbitmqctl -q set_permissions -p / "$user" '.*' '.*' '.*' >/dev/null \
      && echo "POLYMER: usuario de RabbitMQ «$user» creado con la contraseña de secrets/rabbitmq_password.txt"
  fi
  if [ "$legacy" != "$user" ] && users | grep -qx "$legacy"; then
    if printf '%s' "$password" | rabbitmqctl -q authenticate_user "$user" >/dev/null 2>&1; then
      rabbitmqctl -q delete_user "$legacy" >/dev/null && echo "POLYMER: usuario heredado «$legacy» eliminado (migrado a «$user»)"
    else
      echo "POLYMER: «$user» no se pudo autenticar; se conserva el usuario heredado «$legacy»" >&2
    fi
  fi
) &

exec docker-entrypoint.sh "$@"
