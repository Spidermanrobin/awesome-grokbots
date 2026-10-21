"""Shared catalog loading. YAML files are the only editorial source."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("bots", "skills", "guides")
CATEGORIES = ("finance", "research", "content", "video", "skills", "guides")


class UniqueLoader(yaml.SafeLoader):
    pass


def mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def read_yaml(path):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueLoader)


def load_catalog(root=ROOT):
    return {kind: read_yaml(root / "data" / f"{kind}.yaml") for kind in KINDS}


def locales(root=ROOT):
    return {p.stem: read_yaml(p) for p in sorted((root / "i18n").glob("*.yaml"))}


def review(entry, lang):
    return entry["review_i18n"].get(lang, entry["review"])
