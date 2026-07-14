"""Constants for FruitForest."""

from typing import Final

DOMAIN: Final = "fruitforest"

CONF_ECHO_ENTITIES: Final = "echo_entities"
CONF_GROUPS: Final = "groups"
CONF_GROUP_CARRIER: Final = "carrier"
CONF_GROUP_NAME: Final = "group_name"
CONF_WEBHOOK_ID: Final = "webhook_id"

SERVICE_GET_TARGETS: Final = "get_targets"
SERVICE_PLAY: Final = "play"

KIND_ALBUM: Final = "album"
KIND_FREEFORM: Final = "freeform"
KIND_PLAYLIST: Final = "playlist"
KIND_TRACK: Final = "track"
PLAYBACK_KINDS: Final = (KIND_TRACK, KIND_ALBUM, KIND_PLAYLIST, KIND_FREEFORM)

WEBHOOK_NAME: Final = "FruitForest Shortcuts"
