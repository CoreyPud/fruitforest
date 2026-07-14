"""Config flow for FruitForest."""

from typing import Any, override

import voluptuous as vol

from homeassistant.components import webhook
from homeassistant.components.media_player.const import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_ECHO_ENTITIES,
    CONF_GROUP_CARRIER,
    CONF_GROUP_NAME,
    CONF_GROUPS,
    CONF_WEBHOOK_ID,
    DOMAIN,
)

ECHO_PLATFORMS = {"alexa_devices", "alexa_media"}


def _echo_selector(
    hass: HomeAssistant, selected: list[str] | None = None, *, multiple: bool
) -> EntitySelector:
    """Return an entity picker focused on discovered Alexa media players."""
    registry = er.async_get(hass)
    discovered = {
        entry.entity_id
        for entry in registry.entities.values()
        if entry.domain == MEDIA_PLAYER_DOMAIN and entry.platform in ECHO_PLATFORMS
    }
    included = sorted(discovered | set(selected or []))
    return EntitySelector(
        EntitySelectorConfig(
            domain=MEDIA_PLAYER_DOMAIN,
            include_entities=included,
            multiple=multiple,
            reorder=multiple,
        )
    )


class FruitForestConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure FruitForest."""

    VERSION = 1

    def __init__(self) -> None:
        self._webhook_id = webhook.async_generate_id()

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: Any) -> "FruitForestOptionsFlow":
        """Return the FruitForest options flow."""
        return FruitForestOptionsFlow()

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the single FruitForest bridge."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        if user_input is not None:
            webhook_id = user_input[CONF_WEBHOOK_ID].strip()
            if not user_input[CONF_ECHO_ENTITIES]:
                errors[CONF_ECHO_ENTITIES] = "echo_required"
            elif len(webhook_id) < 16:
                errors[CONF_WEBHOOK_ID] = "webhook_too_short"
            else:
                return self.async_create_entry(
                    title="FruitForest",
                    data={CONF_WEBHOOK_ID: webhook_id},
                    options={
                        CONF_ECHO_ENTITIES: user_input[CONF_ECHO_ENTITIES],
                        CONF_GROUPS: {},
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_ECHO_ENTITIES): _echo_selector(
                    self.hass, multiple=True
                ),
                vol.Required(CONF_WEBHOOK_ID, default=self._webhook_id): TextSelector(
                    TextSelectorConfig()
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class FruitForestOptionsFlow(OptionsFlow):
    """Edit Echo destinations and Alexa groups."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the configuration menu."""
        menu_options = ["devices", "add_group"]
        if self.config_entry.options.get(CONF_GROUPS):
            menu_options.append("remove_group")
        return self.async_show_menu(step_id="init", menu_options=menu_options)

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the enabled Echo checklist."""
        if user_input is not None:
            options = dict(self.config_entry.options)
            options[CONF_ECHO_ENTITIES] = user_input[CONF_ECHO_ENTITIES]
            return self.async_create_entry(title="", data=options)

        selected = self.config_entry.options.get(CONF_ECHO_ENTITIES, [])
        schema = vol.Schema(
            {
                vol.Required(CONF_ECHO_ENTITIES): _echo_selector(
                    self.hass, selected, multiple=True
                )
            }
        )
        return self.async_show_form(
            step_id="devices",
            data_schema=self.add_suggested_values_to_schema(
                schema,
                {
                    CONF_ECHO_ENTITIES: self.config_entry.options.get(
                        CONF_ECHO_ENTITIES, []
                    )
                },
            ),
        )

    async def async_step_add_group(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add or update an Alexa multi-room group."""
        if user_input is not None:
            group_name = user_input[CONF_GROUP_NAME].strip()
            if not group_name:
                return self.async_show_form(
                    step_id="add_group",
                    data_schema=self._group_schema(),
                    errors={CONF_GROUP_NAME: "group_name_required"},
                )

            options = dict(self.config_entry.options)
            groups = dict(options.get(CONF_GROUPS, {}))
            existing_name = next(
                (name for name in groups if name.casefold() == group_name.casefold()),
                None,
            )
            if existing_name is not None:
                groups.pop(existing_name)
            groups[group_name] = {CONF_GROUP_CARRIER: user_input[CONF_GROUP_CARRIER]}
            options[CONF_GROUPS] = groups
            return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="add_group", data_schema=self._group_schema()
        )

    async def async_step_remove_group(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Remove an Alexa multi-room group."""
        groups = dict(self.config_entry.options.get(CONF_GROUPS, {}))
        if not groups:
            return self.async_abort(reason="no_groups")

        if user_input is not None:
            groups.pop(user_input[CONF_GROUP_NAME], None)
            options = dict(self.config_entry.options)
            options[CONF_GROUPS] = groups
            return self.async_create_entry(title="", data=options)

        options = [SelectOptionDict(value=name, label=name) for name in groups]
        return self.async_show_form(
            step_id="remove_group",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_GROUP_NAME): SelectSelector(
                        SelectSelectorConfig(options=options)
                    )
                }
            ),
        )

    def _group_schema(self) -> vol.Schema:
        selected = self.config_entry.options.get(CONF_ECHO_ENTITIES, [])
        return vol.Schema(
            {
                vol.Required(CONF_GROUP_NAME): TextSelector(TextSelectorConfig()),
                vol.Required(CONF_GROUP_CARRIER): _echo_selector(
                    self.hass, selected, multiple=False
                ),
            }
        )
