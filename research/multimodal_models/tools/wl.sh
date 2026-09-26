#!/usr/bin/env bash
# usage: wl.sh <tool> <query_or_url> <excerpt>
f=/home/user/os-ai-map/research/multimodal_models/web-log.tsv
n=$(( $(wc -l < "$f") ))
id=$(printf "W%04d" "$n")
ex=$(printf "%s" "$3" | tr '\t\n' '  ')
printf "%s\t%s\t%s\t%s\t%s\n" "$id" "$(date -u +%FT%TZ)" "$1" "$2" "$ex" >> "$f"
echo $id
