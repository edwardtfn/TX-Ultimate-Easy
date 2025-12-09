// tx_ultimate_easy_api.h - Generic flag system for TX Ultimate Easy
#pragma once

#include "esphome/components/api/custom_api_device.h"  // For API HA event call
#include "esphome/core/application.h"  // For App
#include "esphome/core/hal.h"          // For delay()
#include "esphome/core/log.h"
#include <cstdint>
#include <map>
#include <string>

#ifndef TX_ULTIMATE_EASY_FIRMWARE_VERSION
#define TX_ULTIMATE_EASY_FIRMWARE_VERSION "unknown"
#endif

namespace esphome {
    namespace tx_ultimate_easy {

    // Cached device name to avoid repeated lookups and string copies
    extern std::string cached_device_name;

    /**
    * @brief Initialize the cached device name from a raw name string.
    * 
    * Sanitizes the raw device name by converting it to lowercase alphanumeric
    * characters with underscores replacing non-alphanumeric characters. Consecutive
    * underscores are avoided. This function should be called early in the boot
    * process (e.g., on WiFi connect) to populate the cached_device_name.
    * 
    * If cached_device_name is already populated (non-empty), this function does
    * nothing to avoid overwriting an existing value.
    * 
    * @param raw_name The raw device name (typically from App.get_name()) to sanitize
    * 
    * Example:
    *   Raw name: "TX-Ultimate Easy!"
    *   Result:   "tx_ultimate_easy"
    */
    void initialize_cached_device_name(const std::string &raw_name);

    /// @brief Feed the watchdog timer with an optional delay
    ///
    /// This utility function combines a delay with a watchdog timer feed operation.
    /// It's commonly used in long-running operations to prevent watchdog timeouts
    /// while giving the system time to process other tasks.
    ///
    /// @param ms Delay duration in milliseconds before feeding the watchdog (default: 5ms)
    ///
    /// @note This function is blocking - execution will pause for the specified duration
    /// @note Minimum recommended delay is 5ms to allow system task processing
    ///
    /// @code
    /// // Example usage with default 5ms delay
    /// feed_wdt_delay();
    ///
    /// // Example usage with custom 25ms delay
    /// feed_wdt_delay(25);
    ///
    /// // Common pattern in loops
    /// for (uint8_t i = 0; i < 10; ++i) {
    ///   // ... do work ...
    ///   feed_wdt_delay(5);  // Prevent watchdog timeout
    /// }
    /// @endcode
    ///
    /// @see delay()
    /// @see App.feed_wdt()
    inline void feed_wdt_delay(uint32_t ms = 5) {
      esphome::delay(ms);       // Block execution for specified milliseconds
      esphome::App.feed_wdt();  // Reset the watchdog timer
    }

    /**
    * @brief Fire a Home Assistant event for TX Ultimate Easy
    *
    * Automatically adds device_name, firmware, domain and type to the event data.
    *
    * @param domain Event domain (e.g., "touch", "audio", "relay").
    * @param type   Event type   (e.g., "multi_touch", "swipe", "boot").
    * @param data   Additional event data; core fields are injected automatically.
    *
    * @note The event name is fixed to "esphome.tx_ultimate_easy".
    *
    * @code
    * fire_ha_event("touch", "swipe", {
    *   {"swipe-direction", "left"},
    *   {"position", "3"}
    * });
    * @endcode
    */
    void fire_ha_event(const std::string &domain, const std::string &type,
                        std::map<std::string, std::string> data = {});

  }  // namespace tx_ultimate_easy
}  // namespace esphome
