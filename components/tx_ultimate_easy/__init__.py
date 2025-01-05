import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import uart
from esphome.const import (
    CONF_ID,
)

from esphome import automation

CODEOWNERS = ["@edwardtfn"]
DEPENDENCIES = ['uart']

CONF_TX_ULTIMATE_EASY = "tx_ultimate_easy"

CONF_UART = "uart"
CONF_GANG_COUNT = "gang_count"

CONF_ON_TOUCH_EVENT = "on_touch_event"
CONF_ON_PRESS = "on_press"
CONF_ON_RELEASE = "on_release"
CONF_ON_SWIPE_LEFT = "on_swipe_left"
CONF_ON_SWIPE_RIGHT = "on_swipe_right"
CONF_ON_MULTI_TOUCH_RELEASE = "on_multi_touch_release"
CONF_ON_LONG_TOUCH_RELEASE = "on_long_touch_release"

tx_ultimate_easy_ns = cg.esphome_ns.namespace('tx_ultimate_easy')
TouchPoint = tx_ultimate_easy_ns.struct("TouchPoint")

TxUltimateTouch = tx_ultimate_easy_ns.class_(
    'TxUltimateEasy', cg.Component, uart.UARTDevice)


CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(TxUltimateTouch),

    cv.Required(CONF_UART): cv.use_id(uart),
    cv.Optional(CONF_GANG_COUNT, default=1): cv.int_range(min=1, max=4),

    cv.Optional(CONF_ON_TOUCH_EVENT): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_PRESS): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_RELEASE): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_SWIPE_LEFT): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_SWIPE_RIGHT): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_MULTI_TOUCH_RELEASE): automation.validate_automation(single=True),
    cv.Optional(CONF_ON_LONG_TOUCH_RELEASE): automation.validate_automation(single=True),

}).extend(cv.COMPONENT_SCHEMA).extend(uart.UART_DEVICE_SCHEMA)


async def register_tx_ultimate_easy(var, config):
    uart_component = await cg.get_variable(config[CONF_UART])
    cg.add(var.set_uart_component(uart_component))

    if CONF_GANG_COUNT in config:
        cg.add(var.set_gang_count(config[CONF_GANG_COUNT]))

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
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await uart.register_uart_device(var, config)
    await register_tx_ultimate_easy(var, config)

    if CORE.using_esp_idf:
        add_idf_sdkconfig_option("CONFIG_BT_ALLOCATION_FROM_SPIRAM_FIRST", True)
        add_idf_sdkconfig_option("CONFIG_BT_BLE_DYNAMIC_ENV_MEMORY", True)
        add_idf_sdkconfig_option("CONFIG_ESP32_REV_MIN_3", True)
        add_idf_sdkconfig_option("CONFIG_MBEDTLS_DYNAMIC_BUFFER", True)
        add_idf_sdkconfig_option("CONFIG_MBEDTLS_DYNAMIC_FREE_CA_CERT", True)
        add_idf_sdkconfig_option("CONFIG_MBEDTLS_DYNAMIC_FREE_CONFIG_DATA", True)
        add_idf_sdkconfig_option("CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC", True)
        add_idf_sdkconfig_option("CONFIG_SPIRAM_ALLOW_BSS_SEG_EXTERNAL_MEMORY", True)
        add_idf_sdkconfig_option("CONFIG_SPIRAM_RODATA", True)
        add_idf_sdkconfig_option("CONFIG_SPIRAM_TRY_ALLOCATE_WIFI_LWIP", True)

    cg.add_define("USE_TX_ULTIMATE_EASY")
