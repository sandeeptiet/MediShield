#!/usr/bin/env bash
# Deploy MediShield to a running CRC (OpenShift Local) cluster.
#
# Pre-requisites:
#   - `oc` CLI on PATH
#   - You are logged in:  oc login -u developer https://api.crc.testing:6443
#   - .env file in project root with real ANTHROPIC_API_KEY etc.
#
# Usage:
#   ./deploy/openshift/deploy.sh
#
# Idempotent: re-run after edits; it patches instead of failing on existing
# resources.

set -euo pipefail

NAMESPACE="medishield"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="${ROOT}/.env"

step() { printf "\n\033[1;34m▶ %s\033[0m\n" "$*"; }

if ! command -v oc >/dev/null; then
  echo "oc CLI not found on PATH. Install Red Hat OpenShift Local first."
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing .env at $ENV_FILE — copy .env.example and fill it in."
  exit 1
fi

step "1. Ensure project '$NAMESPACE' exists"
oc get ns "$NAMESPACE" >/dev/null 2>&1 || oc new-project "$NAMESPACE"
oc project "$NAMESPACE" >/dev/null

step "2. Create / refresh medishield-secrets from .env"
oc delete secret medishield-secrets --ignore-not-found
# Keep only the keys the manifests actually reference.
TMP_ENV="$(mktemp)"
grep -E '^(ANTHROPIC_API_KEY|GOOGLE_CLIENT_ID|GOOGLE_CLIENT_SECRET|JWT_SECRET|NEXTAUTH_SECRET|LANGSMITH_API_KEY|MYSQL_PASSWORD|MYSQL_ROOT_PASSWORD)=' \
  "$ENV_FILE" > "$TMP_ENV"
oc create secret generic medishield-secrets --from-env-file="$TMP_ENV"
rm -f "$TMP_ENV"

step "3. Build the backend image (binary build from ./backend)"
oc get bc backend >/dev/null 2>&1 || \
  oc new-build --binary --name=backend --strategy=docker --to=backend:latest
oc start-build backend --from-dir="$ROOT/backend" --follow

step "4. Build the frontend image"
oc get bc frontend >/dev/null 2>&1 || \
  oc new-build --binary --name=frontend --strategy=docker --to=frontend:latest
oc start-build frontend --from-dir="$ROOT/frontend" --follow

step "5. Apply manifests"
oc apply -f "$ROOT/deploy/openshift/00-namespace.yaml"
oc apply -f "$ROOT/deploy/openshift/11-configmap.yaml"
oc apply -f "$ROOT/deploy/openshift/20-mysql.yaml"
oc apply -f "$ROOT/deploy/openshift/22-qdrant.yaml"
oc apply -f "$ROOT/deploy/openshift/30-backend.yaml"
oc apply -f "$ROOT/deploy/openshift/31-frontend.yaml"

step "6. Wait for rollouts"
for d in mysql qdrant backend frontend; do
  oc rollout status deployment/$d --timeout=10m
done

step "7. Routes"
oc get route -o custom-columns=NAME:.metadata.name,HOST:.spec.host

step "8. Seed users (one-shot via the backend pod)"
BACKEND_POD="$(oc get pod -l app=backend -o jsonpath='{.items[0].metadata.name}')"
oc exec "$BACKEND_POD" -- python -m scripts.seed_users || \
  echo "(seed_users failed — edit scripts/seed_users.py to add your Gmail then re-run)"

echo
echo "✓ Done. Visit the frontend route printed above."
