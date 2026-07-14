"""Diagnostics support for FruitForest."""

from typing import Any

from homeassistant.core import HomeAssistant

from . import FruitForestConfigEntry
from .const import CONF_WEBHOOK_ID
from .targets import build_targets


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: FruitForestConfigEntry
) -> dict[str, Any]:
    """Return diagnostics without exposing the private webhook id."""
    return {
        "entry_data": {
            key: "REDACTED" if key == CONF_WEBHOOK_ID else value
            for key, value in entry.data.items()
        },
        "options": dict(entry.options),
        "targets": [target.as_dict() for target in build_targets(hass, entry)],
    }
