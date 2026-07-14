"""FruitForest playback routing."""

import re
from typing import Any

from homeassistant.components.media_player.const import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .models import PlaybackTarget, build_search_phrase


async def async_play(
    hass: HomeAssistant,
    target: PlaybackTarget,
    payload: dict[str, Any],
) -> str:
    """Send an Apple Music request to an Echo device or Alexa group."""
    if not target.available:
        raise HomeAssistantError(
            f"{target.name} ({target.entity_id}) is unavailable. "
            "Alexa Media Player may need to be reauthenticated."
        )

    search_phrase = build_search_phrase(
        str(payload.get("kind", "freeform")),
        title=str(payload.get("title", "")),
        artist=str(payload.get("artist", "")),
        name=str(payload.get("name", "")),
    )
    if not search_phrase:
        raise HomeAssistantError(
            "No music title, playlist, or freeform request was provided."
        )

    if target.kind == "group":
        media_content_type = "custom"
        media_content_id = (
            f"play {search_phrase} on apple music on {target.phrase or target.name}"
        )
    else:
        media_content_type = "APPLE_MUSIC"
        media_content_id = search_phrase

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        "play_media",
        {
            ATTR_ENTITY_ID: target.entity_id,
            "media_content_type": media_content_type,
            "media_content_id": media_content_id,
        },
        blocking=True,
    )
    return media_content_id


async def async_notify_failure(
    hass: HomeAssistant, message: str, sender: str = ""
) -> None:
    """Record a failure and optionally notify the sending companion app."""
    if hass.services.has_service("persistent_notification", "create"):
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {"title": "FruitForest failed", "message": message},
            blocking=False,
        )

    if not re.fullmatch(r"[a-z0-9_]+", sender):
        return

    service = f"mobile_app_{sender}"
    if hass.services.has_service("notify", service):
        await hass.services.async_call(
            "notify",
            service,
            {"title": "FruitForest failed", "message": message},
            blocking=False,
        )
