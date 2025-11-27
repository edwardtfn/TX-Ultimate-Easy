// tx_ultimate_easy_api.cpp
#include "tx_ultimate_easy_api.h"
#include "esphome/core/application.h"

namespace esphome {
  namespace tx_ultimate_easy {

    static const char *TAG_COMPONENT_BASE = "tx_ultimate_easy.component.api";

    // Cached strings to avoid repeated lookups and string copies
    std::string cached_device_name;

    // Fire a Home Assistant event for TX Ultimate Easy
    void fire_ha_event(const std::string &domain, const std::string &type, std::map<std::string, std::string> data) {
      // Add device name and type to the event data
      data["device_name"] = cached_device_name;
      data["firmware"] = "TX_ULTIMATE_EASY_FIRMWARE_VERSION";
      data["domain"] = domain;
      data["type"] = type;

      // Log the event being fired
      ESP_LOGD(TAG_COMPONENT_BASE, "HA event: %s/%s", domain.c_str(), type.c_str());

      // Log additional data if verbose logging is enabled
      #if ESPHOME_LOG_LEVEL >= ESPHOME_LOG_LEVEL_VERBOSE
      for (const auto &[key, value] : data) {
        ESP_LOGVV(TAG_COMPONENT_BASE, "  Event data: %s=%s", key.c_str(), value.c_str());
      }
      #endif

      // Create API device and fire the event
      esphome::api::CustomAPIDevice ha_event;
      ha_event.fire_homeassistant_event("esphome.tx_ultimate_easy", data);

      ESP_LOGV(TAG_COMPONENT_BASE, "HA event 'esphome.tx_ultimate_easy' sent successfully");
    }

  }  // namespace tx_ultimate_easy
}  // namespace esphome
