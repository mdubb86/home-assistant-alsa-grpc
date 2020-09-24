"""Home Assistant media player integration for alsa-grpc"""
import logging

import voluptuous as vol

from alsa_grpc_client import AlsaClient

from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player.const import SUPPORT_VOLUME_SET
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, STATE_IDLE
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_SERVERS = "servers"

DOMAIN = "alsa_grpc"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_SERVERS): [{
            vol.Required('ip'): cv.string,
            vol.Optional('port'): cv.port,
            vol.Required("alias"): cv.string
        }]
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Alsa GRPC platform."""

    clients = []
    servers = config.get(CONF_SERVERS)

    def _shutdown(call):
        """Disconnect the client(s) on shutdown."""
        _LOGGER.info("Disconnecting alsa-grpc clinet connections")
        for client in clients:
            client.disconnect()

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, _shutdown)

    for server in servers:
        ip = server['ip']
        port = server['port']
        alias = server['alias']

        def _on_connect(ctrl, alias=alias):
            _LOGGER.info("Configuring alsa-grpc entity %s %s", alias, ctrl.name)
            add_entities([AlsamixerClientEntity(alias, ctrl)])

        client = AlsaClient(ip, port, _on_connect)
        clients.append(client)
        _LOGGER.info("Connecting to alsa-grpc server %s:%d (%s)", ip, port, alias)
        client.connect()


class AlsamixerClientEntity(MediaPlayerEntity):
    """Representation of an alsa-grpc control."""

    def __init__(self, alias, ctrl):
        """Initialize the alsa-grpc control entity."""
        self._ctrl = ctrl
        self._name = alias + " " + ctrl.name
        self._volume = ctrl.volume[0] / 100
        self._state = STATE_IDLE

        def _callback():
            self._volume = ctrl.volume[0] / 100
            self.schedule_update_ha_state()

        ctrl.subscribe(_callback)

    def set_volume_level(self, volume):
        """Set the volume level."""
        self._ctrl.set_volume(volume)

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        """Return the name of the control."""
        return self._name

    @property
    def volume_level(self):
        """Return the volume level."""
        return self._volume

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_VOLUME_SET

    @property
    def state(self):
        """Return the state of the player."""
        return self._state
