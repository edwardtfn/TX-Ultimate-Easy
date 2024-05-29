#pragma once

#include "esphome/core/automation.h"
#include "esphome/core/component.h"
#include "esphome/components/uart/uart.h"
#include "esphome/components/uart/uart_component.h"
#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/components/switch/switch.h"
#include "esphome/components/light/addressable_light.h"

namespace esphome {
    namespace tx_ultimate_easy {
        const static uint8_t TOUCH_STATE_RELEASE = 1;
        const static uint8_t TOUCH_STATE_PRESS = 2;
        const static uint8_t TOUCH_STATE_SWIPE = 3;
        const static uint8_t TOUCH_STATE_MULTI_TOUCH = 11;
        const static uint8_t TOUCH_STATE_SWIPE_RIGHT = 12;
        const static uint8_t TOUCH_STATE_SWIPE_LEFT = 13;

        struct TouchPoint {
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

        protected:
            void send_touch_(TouchPoint tp);
            void handle_touch(int bytes[]);

            TouchPoint get_touch_point(int bytes[]);
            bool is_valid_data(int bytes[]);
            int get_touch_position_x(int bytes[]);
            int get_touch_state(int bytes[]);

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