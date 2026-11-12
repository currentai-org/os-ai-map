"""Build pipeline for the AI Stack Map.

Every module here reads the corpus through `yaml.safe_load`. PyYAML's default loader is pure
Python and parses the 20 MB `sources/` tree roughly 9x slower than libyaml, which made corpus
loads the dominant cost of CI. When PyYAML was built with libyaml, `safe_load` is routed through
`CSafeLoader`, which resolves the same YAML 1.1 safe schema; every committed .yaml file parses to
identical data under both loaders.
"""
import yaml

if getattr(yaml, "__with_libyaml__", False):
    def _c_safe_load(stream):
        return yaml.load(stream, Loader=yaml.CSafeLoader)

    yaml.safe_load = _c_safe_load
