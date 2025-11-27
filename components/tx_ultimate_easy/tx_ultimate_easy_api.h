// tx_ultimate_easy_api.h - Generic flag system for TX Ultimate Easy
#pragma once

#include "esphome/components/api/custom_api_device.h"  // For API HA event call
#include "esphome/core/application.h"  // For App
#include "esphome/core/hal.h"          // For delay()
#include "esphome/core/log.h"
#include <cstdint>

#ifndef TX_ULTIMATE_EASY_FIRMWARE_VERSION
#define TX_ULTIMATE_EASY_FIRMWARE_VERSION "unknown"
#endif

namespace esphome {
    namespace tx_ultimate_easy {

    // Cached device name to avoid repeated lookups and string copies
    extern std::string cached_device_name;

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

    // Cached device name to avoid repeated lookups and string copies
    extern std::string cached_device_name;

    /**
    * @brief Fire a Home Assistant event for TX Ultimate Easy
    *
    * Automatically adds device_name and type to the event data.
    *
    * @param domain Event domain (e.g., "touch", "audio", "relay")
    * @param type Event type (e.g., "button_click", "page_changed", "boot")
    * @param data Additional event data (device_name and type added automatically)
    *
    * @note The event name is automatically set to "esphome.tx_ultimate_easy"
    * @note Call init_device_name_cache() during boot before using this function
    *
    * @code
    * fire_ha_event("button_click", {
    *   {"page", "home"},
    *   {"component", "bt_left"}
    * });
    * @endcode
    */
    void fire_ha_event(const std::string &domain, const std::string &type,
                        std::map<std::string, std::string> data = {});

  }  // namespace tx_ultimate_easy
}  // namespace esphome
