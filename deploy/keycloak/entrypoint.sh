#!/bin/bash
# Dev entrypoint: start Keycloak over HTTP, then set sslRequired=NONE on
# master (admin console) and retail. Master defaults to sslRequired=external,
# which rejects HTTP when the client IP is not loopback (Docker/proxy).
set -eu

/opt/keycloak/bin/kc.sh start-dev \
  --import-realm \
  --http-port=8080 \
  --http-enabled=true \
  --hostname=http://localhost:8080 \
  --hostname-strict=false &
KC_PID=$!

echo "Waiting for Keycloak admin API..."
i=0
while [ "$i" -lt 90 ]; do
  if /opt/keycloak/bin/kcadm.sh config credentials \
      --server http://127.0.0.1:8080 \
      --realm master \
      --user admin \
      --password admin >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 2
done

echo "Relaxing SSL requirement for local HTTP (master + retail)..."
/opt/keycloak/bin/kcadm.sh update realms/master -s sslRequired=NONE
/opt/keycloak/bin/kcadm.sh update realms/retail -s sslRequired=NONE || true

wait "$KC_PID"
