#!/usr/bin/env bash
cd /home/user/os-ai-map && git fetch -q --prune origin
for d in speech_audio classic_ml_cv multimodal_models federated_learning assurance_evidence datacenter_accelerators media_generation robotics_embodied model_hubs; do
  b=origin/claude/promote-$d
  if git rev-parse -q --verify $b >/dev/null; then
    printf "%-24s %s | +%s products | %s\n" $d "$(git log -1 --format='%cI' $b | cut -c12-16)" "$(git diff --name-only --diff-filter=A origin/main...$b -- sources/products | wc -l)" "$(git log -1 --format='%s' $b | cut -c1-70)"
  else printf "%-24s -\n" $d; fi
done
