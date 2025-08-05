// tx_ultimate_easy.h

#pragma once

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

        // Log tag
        static const char *TAG = "tx_ultimate_easy";

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

            uint8_t get_gang_count() { return this->gang_count_; }
            bool set_gang_count(const uint8_t gang_count);
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

            uint8_t gang_count_ = 1;

        }; // class TxUltimateEasy

        /**
        * @brief Light attributes structure for storing color and brightness data.
        * 
        * This structure represents the visual attributes of a light without the state (on/off).
        * It's designed to be packed efficiently into a 32-bit integer for NVS storage.
        * RGB components use the full 8-bit range (0-255) while brightness uses percentage (0-100).
        */
        struct LightAttributes {
            uint8_t brightness;  ///< Light brightness percentage (0-100, where 100 = full brightness)
            uint8_t red;         ///< Red color component (0-255)
            uint8_t green;       ///< Green color component (0-255)  
            uint8_t blue;        ///< Blue color component (0-255)
        };

        /**
        * @brief Packs LightAttributes structure into a 32-bit integer for storage.
        * 
        * Bit layout: [brightness(8)][red(8)][green(8)][blue(8)]
        * This allows efficient storage in ESPHome globals with restore_value support.
        * Note: Brightness values > 100 will be clamped to 100 during packing.
        * 
        * @param attr The LightAttributes structure to pack
        * @return uint32_t Packed representation suitable for NVS storage
        * 
        * @example
        * LightAttributes attrs = {75, 255, 128, 64};
        * uint32_t packed = pack_light_attributes(attrs);  // Returns 0x4BFF8040
        */
        uint32_t pack_light_attributes(const LightAttributes& attr);

        /**
        * @brief Unpacks a 32-bit integer back into LightAttributes structure.
        * 
        * Reverses the packing operation to extract individual color and brightness values.
        * Brightness values > 100 in the packed data will be clamped to 100.
        * 
        * @param packed The packed 32-bit representation
        * @return LightAttributes The unpacked structure with individual components
        * 
        * @example
        * uint32_t packed = 0x4BFF8040;
        * LightAttributes attrs = unpack_light_attributes(packed);
        * // attrs.brightness = 75, attrs.red = 255, attrs.green = 128, attrs.blue = 64
        */
        LightAttributes unpack_light_attributes(uint32_t packed);

        /**
        * @brief Default light attributes for initialization.
        * 
        * Provides sensible defaults for new lights:
        * - Brightness: 100 (full brightness)
        * - Red: 255 (full intensity)
        * - Green: 255 (full intensity) 
        * - Blue: 255 (full intensity)
        * Result: Pure white color at full brightness
        */
        extern const LightAttributes LIGHT_ATTRS_DEFAULT;

        /**
        * @brief Pre-packed version of DEFAULT_LIGHT_ATTRS for convenience.
        * 
        * This constant contains LIGHT_ATTRS_DEFAULT already packed into uint32_t format,
        * suitable for direct use in ESPHome YAML initial_value fields.
        * 
        * Value: 0x64FFFFFF (brightness=100, RGB=255,255,255)
        */
        extern const uint32_t LIGHT_ATTRS_DEFAULT_PACKED;

    } // namespace tx_ultimate_easy
} // namespace esphome
