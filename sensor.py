"""Support for the Torque OBD application."""
import logging
import re

import voluptuous as vol

from homeassistant.components.http import HomeAssistantView
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_EMAIL, CONF_NAME, CONF_SENSORS
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

API_PATH = "/api/torque"

DEFAULT_NAME = "vehicle"
DOMAIN = "torque2"
_DEFAULT_SENSORS = []

ENTITY_NAME_FORMAT = "{0} {1}"

SENSOR_EMAIL_FIELD = "eml"
SENSOR_NAME_KEY = r"userFullName(\w+)"
SENSOR_UNIT_KEY = r"userUnit(\w+)"
SENSOR_VALUE_KEY = r"k(\w+)"

NAME_KEY = re.compile(SENSOR_NAME_KEY)
UNIT_KEY = re.compile(SENSOR_UNIT_KEY)
VALUE_KEY = re.compile(SENSOR_VALUE_KEY)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_SENSORS,default=_DEFAULT_SENSORS): cv.ensure_list,
    }
)


def convert_pid(value):
    """Convert pid from hex string to integer."""
    return int(value, 16)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Torque platform."""
    vehicle = config.get(CONF_NAME)
    email = config.get(CONF_EMAIL)
    sensors = {}
    for sensor in config.get(CONF_SENSORS):
      _LOGGER.debug(sensor)
#      _LOGGER.debug(sensor.item)
      for key, value in sensor.items():
        _LOGGER.debug(value)
        _LOGGER.debug('Key: ' + str(key))
        _LOGGER.debug('Name: ' + str(value['Name']))
        _LOGGER.debug('Unit: ' + str(value['Unit']))
        sensors[int(key)] = TorqueSensor(
            ENTITY_NAME_FORMAT.format(vehicle, value['Name']),
            value['Unit'],
        )
        hass.async_add_job(add_entities, [sensors[int(key)]])
#      for key, value in sensor:
#        _LOGGER.debug(key)
#        _LOGGER.debug(value)
      

    hass.http.register_view(
        TorqueReceiveDataView(email, vehicle, sensors, add_entities)
    )
    return True


class TorqueReceiveDataView(HomeAssistantView):
    """Handle data from Torque requests."""

    url = API_PATH
    name = "api:torque"

    def __init__(self, email, vehicle, sensors, add_entities):
        """Initialize a Torque view."""
        self.email = email
        self.vehicle = vehicle
        self.sensors = sensors
        self.add_entities = add_entities
        _LOGGER.debug('Torque data listener started')

    @callback
    def get(self, request):
        """Handle Torque data request."""
        hass = request.app["hass"]
        data = request.query
        _LOGGER.debug('Reading data')
        _LOGGER.debug(str(data))
        _LOGGER.debug('End of data')

        if self.email is not None and self.email != data[SENSOR_EMAIL_FIELD]:
            return

        names = {}
        units = {}
        for key in data:
            is_name = NAME_KEY.match(key)
            is_unit = UNIT_KEY.match(key)
            is_value = VALUE_KEY.match(key)

            if is_name:
                pid = convert_pid(is_name.group(1))
                names[pid] = data[key]
            elif is_unit:
                pid = convert_pid(is_unit.group(1))

                temp_unit = data[key]
                if "\\xC2\\xB0" in temp_unit:
                    temp_unit = temp_unit.replace("\\xC2\\xB0", "°")

                units[pid] = temp_unit
            elif is_value:
                pid = convert_pid(is_value.group(1))
                if pid in self.sensors:
                    self.sensors[pid].async_on_update(data[key])

        bNoNewFieldsFound = True
        for pid in names:
            if pid not in self.sensors:
                self.sensors[pid] = TorqueSensor(
                    ENTITY_NAME_FORMAT.format(self.vehicle, names[pid]),
                    units.get(pid, None),
                )
                hass.async_add_job(self.add_entities, [self.sensors[pid]])
                if bNoNewFieldsFound :
                  _LOGGER.debug('Set these sensors to Torque configuration: ' + self.vehicle)
                  _LOGGER.debug('    sensors')
                  bNoNewFieldsFound = False
                _LOGGER.debug('      - ' + str(pid) + ':')
                _LOGGER.debug('        Name: ' + names[pid])
                _LOGGER.debug('        Unit: ' + units.get(pid, None))

        return "OK!"


class TorqueSensor(Entity):
    """Representation of a Torque sensor."""

    def __init__(self, name, unit):
        """Initialize the sensor."""
        self._name = name
        self._unit = unit
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the default icon of the sensor."""
        return "mdi:car"

    @callback
    def async_on_update(self, value):
        """Receive an update."""
        self._state = value
        self.async_schedule_update_ha_state()
