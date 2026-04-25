#!/usr/bin/env bash

echo "=== DNS Resolution ==="
getent hosts forge-web forge-internal forge-db forge-privesc

echo
echo "=== Web Preview ==="
curl -s http://forge-web:8080 | head -n 5

echo
echo "=== Fast Port Scan ==="
nmap -F forge-web forge-internal forge-privesc || echo "nmap not available"

echo
echo "=== DB Connectivity Check ==="
psql -h forge-db -U app -d appdb -c '\l' 2>/dev/null || echo "psql failed or auth required"
