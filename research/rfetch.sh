#!/usr/bin/env bash
# Usage: research/rfetch.sh <category_slug> <url> [label]
# Fetches <url> live, saves the body under research/<slug>/raw/, appends a row to
# research/<slug>/fetch-log.tsv (id, utc timestamp, http code, bytes, sha256, url, label),
# and prints the fetch id and the saved path. Use it for EVERY curl-able fact.
set -u
slug="$1"; url="$2"; label="${3:-}"
here="$(cd "$(dirname "$0")" && pwd)"; dir="$here/$slug"; mkdir -p "$dir/raw"
log="$dir/fetch-log.tsv"; [ -f "$log" ] || printf "id\tfetched_at_utc\thttp\tbytes\tsha256\turl\tlabel\n" > "$log"
exec 9>"$dir/.lock"; flock 9
n=$(( $(wc -l < "$log") ))
id=$(printf "F%04d" "$n")
out="$dir/raw/$id.body"
printf "%s\tPENDING\t\t\t\t%s\t%s\n" "$id" "$url" "$label" >> "$log"
flock -u 9
hdr=()
case "$url" in https://api.github.com/*) hdr=(-H "Authorization: Bearer ${GITHUB_TOKEN:-}");; esac
code=$(curl -sSL --max-time 40 "${hdr[@]}" -A "os-ai-map-research" -o "$out" -w "%{http_code}" "$url" 2>/dev/null || echo 000)
bytes=$(wc -c < "$out" 2>/dev/null || echo 0)
sha=$(sha256sum "$out" | cut -d' ' -f1)
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
# Bodies over 1 MB keep their first 300 KB on disk; bytes and sha256 describe the FULL body.
if [ "$bytes" -gt 1000000 ]; then head -c 300000 "$out" > "$out.tmp" && mv "$out.tmp" "$out"; label="$label [truncated-to-300KB]"; fi
flock 9; ID="$id" ROW="$(printf "%s\t%s\t%s\t%s\t%s\t%s\t%s" "$id" "$ts" "$code" "$bytes" "$sha" "$url" "$label")" awk -F"\t" '$1==ENVIRON["ID"] && $2=="PENDING"{print ENVIRON["ROW"]; next} {print}' "$log" > "$log.tmp" && mv "$log.tmp" "$log"; flock -u 9
echo "$id http=$code bytes=$bytes $out"
