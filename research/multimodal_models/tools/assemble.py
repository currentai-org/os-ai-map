T='research/multimodal_models/tools/'; D='research/multimodal_models'
rows=open(f'{D}/rows.yaml').read()
out=open(T+'head.md').read()
out+="\n## 6. Accepted candidates\n\n### 6a. Registry rows (YAML, exact schema, paste-ready)\n\nAlso written to `rows.yaml`, which validates against `docs/schemas/registry.schema.json`. None of these slugs or artifacts is in `corpus-index.tsv`, `sources/products/` or `sources/registry/`. 13 of the org slugs are new (section 9, Q12).\n\n```yaml\n"+rows+"```\n\n"
out+="### 6b. Evidence table, one row per candidate\n\nAdoption is the sum of rolling 30-day Hub downloads over the vendor's own member checkpoints in the cited family listing (third-party quantizations and excluded lines left out). Last release = newest member checkpoint's `createdAt`.\n\n"+open(T+'t6b.md').read()+"\n\n"
out+="### 6c. Source list: every id cited anywhere in this document (ranges expanded), with fetch time (all 2026-09-26 UTC)\n\n"+open(T+'t6c.md').read()+"\n\n"
out+="## 7. Parked candidates\n\n"+open(T+'t7.md').read()+"\n"
out+=open(T+'tail.md').read()
open(f'{D}/sweep.md','w').write(out); print(len(out))
