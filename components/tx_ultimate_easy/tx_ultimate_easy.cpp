// tx_ultimate_easy.cpp

#include "esphome/core/log.h"
#include "tx_ultimate_easy.h"
#include <string>

namespace esphome {
    namespace tx_ultimate_easy {

        void TxUltimateEasy::setup() {
            ESP_LOGI(TAG, "TX Ultimate Easy is initialized");
        }

        void TxUltimateEasy::loop() {
            bool found = false;
            std::array<int, UART_RECEIVED_BYTES_SIZE> uart_received_bytes{};
            int byte = -1;
            int i = 0;

            while (this->available()) {
                byte = this->read();
                if (byte == HEADER_BYTE_1) {
                    this->handle_touch(uart_received_bytes);
                    i = 0;
                }
                if (i < UART_RECEIVED_BYTES_SIZE) {
                    uart_received_bytes[i] = byte;
                    i++;
                }
                if (byte != 0x00) {
                    found = true;
                }
            }
            if (found) this->handle_touch(uart_received_bytes);
        }

        void TxUltimateEasy::handle_touch(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes) {
            ESP_LOGV(TAG, "------------");
            ESP_LOGV(TAG, "- UART-Log -");
            ESP_LOGV(TAG, "------------");
            for (int i = 0; i < UART_RECEIVED_BYTES_SIZE; i++) {
                ESP_LOGV(TAG, "UART - Log - Byte[%i]: %i", i, uart_received_bytes[i]);
            }
            if (this->is_valid_data(uart_received_bytes)) {
                this->send_touch_(this->get_touch_point(uart_received_bytes));
            }
        }

        void TxUltimateEasy::dump_config() {
            ESP_LOGCONFIG(TAG, "TX Ultimate Easy");
            ESP_LOGCONFIG(TAG, "  Gang count: %" PRIu8, this->gang_count_);
        }

        bool TxUltimateEasy::set_gang_count(const uint8_t gang_count) {
            // Hardware supports maximum of 4 touch-sensitive buttons
            if (gang_count < 1 or gang_count > 4)
                return false;
            this->gang_count_ = gang_count;
            return true;
        }

        uint8_t TxUltimateEasy::get_button_from_position(const uint8_t position) {
            // Validate position bounds
            if (position > TOUCH_MAX_POSITION)
                return 0;

            // Special case for single gang (only one button exists)
            if (this->gang_count_ == 1)
                return 1;

            // Calculate button number
            const uint8_t width = (TOUCH_MAX_POSITION + 1) / this->gang_count_;  // Width of each button region
            if (width < 1 or width > this->gang_count_)  // Invalid width - and prevents division by zero
                return 0;
            const uint8_t button = std::min(
                static_cast<uint8_t>((position / width) + 1), // Convert position to button index
                this->gang_count_ // Clamp to max gang count
            );
            return button;
        }

        void TxUltimateEasy::send_touch_(TouchPoint tp) {
            this->trigger_touch_event_.trigger(tp);
            switch (tp.state) {
                case TOUCH_STATE_RELEASE:
                    if (tp.x >= 17) {
                        tp.x -= 16;
                        ESP_LOGV(TAG, "Long touch - Released (x=%d)", tp.x);
                        this->trigger_long_touch_release_.trigger(tp);
                    } else {
                        ESP_LOGV(TAG, "Touch - Released (x=%d)", tp.x);
                        this->trigger_release_.trigger(tp);
                    }
                    break;

                case TOUCH_STATE_PRESS:
                    ESP_LOGV(TAG, "Touch - Pressed (x=%d)", tp.x);
                    this->trigger_touch_.trigger(tp);
                    break;

                case TOUCH_STATE_SWIPE_LEFT:
                    ESP_LOGV(TAG, "Swipe - Left (x=%d)", tp.x);
                    this->trigger_swipe_left_.trigger(tp);
                    break;

                case TOUCH_STATE_SWIPE_RIGHT:
                    ESP_LOGV(TAG, "Swipe - Right (x=%d)", tp.x);
                    this->trigger_swipe_right_.trigger(tp);
                    break;

                case TOUCH_STATE_MULTI_TOUCH:
                    ESP_LOGV(TAG, "Multi touch - Released");
                    this->trigger_multi_touch_release_.trigger(tp);
                    break;

                default:
                    break;
            }
        }

        bool TxUltimateEasy::is_valid_data(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes) {
            if (uart_received_bytes[0] != HEADER_BYTE_1 || 
                uart_received_bytes[1] != HEADER_BYTE_2 || 
                uart_received_bytes[2] != VALID_DATA_BYTE_2 || 
                uart_received_bytes[3] != VALID_DATA_BYTE_3) {
                return false;
            }

            int state = this->get_touch_state(uart_received_bytes);
            return (state == TOUCH_STATE_PRESS ||
                    state == TOUCH_STATE_RELEASE ||
                    state == TOUCH_STATE_SWIPE_LEFT ||
                    state == TOUCH_STATE_SWIPE_RIGHT ||
                    state == TOUCH_STATE_MULTI_TOUCH) &&
                    // Multi-touch events may have x < 0, all other events require valid x position
                    (uart_received_bytes[6] >= 0 || state == TOUCH_STATE_MULTI_TOUCH);
        }

        int TxUltimateEasy::get_touch_position_x(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes) {
            switch (uart_received_bytes[4]) {
                case TOUCH_STATE_RELEASE:
                case TOUCH_STATE_MULTI_TOUCH:
                case TOUCH_STATE_SWIPE_LEFT:
                case TOUCH_STATE_SWIPE_RIGHT:
                    return uart_received_bytes[5];

                default:
                    return uart_received_bytes[6];
            }
        }

        int TxUltimateEasy::get_touch_state(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes) {
            int state = uart_received_bytes[4];
            if (state == TOUCH_STATE_PRESS && uart_received_bytes[5] != 0) state = TOUCH_STATE_RELEASE;
            if (state == TOUCH_STATE_RELEASE && uart_received_bytes[5] == TOUCH_STATE_MULTI_TOUCH) state = TOUCH_STATE_MULTI_TOUCH;
            if (state == TOUCH_STATE_SWIPE) {
                state = (uart_received_bytes[5] == TOUCH_STATE_SWIPE_RIGHT) ? TOUCH_STATE_SWIPE_RIGHT : 
                        (uart_received_bytes[5] == TOUCH_STATE_SWIPE_LEFT) ? TOUCH_STATE_SWIPE_LEFT : state;
            }
            return state;
        }

        TouchPoint TxUltimateEasy::get_touch_point(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes) {
            TouchPoint tp;
            tp.x = this->get_touch_position_x(uart_received_bytes);
            if (tp.x >= 0)
                tp.button = this->get_button_from_position(static_cast<uint8_t>(tp.x));
            tp.state = this->get_touch_state(uart_received_bytes);
            switch (tp.state) {
                case TOUCH_STATE_RELEASE:
                    tp.state_str = "RELEASE";
                    break;
                case TOUCH_STATE_PRESS:
                    tp.state_str = "PRESS";
                    break;
                case TOUCH_STATE_SWIPE:
                    tp.state_str = "SWIPE";
                    break;
                case TOUCH_STATE_MULTI_TOUCH:
                    tp.state_str = "MULTI_TOUCH";
                    break;
                case TOUCH_STATE_SWIPE_RIGHT:
                    tp.state_str = "SWIPE_RIGHT";
                    break;
                case TOUCH_STATE_SWIPE_LEFT:
                    tp.state_str = "SWIPE_LEFT";
                    break;
                default:
                    tp.state_str = "Unknown";
                    break;
            }
            return tp;
        }

    } // namespace tx_ultimate_easy
} // namespace esphome
