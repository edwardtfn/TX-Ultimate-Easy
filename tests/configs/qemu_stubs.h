#pragma once
#include <esp_err.h>
#include <cstddef>
#include <cstdint>

// 1. Stub wifi_component when compiling for QEMU OpenEth without WiFi
#ifndef wifi_component
struct MockWiFiComponent {
    bool is_connected() const { return true; }
};
static MockWiFiComponent s_mock_wifi_instance;
#define wifi_component (&s_mock_wifi_instance)
#endif

// 2. Mock RMT hardware driver calls for QEMU emulation
// QEMU ESP32 target does not simulate the silicon RMT pulse generation hardware,
// which causes real-world rmt_tx_wait_all_done() to hit a 1-second timeout waiting
// for an interrupt that the emulator never fires.
// Wrapping these functions at the linker level allows the test firmware to simulate
// realistic zero-latency hardware completion, matching physical ESP32 execution.
extern "C" {
esp_err_t __wrap_rmt_tx_wait_all_done(void *channel, int timeout_ms) {
    return ESP_OK;
}

esp_err_t __wrap_rmt_transmit(void *channel, void *encoder, const void *payload, size_t payload_bytes, const void *config) {
    return ESP_OK;
}
}
