// tx_ultimate_easy_light.cpp

#ifdef TX_ULTIMATE_EASY_HW_LEDS

#include "esphome/core/log.h"
#include "tx_ultimate_easy_light.h"
#include <cinttypes>
#include <string>

namespace esphome {
    namespace tx_ultimate_easy {

        // Log tag
        static const char *TAG = "tx_ultimate_easy.light";

        // Constant definitions
        const LightAttributes LIGHT_ATTRS_DEFAULT = {100, 255, 255, 255};
        const uint32_t LIGHT_ATTRS_DEFAULT_PACKED = 0x64FFFFFF;
        const uint64_t DEFAULT_DUAL_LIGHT_ATTRS_PACKED = 0x64FFFFFF64FFFFFF;

        // Function implementations
        uint32_t pack_light_attributes(const LightAttributes& attr) {
            return (uint32_t(std::min(attr.brightness, uint8_t(100))) << 24) |
                (uint32_t(attr.red) << 16) |
                (uint32_t(attr.green) << 8) |
                (uint32_t(attr.blue));
        }

        LightAttributes unpack_light_attributes(uint32_t packed) {
            return {
                .brightness = std::min(uint8_t((packed >> 24) & 0xFF), uint8_t(100)),
                .red = uint8_t((packed >> 16) & 0xFF),
                .green = uint8_t((packed >> 8) & 0xFF),
                .blue = uint8_t(packed & 0xFF)
            };
        }

        uint64_t pack_dual_light_attributes(const LightAttributes& group1_attrs, const LightAttributes& group2_attrs) {
            uint32_t group1_packed = pack_light_attributes(group1_attrs);
            uint32_t group2_packed = pack_light_attributes(group2_attrs);
            
            return (uint64_t(group2_packed) << 32) | uint64_t(group1_packed);
        }
        
        std::pair<LightAttributes, LightAttributes> unpack_dual_light_attributes(uint64_t packed) {
            uint32_t group1_packed = uint32_t(packed & 0xFFFFFFFF);          // Lower 32 bits
            uint32_t group2_packed = uint32_t((packed >> 32) & 0xFFFFFFFF);  // Upper 32 bits
            
            return std::make_pair(
                unpack_light_attributes(group1_packed),
                unpack_light_attributes(group2_packed)
            );
        }

    } // namespace tx_ultimate_easy
} // namespace esphome

#endif  // TX_ULTIMATE_EASY_HW_LEDS
