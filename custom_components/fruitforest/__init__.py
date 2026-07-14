"""FruitForest: play Apple Music in the Amazon Forest."""

from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, cast

from aiohttp import web
import voluptuous as vol

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import (
    ConfigEntryError,
    HomeAssistantError,
    ServiceValidationError,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_WEBHOOK_ID,
    DOMAIN,
    PLAYBACK_KINDS,
    SERVICE_GET_TARGETS,
    SERVICE_PLAY,
    WEBHOOK_NAME,
)
from .playback import async_notify_failure, async_play
from .targets import build_targets, resolve_target

PLAY_SCHEMA = vol.Schema(
    {
        vol.Required("target"): cv.string,
        vol.Optional("kind", default="freeform"): vol.In(PLAYBACK_KINDS),
        vol.Optional("title", default=""): cv.string,
        vol.Optional("artist", default=""): cv.string,
        vol.Optional("name", default=""): cv.string,
        vol.Optional("sender", default=""): cv.string,
    }
)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@dataclass(slots=True)
class FruitForestRuntimeData:
    """Runtime state for the FruitForest config entry."""

    webhook_id: str


type FruitForestConfigEntry = ConfigEntry[FruitForestRuntimeData]


def _loaded_entry(hass: HomeAssistant) -> FruitForestConfigEntry:
    entries = hass.config_entries.async_entries(DOMAIN)
    entry = next(
        (entry for entry in entries if entry.state is ConfigEntryState.LOADED), None
    )
    if entry is None:
        raise ServiceValidationError("FruitForest is not configured or loaded.")
    return cast(FruitForestConfigEntry, entry)


def _target_response(
    hass: HomeAssistant, entry: FruitForestConfigEntry
) -> dict[str, Any]:
    targets = build_targets(hass, entry)
    return {
        "version": 1,
        "targets": [target.name for target in targets],
        "items": [target.as_dict() for target in targets],
    }


async def _play_payload(
    hass: HomeAssistant, entry: FruitForestConfigEntry, payload: dict[str, Any]
) -> dict[str, Any]:
    requested_target = str(payload.get("target", ""))
    target = resolve_target(build_targets(hass, entry), requested_target)
    if target is None:
        known = ", ".join(item.name for item in build_targets(hass, entry)) or "none"
        raise HomeAssistantError(
            f'Unknown target "{requested_target}". Known targets: {known}.'
        )

    media_content_id = await async_play(hass, target, payload)
    return {
        "ok": True,
        "target": target.name,
        "target_id": target.target_id,
        "request": media_content_id,
    }


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register FruitForest actions."""

    async def handle_play(call: ServiceCall) -> None:
        entry = _loaded_entry(hass)
        try:
            await _play_payload(hass, entry, dict(call.data))
        except HomeAssistantError as err:
            await async_notify_failure(hass, str(err), str(call.data.get("sender", "")))
            raise ServiceValidationError(str(err)) from err

    async def handle_get_targets(call: ServiceCall) -> ServiceResponse:
        return _target_response(hass, _loaded_entry(hass))

    hass.services.async_register(
        DOMAIN,
        SERVICE_PLAY,
        handle_play,
        schema=PLAY_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_TARGETS,
        handle_get_targets,
        supports_response=SupportsResponse.ONLY,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: FruitForestConfigEntry) -> bool:
    """Set up FruitForest from a config entry."""
    webhook_id = entry.data[CONF_WEBHOOK_ID]
    entry.runtime_data = FruitForestRuntimeData(webhook_id=webhook_id)

    async def handle_webhook(
        hass: HomeAssistant, received_webhook_id: str, request: web.Request
    ) -> web.Response:
        if request.method == "GET":
            return web.json_response(_target_response(hass, entry))

        try:
            payload = await request.json()
        except (ValueError, TypeError):
            return web.json_response(
                {"ok": False, "error": "Expected a JSON request body."},
                status=HTTPStatus.BAD_REQUEST,
            )

        if not isinstance(payload, dict):
            return web.json_response(
                {"ok": False, "error": "Expected a JSON object."},
                status=HTTPStatus.BAD_REQUEST,
            )

        payload.setdefault("kind", "freeform")
        try:
            result = await _play_payload(hass, entry, payload)
        except HomeAssistantError as err:
            message = str(err)
            await async_notify_failure(hass, message, str(payload.get("sender", "")))
            return web.json_response(
                {"ok": False, "error": message},
                status=HTTPStatus.UNPROCESSABLE_ENTITY,
            )
        return web.json_response(result, status=HTTPStatus.ACCEPTED)

    try:
        webhook.async_register(
            hass,
            DOMAIN,
            WEBHOOK_NAME,
            webhook_id,
            handle_webhook,
            local_only=True,
            allowed_methods={"GET", "POST"},
        )
    except ValueError as err:
        raise ConfigEntryError(
            "The configured webhook ID is already registered. Remove or disable "
            "the old Play on Echo package automation, then reload FruitForest."
        ) from err

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: FruitForestConfigEntry
) -> bool:
    """Unload a FruitForest config entry."""
    webhook.async_unregister(hass, entry.runtime_data.webhook_id)
    return True


async def _async_reload_entry(
    hass: HomeAssistant, entry: FruitForestConfigEntry
) -> None:
    """Reload FruitForest when its UI-managed options change."""
    await hass.config_entries.async_reload(entry.entry_id)
