"""Build FruitForest destinations from Home Assistant registries."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_FRIENDLY_NAME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import CONF_ECHO_ENTITIES, CONF_GROUP_CARRIER, CONF_GROUPS
from .models import PlaybackTarget, disambiguate_targets


def _entity_area_name(hass: HomeAssistant, entity_id: str) -> str | None:
    """Return the entity's explicitly or indirectly assigned Area name."""
    entity_entry = er.async_get(hass).async_get(entity_id)
    if entity_entry is None:
        return None

    area_id = entity_entry.area_id
    if area_id is None and entity_entry.device_id is not None:
        device = dr.async_get(hass).async_get(entity_entry.device_id)
        if device is not None:
            area_id = device.area_id

    if area_id is None:
        return None

    area = ar.async_get(hass).async_get_area(area_id)
    return area.name if area is not None else None


def _entity_name(hass: HomeAssistant, entity_id: str) -> str:
    """Return a readable fallback name for an entity."""
    state = hass.states.get(entity_id)
    if state is not None:
        return str(state.attributes.get(ATTR_FRIENDLY_NAME, entity_id))
    return entity_id


def _is_available(hass: HomeAssistant, entity_id: str) -> bool:
    state = hass.states.get(entity_id)
    return state is not None and state.state not in {STATE_UNAVAILABLE, STATE_UNKNOWN}


def build_targets(hass: HomeAssistant, entry: ConfigEntry) -> list[PlaybackTarget]:
    """Build the current destination list from the config entry and registries."""
    options = entry.options
    echo_entities = options.get(
        CONF_ECHO_ENTITIES, entry.data.get(CONF_ECHO_ENTITIES, [])
    )
    groups = options.get(CONF_GROUPS, {})

    targets: list[PlaybackTarget] = []
    for entity_id in echo_entities:
        entity_name = _entity_name(hass, entity_id)
        display_name = _entity_area_name(hass, entity_id) or entity_name
        targets.append(
            PlaybackTarget(
                target_id="",
                name=display_name,
                kind="device",
                entity_id=entity_id,
                available=_is_available(hass, entity_id),
                fallback_name=entity_name,
            )
        )

    for group_name, group_config in groups.items():
        carrier = group_config[CONF_GROUP_CARRIER]
        targets.append(
            PlaybackTarget(
                target_id="",
                name=group_name,
                kind="group",
                entity_id=carrier,
                available=_is_available(hass, carrier),
                phrase=group_name,
                fallback_name="Group",
            )
        )

    return disambiguate_targets(targets)


def resolve_target(
    targets: list[PlaybackTarget], requested_target: str
) -> PlaybackTarget | None:
    """Resolve either a public id or display name, case-insensitively."""
    requested = requested_target.strip().casefold()
    return next(
        (
            target
            for target in targets
            if requested in {target.target_id.casefold(), target.name.casefold()}
        ),
        None,
    )
