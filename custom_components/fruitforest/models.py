"""Data models and pure helpers for FruitForest."""

from dataclasses import dataclass, replace
import re


@dataclass(frozen=True, slots=True)
class PlaybackTarget:
    """A destination shown to FruitForest clients."""

    target_id: str
    name: str
    kind: str
    entity_id: str
    available: bool
    phrase: str | None = None
    fallback_name: str | None = None

    def as_dict(self) -> dict[str, str | bool]:
        """Return the public target representation."""
        return {
            "id": self.target_id,
            "name": self.name,
            "type": self.kind,
            "available": self.available,
        }


def slugify(value: str) -> str:
    """Create a stable, Shortcut-friendly identifier."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "echo"


def disambiguate_targets(targets: list[PlaybackTarget]) -> list[PlaybackTarget]:
    """Give duplicate display names and ids deterministic unique values."""
    name_counts: dict[str, int] = {}
    for target in targets:
        key = target.name.casefold()
        name_counts[key] = name_counts.get(key, 0) + 1

    named: list[PlaybackTarget] = []
    for target in targets:
        if name_counts[target.name.casefold()] == 1:
            named.append(target)
            continue

        suffix = target.fallback_name or target.kind.title()
        named.append(replace(target, name=f"{target.name} ({suffix})"))

    used_ids: set[str] = set()
    result: list[PlaybackTarget] = []
    for target in named:
        base_id = slugify(target.name)
        target_id = base_id
        counter = 2
        while target_id in used_ids:
            target_id = f"{base_id}-{counter}"
            counter += 1
        used_ids.add(target_id)
        result.append(replace(target, target_id=target_id))

    return result


def build_search_phrase(
    kind: str,
    *,
    title: str = "",
    artist: str = "",
    name: str = "",
) -> str:
    """Build the Alexa search phrase proven by the original YAML package."""
    if kind == "track":
        return f"{title}{f' by {artist}' if artist else ''}".strip()
    if kind == "album":
        return f"the album {title}{f' by {artist}' if artist else ''}".strip()
    if kind == "playlist":
        return f"the playlist {name}".strip()
    return title.strip()
