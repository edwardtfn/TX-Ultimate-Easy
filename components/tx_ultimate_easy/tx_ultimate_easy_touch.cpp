// tx_ultimate_easy_touch.cpp

#ifdef TX_ULTIMATE_EASY_HW_TOUCH

#include "esphome/core/log.h"
#include "tx_ultimate_easy_touch.h"
#include <cinttypes>
#include <string>

namespace esphome {
    namespace tx_ultimate_easy {

        // Log tag
        static const char *TAG = "tx_ultimate_easy.touch";

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

        /**
         * @brief Log the component configuration for TX Ultimate Easy.
         *
         * Logs the component identifier and the configured gang count constant.
         */
        void TxUltimateEasy::dump_config() {
            ESP_LOGCONFIG(TAG, "TX Ultimate Easy");
            ESP_LOGCONFIG(TAG, "  Gang count: %" PRIu8, TX_ULTIMATE_EASY_GANG_COUNT);
        }

        /**
         * @brief Maps a touch position to a 1-based button index.
         *
         * Maps a touch sensor position into one of the configured button (gang) regions and returns
         * the corresponding 1-based button index. If the position is out of range or cannot be
         * mapped, returns 0.
         *
         * @param position Touch position from the sensor.
         * @return uint8_t `1`..`TX_ULTIMATE_EASY_GANG_COUNT` for a mapped button, `0` if the position is invalid or unmapped.
         */
        uint8_t TxUltimateEasy::get_button_from_position(const uint8_t position) {
            // Validate position bounds
            if (position > TOUCH_MAX_POSITION)
                return 0;

            // Special case for single gang (only one button exists) or no selection
            if (TX_ULTIMATE_EASY_GANG_COUNT <= 1)
                return 1;

            // Calculate button width (rounds up to ensure full coverage)
            const uint8_t width =
                (TOUCH_MAX_POSITION + TX_ULTIMATE_EASY_GANG_COUNT) / TX_ULTIMATE_EASY_GANG_COUNT;  // Width of each button region
            if (width < 1)  // Invalid width - and prevents division by zero
                return 0;
            const uint8_t button = std::min(
                static_cast<uint8_t>((position / width) + 1),      // Convert position to button index
                static_cast<uint8_t>(TX_ULTIMATE_EASY_GANG_COUNT)  // Clamp to max gang count
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
                    ESP_LOGV(TAG, "Swipe - Left (from=%d, to=%d, from_button=%d, to_button=%d)",
                             tp.swipe_from, tp.swipe_to, tp.swipe_from_button, tp.swipe_to_button);
                    this->trigger_swipe_left_.trigger(tp);
                    break;

                case TOUCH_STATE_SWIPE_RIGHT:
                    ESP_LOGV(TAG, "Swipe - Right (from=%d, to=%d, from_button=%d, to_button=%d)",
                             tp.swipe_from, tp.swipe_to, tp.swipe_from_button, tp.swipe_to_button);
                    this->trigger_swipe_right_.trigger(tp);
                    break;

                case TOUCH_STATE_MULTI_TOUCH:
                    // NOTE: uart_received_bytes[5] for a multi-touch event is a fixed
                    // sentinel (0x0B), not a position. The hardware protocol does not
                    // report which buttons participated in a multi-touch gesture, so
                    // tp.x/tp.button are intentionally left invalid (see
                    // get_touch_position_x()). Do not rely on tp.button here.
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

        /**
         * @brief Decodes the lowest and highest touched channel from a swipe bitmap.
         *
         * uart_received_bytes[6] and uart_received_bytes[7] together form a 10-bit
         * bitmap of channels crossed during the swipe gesture:
         *   - uart_received_bytes[7] bits 0-7 represent channels 1-8
         *   - uart_received_bytes[6] bits 0-1 represent channels 9-10
         * (Confirmed both by the pre-existing implementation's comments and by
         * community findings on the blakadder/tx-ultimate Berry driver.)
         *
         * @param uart_received_bytes Raw frame bytes.
         * @param lowest_channel  Output: lowest channel number with its bit set (0 if none).
         * @param highest_channel Output: highest channel number with its bit set (0 if none).
         */
        void TxUltimateEasy::get_swipe_range(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes,
                                              uint8_t &lowest_channel, uint8_t &highest_channel) {
            lowest_channel = 0;
            highest_channel = 0;
            const uint16_t crossed = (static_cast<uint16_t>(uart_received_bytes[6]) << 8) |
                                      static_cast<uint16_t>(uart_received_bytes[7]);
            for (uint8_t ch = 1; ch <= TOUCH_MAX_POSITION; ch++) {
                if (crossed & (1 << (ch - 1))) {
                    if (lowest_channel == 0) lowest_channel = ch;
                    highest_channel = ch;
                }
            }
        }

        int TxUltimateEasy::get_touch_position_x(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes) {
            switch (uart_received_bytes[4]) {
                case TOUCH_STATE_RELEASE:
                    return uart_received_bytes[5];

                case TOUCH_STATE_MULTI_TOUCH:
                    // uart_received_bytes[5] is a fixed sentinel value (0x0B) that only
                    // marks "this is a multi-touch event". It is NOT a touch position,
                    // unlike TOUCH_STATE_RELEASE. The hardware provides no per-button
                    // information for multi-touch, so there is no valid position to
                    // report here. Returning -1 correctly prevents get_touch_point()
                    // from computing a bogus tp.button value from the sentinel byte.
                    return -1;

                case TOUCH_STATE_SWIPE_LEFT:
                case TOUCH_STATE_SWIPE_RIGHT: {
                    // Bytes 6-7 form a 10-bit bitmap of crossed channels (see
                    // get_swipe_range()). Kept for backward compatibility with
                    // existing consumers of tp.x: returns the highest crossed
                    // channel for a rightward swipe, or the lowest for a
                    // leftward swipe -- the same single endpoint the original
                    // implementation returned.
                    uint8_t lowest = 0, highest = 0;
                    this->get_swipe_range(uart_received_bytes, lowest, highest);
                    return (uart_received_bytes[5] == TOUCH_STATE_SWIPE_RIGHT) ? highest : lowest;
                }

                default:
                    return uart_received_bytes[6];
            }
        }

        int TxUltimateEasy::get_touch_state(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes) {
            int state = uart_received_bytes[4];
            if (state == TOUCH_STATE_PRESS && uart_received_bytes[5] != 0)
                state = TOUCH_STATE_RELEASE;
            if (state == TOUCH_STATE_RELEASE && uart_received_bytes[5] == TOUCH_STATE_MULTI_TOUCH)
                state = TOUCH_STATE_MULTI_TOUCH;
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

            if (tp.state == TOUCH_STATE_SWIPE_LEFT || tp.state == TOUCH_STATE_SWIPE_RIGHT) {
                uint8_t lowest = 0, highest = 0;
                this->get_swipe_range(uart_received_bytes, lowest, highest);
                if (tp.state == TOUCH_STATE_SWIPE_RIGHT) {
                    tp.swipe_from = lowest;
                    tp.swipe_to = highest;
                } else {  // TOUCH_STATE_SWIPE_LEFT
                    tp.swipe_from = highest;
                    tp.swipe_to = lowest;
                }
                tp.swipe_from_button = this->get_button_from_position(tp.swipe_from);
                tp.swipe_to_button = this->get_button_from_position(tp.swipe_to);
            }

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

#endif  // TX_ULTIMATE_EASY_HW_TOUCH
