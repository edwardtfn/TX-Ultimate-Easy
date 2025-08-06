// tx_ultimate_easy_light.h

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
        // Log tag
        static const char *TAG = "tx_ultimate_easy.light";

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

        /**
        * @brief Packs two LightAttributes into a single uint64_t for dual light storage.
        * 
        * Bit layout: [group2_light(32)][group1_light(32)]
        * Each light uses 32 bits: [brightness(8)][red(8)][green(8)][blue(8)]
        * 
        * @param group1_attrs First light attributes (stored in lower 32 bits)
        * @param group2_attrs Second light attributes (stored in upper 32 bits)
        * @return uint64_t Packed representation suitable for NVS storage
        */
        uint64_t pack_dual_light_attributes(const LightAttributes& group1_attrs, const LightAttributes& group2_attrs);

        /**
        * @brief Unpacks uint64_t back into two LightAttributes structures.
        * 
        * @param packed The packed 64-bit representation
        * @return std::pair<LightAttributes, LightAttributes> Pair of (group1, group2) attributes
        */
        std::pair<LightAttributes, LightAttributes> unpack_dual_light_attributes(uint64_t packed);
        
        /**
        * @brief Pre-packed version of dual default attributes for convenience.
        * 
        * Value: 0x64FFFFFF64FFFFFF (both lights: brightness=100, RGB=255,255,255)
        */
        extern const uint64_t DEFAULT_DUAL_LIGHT_ATTRS_PACKED;

    } // namespace tx_ultimate_easy
} // namespace esphome
