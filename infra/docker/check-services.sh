#!/bin/bash

echo "🔍 Checking service health..."

services=("postgres:5432" "redis:6379" "mosquitto:1883" "nats:4222" "qdrant:6333")

all_healthy=true

for service in "${services[@]}"; do
  IFS=':' read -r name port <<< "$service"
  
  if nc -z localhost "$port" 2>/dev/null; then
    echo "✅ $name is healthy (port $port)"
  else
    echo "❌ $name is not responding (port $port)"
    all_healthy=false
  fi
done

if [ "$all_healthy" = true ]; then
  echo ""
  echo "🎉 All services are healthy!"
  exit 0
else
  echo ""
  echo "⚠️  Some services are not healthy. Check docker-compose logs."
  exit 1
fi