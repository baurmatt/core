"""Test MQTT fans."""
import json

from homeassistant.components import fan
from homeassistant.const import (
    ATTR_ASSUMED_STATE,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.setup import async_setup_component

from .common import (
    help_test_discovery_broken,
    help_test_discovery_removal,
    help_test_discovery_update,
    help_test_discovery_update_attr,
    help_test_entity_device_info_update,
    help_test_entity_device_info_with_identifier,
    help_test_entity_id_update,
    help_test_setting_attribute_via_mqtt_json_message,
    help_test_unique_id,
    help_test_update_with_json_attrs_bad_JSON,
    help_test_update_with_json_attrs_not_dict,
)

from tests.common import async_fire_mqtt_message
from tests.components.fan import common


async def test_fail_setup_if_no_command_topic(hass, mqtt_mock):
    """Test if command fails with command topic."""
    assert await async_setup_component(
        hass, fan.DOMAIN, {fan.DOMAIN: {"platform": "mqtt", "name": "test"}}
    )
    assert hass.states.get("fan.test") is None


async def test_controlling_state_via_topic(hass, mqtt_mock):
    """Test the controlling state via topic."""
    assert await async_setup_component(
        hass,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "payload_off": "StAtE_OfF",
                "payload_on": "StAtE_On",
                "oscillation_state_topic": "oscillation-state-topic",
                "oscillation_command_topic": "oscillation-command-topic",
                "payload_oscillation_off": "OsC_OfF",
                "payload_oscillation_on": "OsC_On",
                "speed_state_topic": "speed-state-topic",
                "speed_command_topic": "speed-command-topic",
                "payload_off_speed": "speed_OfF",
                "payload_low_speed": "speed_lOw",
                "payload_medium_speed": "speed_mEdium",
                "payload_high_speed": "speed_High",
            }
        },
    )

    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "state-topic", "StAtE_On")
    state = hass.states.get("fan.test")
    assert state.state is STATE_ON

    async_fire_mqtt_message(hass, "state-topic", "StAtE_OfF")
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get("oscillating") is False

    async_fire_mqtt_message(hass, "oscillation-state-topic", "OsC_On")
    state = hass.states.get("fan.test")
    assert state.attributes.get("oscillating") is True

    async_fire_mqtt_message(hass, "oscillation-state-topic", "OsC_OfF")
    state = hass.states.get("fan.test")
    assert state.attributes.get("oscillating") is False

    assert state.attributes.get("speed") == fan.SPEED_OFF

    async_fire_mqtt_message(hass, "speed-state-topic", "speed_lOw")
    state = hass.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_LOW

    async_fire_mqtt_message(hass, "speed-state-topic", "speed_mEdium")
    state = hass.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_MEDIUM

    async_fire_mqtt_message(hass, "speed-state-topic", "speed_High")
    state = hass.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_HIGH

    async_fire_mqtt_message(hass, "speed-state-topic", "speed_OfF")
    state = hass.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_OFF


async def test_controlling_state_via_topic_and_json_message(hass, mqtt_mock):
    """Test the controlling state via topic and JSON message."""
    assert await async_setup_component(
        hass,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "oscillation_state_topic": "oscillation-state-topic",
                "oscillation_command_topic": "oscillation-command-topic",
                "speed_state_topic": "speed-state-topic",
                "speed_command_topic": "speed-command-topic",
                "state_value_template": "{{ value_json.val }}",
                "oscillation_value_template": "{{ value_json.val }}",
                "speed_value_template": "{{ value_json.val }}",
            }
        },
    )

    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "state-topic", '{"val":"ON"}')
    state = hass.states.get("fan.test")
    assert state.state is STATE_ON

    async_fire_mqtt_message(hass, "state-topic", '{"val":"OFF"}')
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get("oscillating") is False

    async_fire_mqtt_message(hass, "oscillation-state-topic", '{"val":"oscillate_on"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("oscillating") is True

    async_fire_mqtt_message(hass, "oscillation-state-topic", '{"val":"oscillate_off"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("oscillating") is False

    assert state.attributes.get("speed") == fan.SPEED_OFF

    async_fire_mqtt_message(hass, "speed-state-topic", '{"val":"low"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_LOW

    async_fire_mqtt_message(hass, "speed-state-topic", '{"val":"medium"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_MEDIUM

    async_fire_mqtt_message(hass, "speed-state-topic", '{"val":"high"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_HIGH

    async_fire_mqtt_message(hass, "speed-state-topic", '{"val":"off"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_OFF


async def test_sending_mqtt_commands_and_optimistic(hass, mqtt_mock):
    """Test optimistic mode without state topic."""
    assert await async_setup_component(
        hass,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "command_topic": "command-topic",
                "payload_off": "StAtE_OfF",
                "payload_on": "StAtE_On",
                "oscillation_command_topic": "oscillation-command-topic",
                "oscillation_state_topic": "oscillation-state-topic",
                "payload_oscillation_off": "OsC_OfF",
                "payload_oscillation_on": "OsC_On",
                "speed_command_topic": "speed-command-topic",
                "speed_state_topic": "speed-state-topic",
                "payload_off_speed": "speed_OfF",
                "payload_low_speed": "speed_lOw",
                "payload_medium_speed": "speed_mEdium",
                "payload_high_speed": "speed_High",
            }
        },
    )

    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(hass, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "command-topic", "StAtE_On", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_off(hass, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "command-topic", "StAtE_OfF", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_oscillate(hass, "fan.test", True)
    mqtt_mock.async_publish.assert_called_once_with(
        "oscillation-command-topic", "OsC_On", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_oscillate(hass, "fan.test", False)
    mqtt_mock.async_publish.assert_called_once_with(
        "oscillation-command-topic", "OsC_OfF", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(hass, "fan.test", fan.SPEED_LOW)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "speed_lOw", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(hass, "fan.test", fan.SPEED_MEDIUM)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "speed_mEdium", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(hass, "fan.test", fan.SPEED_HIGH)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "speed_High", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(hass, "fan.test", fan.SPEED_OFF)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "speed_OfF", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)


async def test_sending_mqtt_commands_and_explicit_optimistic(hass, mqtt_mock):
    """Test optimistic mode with state topic."""
    assert await async_setup_component(
        hass,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "oscillation_state_topic": "oscillation-state-topic",
                "oscillation_command_topic": "oscillation-command-topic",
                "speed_state_topic": "speed-state-topic",
                "speed_command_topic": "speed-command-topic",
                "optimistic": True,
            }
        },
    )

    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(hass, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with("command-topic", "ON", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_off(hass, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with("command-topic", "OFF", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_oscillate(hass, "fan.test", True)
    mqtt_mock.async_publish.assert_called_once_with(
        "oscillation-command-topic", "oscillate_on", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_oscillate(hass, "fan.test", False)
    mqtt_mock.async_publish.assert_called_once_with(
        "oscillation-command-topic", "oscillate_off", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(hass, "fan.test", fan.SPEED_LOW)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "low", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(hass, "fan.test", fan.SPEED_MEDIUM)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "medium", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(hass, "fan.test", fan.SPEED_HIGH)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "high", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(hass, "fan.test", fan.SPEED_OFF)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "off", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)


async def test_default_availability_payload(hass, mqtt_mock):
    """Test the availability payload."""
    assert await async_setup_component(
        hass,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "availability_topic": "availability_topic",
            }
        },
    )

    state = hass.states.get("fan.test")
    assert state.state is STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "availability_topic", "online")

    state = hass.states.get("fan.test")
    assert state.state is not STATE_UNAVAILABLE
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "availability_topic", "offline")

    state = hass.states.get("fan.test")
    assert state.state is STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "state-topic", "1")

    state = hass.states.get("fan.test")
    assert state.state is STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "availability_topic", "online")

    state = hass.states.get("fan.test")
    assert state.state is not STATE_UNAVAILABLE


async def test_custom_availability_payload(hass, mqtt_mock):
    """Test the availability payload."""
    assert await async_setup_component(
        hass,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "availability_topic": "availability_topic",
                "payload_available": "good",
                "payload_not_available": "nogood",
            }
        },
    )

    state = hass.states.get("fan.test")
    assert state.state is STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "availability_topic", "good")

    state = hass.states.get("fan.test")
    assert state.state is not STATE_UNAVAILABLE
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "availability_topic", "nogood")

    state = hass.states.get("fan.test")
    assert state.state is STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "state-topic", "1")

    state = hass.states.get("fan.test")
    assert state.state is STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "availability_topic", "good")

    state = hass.states.get("fan.test")
    assert state.state is not STATE_UNAVAILABLE


async def test_setting_attribute_via_mqtt_json_message(hass, mqtt_mock):
    """Test the setting of attribute via MQTT with JSON payload."""
    config = {
        fan.DOMAIN: {
            "platform": "mqtt",
            "name": "test",
            "command_topic": "test-topic",
            "json_attributes_topic": "attr-topic",
        }
    }
    await help_test_setting_attribute_via_mqtt_json_message(
        hass, mqtt_mock, fan.DOMAIN, config
    )


async def test_update_with_json_attrs_not_dict(hass, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    config = {
        fan.DOMAIN: {
            "platform": "mqtt",
            "name": "test",
            "command_topic": "test-topic",
            "json_attributes_topic": "attr-topic",
        }
    }
    await help_test_update_with_json_attrs_not_dict(
        hass, mqtt_mock, caplog, fan.DOMAIN, config
    )


async def test_update_with_json_attrs_bad_JSON(hass, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    config = {
        fan.DOMAIN: {
            "platform": "mqtt",
            "name": "test",
            "command_topic": "test-topic",
            "json_attributes_topic": "attr-topic",
        }
    }
    await help_test_update_with_json_attrs_bad_JSON(
        hass, mqtt_mock, caplog, fan.DOMAIN, config
    )


async def test_discovery_update_attr(hass, mqtt_mock, caplog):
    """Test update of discovered MQTTAttributes."""
    data1 = (
        '{ "name": "Beer",'
        '  "command_topic": "test_topic",'
        '  "json_attributes_topic": "attr-topic1" }'
    )
    data2 = (
        '{ "name": "Beer",'
        '  "command_topic": "test_topic",'
        '  "json_attributes_topic": "attr-topic2" }'
    )
    await help_test_discovery_update_attr(
        hass, mqtt_mock, caplog, fan.DOMAIN, data1, data2
    )


async def test_unique_id(hass):
    """Test unique_id option only creates one fan per id."""
    config = {
        fan.DOMAIN: [
            {
                "platform": "mqtt",
                "name": "Test 1",
                "state_topic": "test-topic",
                "command_topic": "test_topic",
                "unique_id": "TOTALLY_UNIQUE",
            },
            {
                "platform": "mqtt",
                "name": "Test 2",
                "state_topic": "test-topic",
                "command_topic": "test_topic",
                "unique_id": "TOTALLY_UNIQUE",
            },
        ]
    }
    await help_test_unique_id(hass, fan.DOMAIN, config)


async def test_discovery_removal_fan(hass, mqtt_mock, caplog):
    """Test removal of discovered fan."""
    data = '{ "name": "Beer",' '  "command_topic": "test_topic" }'
    await help_test_discovery_removal(hass, mqtt_mock, caplog, fan.DOMAIN, data)


async def test_discovery_update_fan(hass, mqtt_mock, caplog):
    """Test update of discovered fan."""
    data1 = '{ "name": "Beer",' '  "command_topic": "test_topic" }'
    data2 = '{ "name": "Milk",' '  "command_topic": "test_topic" }'
    await help_test_discovery_update(hass, mqtt_mock, caplog, fan.DOMAIN, data1, data2)


async def test_discovery_broken(hass, mqtt_mock, caplog):
    """Test handling of bad discovery message."""
    data1 = '{ "name": "Beer" }'
    data2 = '{ "name": "Milk",' '  "command_topic": "test_topic" }'
    await help_test_discovery_broken(hass, mqtt_mock, caplog, fan.DOMAIN, data1, data2)


async def test_entity_device_info_with_identifier(hass, mqtt_mock):
    """Test MQTT fan device registry integration."""
    data = json.dumps(
        {
            "platform": "mqtt",
            "name": "Test 1",
            "state_topic": "test-topic",
            "command_topic": "test-command-topic",
            "device": {
                "identifiers": ["helloworld"],
                "connections": [["mac", "02:5b:26:a8:dc:12"]],
                "manufacturer": "Whatever",
                "name": "Beer",
                "model": "Glass",
                "sw_version": "0.1-beta",
            },
            "unique_id": "veryunique",
        }
    )
    await help_test_entity_device_info_with_identifier(
        hass, mqtt_mock, fan.DOMAIN, data
    )


async def test_entity_device_info_update(hass, mqtt_mock):
    """Test device registry update."""
    config = {
        "platform": "mqtt",
        "name": "Test 1",
        "state_topic": "test-topic",
        "command_topic": "test-command-topic",
        "device": {
            "identifiers": ["helloworld"],
            "connections": [["mac", "02:5b:26:a8:dc:12"]],
            "manufacturer": "Whatever",
            "name": "Beer",
            "model": "Glass",
            "sw_version": "0.1-beta",
        },
        "unique_id": "veryunique",
    }
    await help_test_entity_device_info_update(hass, mqtt_mock, fan.DOMAIN, config)


async def test_entity_id_update(hass, mqtt_mock):
    """Test MQTT subscriptions are managed when entity_id is updated."""
    config = {
        fan.DOMAIN: [
            {
                "platform": "mqtt",
                "name": "beer",
                "state_topic": "test-topic",
                "command_topic": "command-topic",
                "availability_topic": "avty-topic",
                "unique_id": "TOTALLY_UNIQUE",
            }
        ]
    }
    await help_test_entity_id_update(hass, mqtt_mock, fan.DOMAIN, config)
