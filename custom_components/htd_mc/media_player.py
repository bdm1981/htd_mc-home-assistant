"""Support for HTD MC Series"""
from .htd_mc import HtdMcClient, MAX_HTD_VOLUME
from . import DOMAIN, CONF_ZONES
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)
from homeassistant.components.media_player.const import (
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
import logging
_LOGGER = logging.getLogger(__name__)


SUPPORT_HTD_MC = (
    SUPPORT_SELECT_SOURCE
    | SUPPORT_TURN_OFF
    | SUPPORT_TURN_ON
    | SUPPORT_VOLUME_MUTE
    # | SUPPORT_VOLUME_SET (this doesn't seem to work with the Lync system)
    | SUPPORT_VOLUME_STEP
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    htd_configs = hass.data[DOMAIN]
    entities = []

    for k in range(len(htd_configs)):
        config = htd_configs[k]
        zones = config["zones"]
        client = config["client"]
        sources = config["sources"]

        for i in range(len(zones)):
            entities.append(HtdDevice(k, client, sources, i + 1, zones[i]))

    add_entities(entities)


def hide_source(source):
    if source != "hidden":
        return source


class HtdDevice(MediaPlayerEntity):
    def __init__(self, id, client, sources, zone, zone_name):
        self.zone = zone
        self.id = id
        self.zone_name = zone_name
        self.sources = sources
        self.client = client
        self.update()

    @property
    def supported_features(self):
        return SUPPORT_HTD_MC

    @property
    def unique_id(self):
        return f"media_player.htd_mc_zone_{self.id}_{self.zone}"

    @property
    def name(self):
        return self.zone_name

    def update(self):
        self.zone_info = self.client.query_zone(self.zone)

    @property
    def state(self):
        if self.zone_info["power"] == "unknown":
            return STATE_UNKNOWN

        return STATE_ON if self.zone_info["power"] == "on" else STATE_OFF

    def turn_on(self):
        self.client.set_power(self.zone, 1)

    def turn_off(self):
        self.client.set_power(self.zone, 0)

    @property
    def volume_level(self):
        return self.zone_info["vol"] / MAX_HTD_VOLUME

    def volume_up(self):
        self.client.volume_up(self.zone)
        self.client.set_power(self.zone, 1)

    def volume_down(self):
        self.client.volume_down(self.zone)
        self.client.set_power(self.zone, 1)

    @property
    def is_volume_muted(self):
        return self.zone_info["mute"] == "on"

    def mute_volume(self, mute):
        self.client.toggle_mute(self.zone)

    @property
    def source(self):
        return self.sources[self.zone_info["source"] - 1]

    @property
    def source_list(self):
        return list(filter(hide_source, self.sources))

    @property
    def media_title(self):
        return self.source

    def select_source(self, source):
        index = self.sources.index(source)
        self.client.set_source(self.zone, index + 1)

    @property
    def icon(self):
        return "mdi:speaker"
