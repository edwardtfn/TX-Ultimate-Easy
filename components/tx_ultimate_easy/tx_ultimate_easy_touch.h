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
