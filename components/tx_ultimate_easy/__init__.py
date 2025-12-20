import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation
from esphome.components import uart
from esphome.const import (
    CONF_ID,
)
from esphome.core import CORE

CODEOWNERS = ["@edwardtfn"]
DEPENDENCIES = ['uart']

CONF_TX_ULTIMATE_EASY = "tx_ultimate_easy"

CONF_UART = "uart"

CONF_DEVICE_FORMAT = "device_format"
CONF_GANG_COUNT = "gang_count"

CONF_ON_TOUCH_EVENT = "on_touch_event"
CONF_ON_PRESS = "on_press"
CONF_ON_RELEASE = "on_release"
CONF_ON_SWIPE_LEFT = "on_swipe_left"
CONF_ON_SWIPE_RIGHT = "on_swipe_right"
CONF_ON_MULTI_TOUCH_RELEASE = "on_multi_touch_release"
CONF_ON_LONG_TOUCH_RELEASE = "on_long_touch_release"

# Device format options
DEVICE_FORMAT_EU = "EU"
DEVICE_FORMAT_US = "US"

tx_ultimate_easy_ns = cg.esphome_ns.namespace('tx_ultimate_easy')
TouchPoint = tx_ultimate_easy_ns.struct("TouchPoint")

TxUltimateTouch = tx_ultimate_easy_ns.class_(
    'TxUltimateEasy', cg.Component, uart.UARTDevice)


def validate_gang_count(value):
    """
    Validate gang_count is an integer between 1 and 4.
    
    Parameters:
        value: The gang_count value to validate.
    
    Returns:
        int: The validated gang_count value.
    
    Raises:
        cv.Invalid: If value is not an integer or not in range 1-4.
    """
    value = cv.int_(value)
    if value < 1 or value > 4:
        raise cv.Invalid(
            f"gang_count must be between 1 and 4, got {value}\n"
            "Please set gang_count in your YAML substitutions to 1, 2, 3, or 4\n"
            "substitutions:\n"
            "  device_format: EU  # REQUIRED: 'EU' or 'US' (case-sensitive, uppercase only)\n"
            "  gang_count: 1      # REQUIRED: Number of relays/buttons (1, 2, 3, or 4)"
        )
    return value


def validate_device_format(value):
    """
    Validate device_format is either 'EU' or 'US'.
    
    Parameters:
        value: The device_format value to validate.
    
    Returns:
        str: The validated device_format value.
    
    Raises:
        cv.Invalid: If value is not 'EU' or 'US'.
    """
    value = cv.string_strict(value)
    if value not in [DEVICE_FORMAT_EU, DEVICE_FORMAT_US]:
        raise cv.Invalid(
            f"device_format must be either '{DEVICE_FORMAT_EU}' or '{DEVICE_FORMAT_US}', got '{value}'\n"
            "Please add to your YAML substitutions: device_format: EU  # Must be either 'EU' or 'US'\n"
            "substitutions:\n"
            "  device_format: EU  # REQUIRED: 'EU' or 'US' (case-sensitive, uppercase only)\n"
            "  gang_count: 1      # REQUIRED: Number of relays/buttons (1, 2, 3, or 4)"
        )
    return value


CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(TxUltimateTouch),

    cv.Required(CONF_UART): cv.use_id(uart),

    cv.Optional(CONF_GANG_COUNT): validate_gang_count,
    cv.Optional(CONF_DEVICE_FORMAT): validate_device_format,

    cv.Optional(CONF_ON_TOUCH_EVENT): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_PRESS): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_RELEASE): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_SWIPE_LEFT): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_SWIPE_RIGHT): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_MULTI_TOUCH_RELEASE): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_LONG_TOUCH_RELEASE): automation.validate_automation(single=True),

}).extend(cv.COMPONENT_SCHEMA).extend(uart.UART_DEVICE_SCHEMA)


async def register_tx_ultimate_easy(var, config):
    """
    Register the TxUltimateEasy component with its UART device and wire configured automations.
    
    For the given component instance, attach the configured UART component and build any automations present in the config for touch events, presses, releases, swipes, multi-touch releases, and long-touch releases. Each automation receives a payload field named "touch" of type `TouchPoint`.
    
    Parameters:
        var: The TxUltimateTouch component instance to configure.
        config (dict): Parsed configuration mapping containing `CONF_UART` and optional automation keys.
    """
    uart_component = await cg.get_variable(config[CONF_UART])
    cg.add(var.set_uart_component(uart_component))

    if CONF_ON_TOUCH_EVENT in config:
        await automation.build_automation(
            var.get_trigger_touch_event(),
            [(TouchPoint, "touch")],
            config[CONF_ON_TOUCH_EVENT],
        )

    if CONF_ON_PRESS in config:
        await automation.build_automation(
            var.get_trigger_touch(),
            [(TouchPoint, "touch")],
            config[CONF_ON_PRESS],
        )

    if CONF_ON_RELEASE in config:
        await automation.build_automation(
            var.get_trigger_release(),
            [(TouchPoint, "touch")],
            config[CONF_ON_RELEASE],
        )

    if CONF_ON_SWIPE_LEFT in config:
        await automation.build_automation(
            var.get_trigger_swipe_left(),
            [(TouchPoint, "touch")],
            config[CONF_ON_SWIPE_LEFT],
        )

    if CONF_ON_SWIPE_RIGHT in config:
        await automation.build_automation(
            var.get_trigger_swipe_right(),
            [(TouchPoint, "touch")],
            config[CONF_ON_SWIPE_RIGHT],
        )

    if CONF_ON_MULTI_TOUCH_RELEASE in config:
        await automation.build_automation(
            var.get_trigger_multi_touch_release(),
            [(TouchPoint, "touch")],
            config[CONF_ON_MULTI_TOUCH_RELEASE],
        )

    if CONF_ON_LONG_TOUCH_RELEASE in config:
        await automation.build_automation(
            var.get_trigger_long_touch_release(),
            [(TouchPoint, "touch")],
            config[CONF_ON_LONG_TOUCH_RELEASE],
        )


async def to_code(config):
    """
    Create and register a TxUltimateTouch component and its UART device from the provided configuration.
    
    This registers the component with ESPHome, registers it as a UART device, applies additional TxUltimateEasy setup, and defines the USE_TX_ULTIMATE_EASY build macro.
    
    Parameters:
        config (dict): Parsed component configuration from YAML used to create and wire the component.
    """
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await uart.register_uart_device(var, config)
    await register_tx_ultimate_easy(var, config)

    cg.add_define("USE_TX_ULTIMATE_EASY")
