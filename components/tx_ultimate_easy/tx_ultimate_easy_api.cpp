// tx_ultimate_easy_api.cpp
#include "tx_ultimate_easy_api.h"
#include "esphome/core/application.h"
#include <cctype>
#include <cinttypes>

#ifdef USE_ESP32
#include <esp_partition.h>
#include <nvs.h>
#endif  // USE_ESP32

// Macro stringification helpers
#define STRINGIFY_IMPL(x) #x
#define STRINGIFY(x) STRINGIFY_IMPL(x)

namespace esphome {
namespace tx_ultimate_easy {

static const char *TAG_COMPONENT_BASE = "tx_ultimate_easy.component.api";

// Cached strings to avoid repeated lookups and string copies
std::string cached_device_name;

void initialize_cached_device_name(const std::string &raw_name) {
  if (!cached_device_name.empty())
    return;  // Already initialized

  bool last_was_underscore = false;
  for (const char &c : raw_name) {
    if (std::isalnum(static_cast<unsigned char>(c))) {
      cached_device_name += static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
      last_was_underscore = false;
    } else if (!last_was_underscore) {
      cached_device_name += '_';
      last_was_underscore = true;
    }
  }
  // Remove trailing underscore if present
  if (!cached_device_name.empty() && cached_device_name.back() == '_') {
    cached_device_name.pop_back();
  }
}

// Fire a Home Assistant event for TX Ultimate Easy
void fire_ha_event(const std::string &domain, const std::string &type, std::map<std::string, std::string> data) {
  // Add guard for uninitialized device name
  if (cached_device_name.empty()) {
    ESP_LOGW(TAG_COMPONENT_BASE, "Device name not initialized; HA event may have empty device_name field");
  }

  // Add device name and type to the event data
  data["device_name"] = cached_device_name;
  data["firmware"] = STRINGIFY(TX_ULTIMATE_EASY_FIRMWARE_VERSION);
  data["domain"] = domain;
  data["type"] = type;

  // Log the event being fired
  ESP_LOGD(TAG_COMPONENT_BASE, "HA event: %s/%s", domain.c_str(), type.c_str());

// Log additional data if verbose logging is enabled
#if ESPHOME_LOG_LEVEL >= ESPHOME_LOG_LEVEL_VERBOSE
  for (const auto &[key, value] : data) {
    ESP_LOGVV(TAG_COMPONENT_BASE, "  Event data: %s=%s", key.c_str(), value.c_str());
  }
#endif  // ESPHOME_LOG_LEVEL >= ESPHOME_LOG_LEVEL_VERBOSE

  // Create API device and fire the event
  esphome::api::CustomAPIDevice ha_event;
  ha_event.fire_homeassistant_event("esphome.tx_ultimate_easy", data);

  ESP_LOGV(TAG_COMPONENT_BASE, "HA event 'esphome.tx_ultimate_easy' sent successfully");
}

void log_nvs_stats(const char *tag) {
#ifdef USE_ESP32
  const esp_partition_t *partition =
      esp_partition_find_first(ESP_PARTITION_TYPE_DATA, ESP_PARTITION_SUBTYPE_DATA_NVS, nullptr);
  if (partition == nullptr) {
    ESP_LOGW(tag, "NVS partition: not found");
    return;
  }  // partition == nullptr

  nvs_stats_t stats{};
  const esp_err_t err = nvs_get_stats(nullptr, &stats);
  if (err != ESP_OK) {
    ESP_LOGW(tag, "NVS partition: %" PRIu32 " bytes, stats unavailable (%s)", static_cast<uint32_t>(partition->size),
             esp_err_to_name(err));
    return;
  }  // err != ESP_OK

  ESP_LOGCONFIG(tag,
                "NVS partition:\n"
                "  Size:         %" PRIu32 " bytes\n"
                "  Entries used: %zu\n"
                "  Entries free: %zu\n"
                "  Entries:      %zu\n"
                "  Namespaces:   %zu",
                static_cast<uint32_t>(partition->size), stats.used_entries, stats.free_entries, stats.total_entries,
                stats.namespace_count);
  if (stats.free_entries * 10 < stats.total_entries) {
    ESP_LOGW(tag, "NVS partition almost full: settings may fail to save");
  }  // less than 10% free
#else   // USE_ESP32
  ESP_LOGCONFIG(tag, "NVS partition: not available on this platform");
#endif  // USE_ESP32
}

}  // namespace tx_ultimate_easy
}  // namespace esphome
