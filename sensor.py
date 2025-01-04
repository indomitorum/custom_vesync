import logging
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .common import VeSyncDevice, has_feature
from .const import DOMAIN, VS_FANS, VS_DISCOVERY, VS_TO_HA_ATTRIBUTES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the VeSync fan platform for air purifiers."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    @callback
    def discover(devices):
        """Add new devices to platform."""
        _setup_entities(devices, async_add_entities, coordinator)

    config_entry.async_on_unload(
        async_dispatcher_connect(hass, VS_DISCOVERY.format(VS_FANS), discover)
    )

    _setup_entities(
        hass.data[DOMAIN][config_entry.entry_id][VS_FANS],
        async_add_entities,
        coordinator,
    )


@callback
def _setup_entities(devices, async_add_entities, coordinator):
    """Check if device is online and add entity."""
    entities = []
    for dev in devices:
        if dev.device_type == "air_purifier":  # Check if it's an air purifier
            entities.append(VeSyncAirPurifierFanEntity(dev, coordinator))
    async_add_entities(entities, update_before_add=True)


class VeSyncAirPurifierFanEntity(VeSyncDevice, FanEntity):
    """Class representing a VeSync air purifier as a fan."""

    def __init__(self, air_purifier, coordinator) -> None:
        """Initialize the VeSync air purifier as a fan."""
        super().__init__(air_purifier, coordinator)
        self.air_purifier = air_purifier
        self._name = f"fan.{self.air_purifier.device_name}"  # Fan entity name
        self._is_on = self.air_purifier.is_on  # Device on/off status
        self._speed = self.air_purifier.fan_level  # Fan speed
        self._preset_modes = ["manual", "auto", "sleep"]  # Supported modes

    @property
    def name(self) -> str:
        """Return the name of the fan."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if the fan is on."""
        return self._is_on

    @property
    def speed(self) -> int:
        """Return the current speed of the fan."""
        return self._speed

    @property
    def supported_features(self) -> int:
        """Return the supported features of the fan."""
        return (
            FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF | FanEntityFeature.SET_SPEED
        )

    @property
    def preset_modes(self):
        """Return the supported preset modes."""
        return self._preset_modes

    def turn_on(self, **kwargs) -> None:
        """Turn on the air purifier (fan)."""
        _LOGGER.debug("Turning on the air purifier fan")
        self.air_purifier.turn_on()  # Call method to turn on the air purifier
        self._is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs) -> None:
        """Turn off the air purifier (fan)."""
        _LOGGER.debug("Turning off the air purifier fan")
        self.air_purifier.turn_off()  # Call method to turn off the air purifier
        self._is_on = False
        self.schedule_update_ha_state()

    def set_speed(self, speed: int) -> None:
        """Set the speed of the air purifier (fan)."""
        _LOGGER.debug(f"Setting fan speed to {speed}")
        self.air_purifier.set_speed(speed)  # Call method to set fan speed
        self._speed = speed
        self.schedule_update_ha_state()

    def update(self) -> None:
        """Update the fan's state (on/off, speed)."""
        # Update device status and speed from the air purifier
        self._is_on = self.air_purifier.is_on
        self._speed = self.air_purifier.fan_level
        self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the air purifier (fan)."""
        attributes = {}
        for key, value in self.air_purifier.details.items():
            if key in VS_TO_HA_ATTRIBUTES:
                attributes[VS_TO_HA_ATTRIBUTES[key]] = value
            else:
                attributes[key] = value
        return attributes
