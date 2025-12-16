// tx_ultimate_easy_touch.h

#pragma once

#ifdef TX_ULTIMATE_EASY_HW_TOUCH

#include "esphome/core/automation.h"
#include "esphome/core/component.h"
#include "esphome/components/uart/uart.h"
#include "esphome/components/uart/uart_component.h"
#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/components/switch/switch.h"
#include "esphome/components/light/addressable_light.h"
#include <array>

/**
 * Return the trigger that fires for any touch-related event with a TouchPoint payload.
 * @returns Pointer to the trigger invoked for all touch events.
 */
/**
 * Return the trigger that fires when a touch press is detected.
 * @returns Pointer to the trigger invoked on touch press.
 */
/**
 * Return the trigger that fires when a touch release is detected.
 * @returns Pointer to the trigger invoked on touch release.
 */
/**
 * Return the trigger that fires when a swipe-left gesture is detected.
 * @returns Pointer to the trigger invoked on swipe-left.
 */
/**
 * Return the trigger that fires when a swipe-right gesture is detected.
 * @returns Pointer to the trigger invoked on swipe-right.
 */
/**
 * Return the trigger that fires when a multi-touch release is detected.
 * @returns Pointer to the trigger invoked on multi-touch release.
 */
/**
 * Return the trigger that fires when a long-touch release is detected.
 * @returns Pointer to the trigger invoked on long-touch release.
 */
/**
 * Bind a parent UARTComponent instance to this device.
 * @param uart_component Pointer to the UARTComponent to use as the UART parent.
 */
/**
 * Perform component setup tasks executed once at startup.
 */
/**
 * Perform periodic processing; called frequently by the main loop.
 */
/**
 * Dump component configuration and state to the logger.
 */
/**
 * Map a touch position index to a button index on the device.
 * Positions outside the valid range are clamped to the nearest valid button.
 * @param position Touch position index (1-based from device).
 * @returns Button index corresponding to the provided position.
 */
/**
 * Send a TouchPoint event into the component's internal handling flow (and triggers).
 * @param tp TouchPoint to send.
 */
/**
 * Process a raw UART packet of size UART_RECEIVED_BYTES_SIZE and dispatch corresponding touch events.
 * Invalid or non-touch packets are ignored.
 * @param bytes Array containing the raw received bytes.
 */
/**
 * Parse a raw UART packet and construct the corresponding TouchPoint.
 * @param bytes Array containing the raw received bytes.
 * @returns Constructed TouchPoint representing the parsed packet.
 */
/**
 * Validate that a received UART packet contains a well-formed touch data message.
 * Validation checks include header bytes and expected marker bytes.
 * @param bytes Array containing the raw received bytes.
 * @returns `true` if the packet is a valid touch data message, `false` otherwise.
 */
/**
 * Extract the horizontal touch position (x) from a raw UART packet.
 * @param bytes Array containing the raw received bytes.
 * @returns X position in device-specific coordinates, or -1 if not present/valid.
 */
/**
 * Extract the touch state code from a raw UART packet.
 * @param bytes Array containing the raw received bytes.
 * @returns Numeric touch state code corresponding to the TOUCH_STATE_* constants, or -1 if not present/valid.
 */
namespace esphome {
    namespace tx_ultimate_easy {
        // Touch Max Position
        constexpr uint8_t TOUCH_MAX_POSITION = 10;

        // Touch State Constants
        constexpr uint8_t TOUCH_STATE_RELEASE = 0x01;
        constexpr uint8_t TOUCH_STATE_PRESS = 0x02;
        constexpr uint8_t TOUCH_STATE_SWIPE = 0x03;
        constexpr uint8_t TOUCH_STATE_MULTI_TOUCH = 0x0B;
        constexpr uint8_t TOUCH_STATE_SWIPE_RIGHT = 0x0C;
        constexpr uint8_t TOUCH_STATE_SWIPE_LEFT = 0x0D;

        // UART Constants
        constexpr int UART_RECEIVED_BYTES_SIZE = 15;
        constexpr int HEADER_BYTE_1 = 0xAA;
        constexpr int HEADER_BYTE_2 = 0x55;
        constexpr int VALID_DATA_BYTE_2 = 0x01;
        constexpr int VALID_DATA_BYTE_3 = 0x02;

        struct TouchPoint {
            uint8_t button = 0;
            int8_t x = -1;
            int8_t state = -1;
            std::string state_str = "Unknown";
        };

        class TxUltimateEasy : public uart::UARTDevice, public Component {
        public:
            Trigger<TouchPoint> *get_trigger_touch_event() { return &this->trigger_touch_event_; }
            Trigger<TouchPoint> *get_trigger_touch() { return &this->trigger_touch_; }
            Trigger<TouchPoint> *get_trigger_release() { return &this->trigger_release_; }
            Trigger<TouchPoint> *get_trigger_swipe_left() { return &this->trigger_swipe_left_; }
            Trigger<TouchPoint> *get_trigger_swipe_right() { return &this->trigger_swipe_right_; }
            Trigger<TouchPoint> *get_trigger_multi_touch_release() { return &this->trigger_multi_touch_release_; }
            Trigger<TouchPoint> *get_trigger_long_touch_release() { return &this->trigger_long_touch_release_; }

            void set_uart_component(esphome::uart::UARTComponent *uart_component) { this->set_uart_parent(uart_component); }

            void setup() override;
            void loop() override;
            void dump_config() override;

            uint8_t get_button_from_position(const uint8_t position);

        protected:
            void send_touch_(TouchPoint tp);
            void handle_touch(const std::array<int, UART_RECEIVED_BYTES_SIZE> &bytes);

            TouchPoint get_touch_point(const std::array<int, UART_RECEIVED_BYTES_SIZE> &bytes);
            bool is_valid_data(const std::array<int, UART_RECEIVED_BYTES_SIZE> &bytes);
            int get_touch_position_x(const std::array<int, UART_RECEIVED_BYTES_SIZE> &bytes);
            int get_touch_state(const std::array<int, UART_RECEIVED_BYTES_SIZE> &bytes);

            Trigger<TouchPoint> trigger_touch_event_;
            Trigger<TouchPoint> trigger_touch_;
            Trigger<TouchPoint> trigger_release_;
            Trigger<TouchPoint> trigger_swipe_left_;
            Trigger<TouchPoint> trigger_swipe_right_;
            Trigger<TouchPoint> trigger_multi_touch_release_;
            Trigger<TouchPoint> trigger_long_touch_release_;

        }; // class TxUltimateEasy

    } // namespace tx_ultimate_easy
} // namespace esphome

#endif  // TX_ULTIMATE_EASY_HW_TOUCH