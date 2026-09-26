#!/usr/bin/env bash
# Usage: wlog.sh <tool> <query-or-url> <excerpt>  -> appends a Wnnnn row to web-log.tsv
d="$(cd "$(dirname "$0")" && pwd)"; log="$d/web-log.tsv"
[ -f "$log" ] || printf "id\tutc\ttool\tquery_or_url\texcerpt\n" > "$log"
n=$(( $(wc -l < "$log") )); id=$(printf "W%04d" "$n")
ex=$(printf "%s" "$3" | tr '\t\n' '  ' | cut -c1-300)
printf "%s\t%s\t%s\t%s\t%s\n" "$id" "$(date -u +%FT%TZ)" "$1" "$2" "$ex" >> "$log"; echo "$id"
