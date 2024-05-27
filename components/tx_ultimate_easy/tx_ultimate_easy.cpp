#include "esphome/core/log.h"
#include "tx_ultimate_easy.h"

namespace esphome {
    namespace tx_ultimate_easy {
        static const char *TAG = "tx_ultimate_easy";

        void TxUltimateEasy::setup() {
            ESP_LOGI("log", "%s", "Tx Ultimate Easy is initialized");
        }

        void TxUltimateEasy::loop() {
            bool found = false;
            int uart_received_bytes[15] = {};
            int byte = -1;
            int i = 0;
            while (this->available()) {
                byte = this->read();
                if (byte == 170) {
                handle_touch(uart_received_bytes);
                i = 0;
                }
                uart_received_bytes[i] = byte;
                i++;
                if (byte != 0) {
                found = true;
                }
            };
            if (found) handle_touch(uart_received_bytes);
        }

        void TxUltimateEasy::handle_touch(int uart_received_bytes[]) {
            ESP_LOGVV(TAG, "------------");
            ESP_LOGVV(TAG, "- UART-Log -");
            ESP_LOGVV(TAG, "------------");
            for (int i = 0; i < 15; i++) ESP_LOGVV(TAG, "UART - Log - Byte[%i]: %i", i, uart_received_bytes[i]);
            if (is_valid_data(uart_received_bytes)) send_touch_(get_touch_point(uart_received_bytes));
        }

        void TxUltimateEasy::dump_config() { ESP_LOGCONFIG(TAG, "Tx Ultimate Easy"); }

        void TxUltimateEasy::send_touch_(TouchPoint tp) {
            this->trigger_touch_event_.trigger(tp);
            switch (tp.state) {
                case TOUCH_STATE_RELEASE:
                    if (tp.x >= 17) {
                        tp.x = tp.x - 16;
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

        bool TxUltimateEasy::is_valid_data(int uart_received_bytes[]) {
            bool valid = true;
            if (!(uart_received_bytes[0] == 170 && uart_received_bytes[1] == 85 && uart_received_bytes[2] == 1 && uart_received_bytes[3] == 2)) return false;

            int state = get_touch_state(uart_received_bytes);
            if (state != TOUCH_STATE_PRESS &&
                state != TOUCH_STATE_RELEASE &&
                state != TOUCH_STATE_SWIPE_LEFT &&
                state != TOUCH_STATE_SWIPE_RIGHT &&
                state != TOUCH_STATE_MULTI_TOUCH)
                return false;

            if (uart_received_bytes[6] < 0 && state != TOUCH_STATE_MULTI_TOUCH) return false;

            return true;
        }

        int TxUltimateEasy::get_touch_position_x(int uart_received_bytes[]) {
            int state = uart_received_bytes[4];
            switch (state) {
                case TOUCH_STATE_RELEASE:
                case TOUCH_STATE_MULTI_TOUCH:
                case TOUCH_STATE_SWIPE_LEFT:
                case TOUCH_STATE_SWIPE_RIGHT:
                    return uart_received_bytes[5];
                    break;

                default:
                    return uart_received_bytes[6];
                    break;
            }
        }

        int TxUltimateEasy::get_touch_state(int uart_received_bytes[]) {
            int state = uart_received_bytes[4];
            if (state == TOUCH_STATE_PRESS && uart_received_bytes[5] != 0) state = TOUCH_STATE_RELEASE;
            if (state == TOUCH_STATE_RELEASE && uart_received_bytes[5] == TOUCH_STATE_MULTI_TOUCH) state = TOUCH_STATE_MULTI_TOUCH;
            if (state == TOUCH_STATE_SWIPE) {
                if (uart_received_bytes[5] == TOUCH_STATE_SWIPE_RIGHT) state = TOUCH_STATE_SWIPE_RIGHT;
                else if (uart_received_bytes[5] == TOUCH_STATE_SWIPE_LEFT) state = TOUCH_STATE_SWIPE_LEFT;
            }
            return state;
        }

        TouchPoint TxUltimateEasy::get_touch_point(int uart_received_bytes[]) {
            TouchPoint tp;
            tp.x = get_touch_position_x(uart_received_bytes);
            tp.state = get_touch_state(uart_received_bytes);
            tp.state_str = "Unknown";
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
            }
            return tp;
        }

    } // namespace tx_ultimate_easy
} // namespace esphome