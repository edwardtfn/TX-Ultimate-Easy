// tx_ultimate_easy_touch.cpp

#ifdef TX_ULTIMATE_EASY_HW_TOUCH

#include "esphome/core/hal.h"  // For millis()
#include "esphome/core/log.h"
#include "tx_ultimate_easy_touch.h"
#include <cinttypes>
#include <string>

namespace esphome {
namespace tx_ultimate_easy {

// Log tag
static const char *TAG = "tx_ultimate_easy.touch";

void TxUltimateEasy::setup() { ESP_LOGI(TAG, "TX Ultimate Easy is initialized"); }

/**
 * @brief Reads the touch panel UART and dispatches each complete frame.
 *
 * A frame starts with the 0xAA 0x55 header. The frame being received is kept across loop() calls, so a frame
 * split across them (the UART read caught it mid-transmission) is completed by the next call instead of lost.
 *
 * A frame is dispatched as soon as UART_FRAME_DECODE_SIZE bytes are received, as no later byte is decoded, and
 * the rest of it is ignored. This also keeps a 0xAA in the payload (e.g. a swipe channel bitmap) from being taken
 * as a new header. A 0xAA as the last decoded byte is only taken as a new header if a 0x55 follows it. A shorter frame
 * is dispatched when a new header arrives or after UART_FRAME_IDLE_TIMEOUT_MS without new bytes, if it has at least
 * UART_FRAME_MIN_SIZE bytes (all UART_FRAME_DECODE_SIZE bytes for a swipe); otherwise it is discarded. A lone 0xAA
 * followed by a gap of UART_HEADER_GAP_TIMEOUT_MS is not taken as the start of a header.
 */
void TxUltimateEasy::loop() {
  bool received = false;
  while (this->available()) {
    const int byte = this->read();
    if (byte < 0)
      break;
    received = true;
    const uint32_t now = millis();
    // Bytes of a frame arrive back-to-back: after a gap, an earlier byte is not part of the same header or frame
    const bool contiguous = (now - this->uart_last_byte_ms_) < UART_HEADER_GAP_TIMEOUT_MS;
    const int previous_byte = contiguous ? this->uart_last_byte_ : -1;
    this->uart_last_byte_ = byte;
    this->uart_last_byte_ms_ = now;
    if (!contiguous && this->uart_frame_size_ == 1 && !this->uart_frame_dispatched_)
      this->uart_frame_size_ = 0;  // Expire a lone 0xAA, so a later 0x55 does not complete it as a header
    const bool receiving = this->uart_frame_size_ > 0 && !this->uart_frame_dispatched_;

    // A header (0xAA 0x55) other than the one of the frame being received always starts a new frame
    if (byte == HEADER_BYTE_2 && previous_byte == HEADER_BYTE_1 && !(receiving && this->uart_frame_size_ == 1)) {
      if (receiving) {
        // The current frame ended before this header: drop the header's 0xAA from it and dispatch it
        if (this->uart_frame_[this->uart_frame_size_ - 1] == HEADER_BYTE_1)
          this->uart_frame_[--this->uart_frame_size_] = 0;
        this->flush_frame_();
      }  // if receiving
      this->start_frame_(2);
      continue;
    }

    if (!receiving) {
      // Waiting for a new frame: anything other than the first header byte is ignored
      if (byte == HEADER_BYTE_1)
        this->start_frame_(1);
      continue;
    }

    if (this->uart_frame_size_ == 1 && byte != HEADER_BYTE_2) {
      // Not a header: discard, or restart if this is the first byte of a new header
      if (byte == HEADER_BYTE_1) {
        this->start_frame_(1);
      } else {
        this->uart_frame_size_ = 0;
      }
      continue;
    }

    if (this->uart_frame_size_ >= UART_FRAME_DECODE_SIZE) {
      // Byte 7 was 0xAA and this byte is not 0x55: it was payload (e.g. a swipe bitmap), not a new header.
      // Dispatch the frame, and handle this byte as the first one after it.
      this->flush_frame_();
      if (byte == HEADER_BYTE_1)
        this->start_frame_(1);
      continue;
    }

    this->uart_frame_[this->uart_frame_size_++] = byte;
    // No later byte is decoded: dispatch now and ignore the rest of the frame. A 0xAA in byte 7 may instead be
    // the start of the next header, after a shorter frame: the next byte decides.
    if (this->uart_frame_size_ >= UART_FRAME_DECODE_SIZE && byte != HEADER_BYTE_1)
      this->flush_frame_();
  }  // while available

  // Incomplete frame: dispatch it once no more bytes arrive, if long enough to be decoded
  if (this->uart_frame_size_ > 0 && !this->uart_frame_dispatched_) {
    if (this->uart_frame_size_ >= UART_FRAME_MIN_SIZE &&
        millis() - this->uart_last_byte_ms_ >= UART_FRAME_IDLE_TIMEOUT_MS) {
      this->flush_frame_();
    } else if (received) {
      ESP_LOGV(TAG, "UART - Partial frame: %" PRIu8 " bytes, waiting for the rest", this->uart_frame_size_);
    }
  }  // if incomplete frame
}

void TxUltimateEasy::start_frame_(const uint8_t header_size) {
  this->uart_frame_.fill(0);
  this->uart_frame_[0] = HEADER_BYTE_1;
  if (header_size > 1)
    this->uart_frame_[1] = HEADER_BYTE_2;
  this->uart_frame_size_ = header_size;
  this->uart_frame_dispatched_ = false;
}

void TxUltimateEasy::flush_frame_() {
  // A swipe needs all UART_FRAME_DECODE_SIZE bytes, as its channel bitmap ends in byte 7
  const bool truncated_swipe =
      this->uart_frame_[4] == TOUCH_STATE_SWIPE && this->uart_frame_size_ < UART_FRAME_DECODE_SIZE;
  if (this->uart_frame_size_ >= UART_FRAME_MIN_SIZE && !truncated_swipe) {
    this->handle_touch(this->uart_frame_);
  } else if (this->uart_frame_size_ > 0) {
    ESP_LOGV(TAG, "UART - Discarded incomplete frame: %" PRIu8 " bytes", this->uart_frame_size_);
  }
  this->uart_frame_dispatched_ = true;
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
  const uint8_t button = std::min(static_cast<uint8_t>((position / width) + 1),      // Convert position to button index
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
      ESP_LOGV(TAG, "Swipe - Left (from=%d, to=%d, from_button=%d, to_button=%d)", tp.swipe_from, tp.swipe_to,
               tp.swipe_from_button, tp.swipe_to_button);
      this->trigger_swipe_left_.trigger(tp);
      break;

    case TOUCH_STATE_SWIPE_RIGHT:
      ESP_LOGV(TAG, "Swipe - Right (from=%d, to=%d, from_button=%d, to_button=%d)", tp.swipe_from, tp.swipe_to,
               tp.swipe_from_button, tp.swipe_to_button);
      this->trigger_swipe_right_.trigger(tp);
      break;

    case TOUCH_STATE_MULTI_TOUCH:
      // No position is reported for multi-touch: tp.x = -1, tp.button = 0
      ESP_LOGV(TAG, "Multi touch - Released");
      this->trigger_multi_touch_release_.trigger(tp);
      break;

    default:
      break;
  }
}

bool TxUltimateEasy::is_valid_data(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes) {
  if (uart_received_bytes[0] != HEADER_BYTE_1 || uart_received_bytes[1] != HEADER_BYTE_2 ||
      uart_received_bytes[2] != VALID_DATA_BYTE_2 || uart_received_bytes[3] != VALID_DATA_BYTE_3) {
    return false;
  }

  int state = this->get_touch_state(uart_received_bytes);
  return (state == TOUCH_STATE_PRESS || state == TOUCH_STATE_RELEASE || state == TOUCH_STATE_SWIPE_LEFT ||
          state == TOUCH_STATE_SWIPE_RIGHT || state == TOUCH_STATE_MULTI_TOUCH) &&
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
 *
 * @param uart_received_bytes Raw frame bytes.
 * @param lowest_channel  Output: lowest channel number with its bit set (0 if none).
 * @param highest_channel Output: highest channel number with its bit set (0 if none).
 */
void TxUltimateEasy::get_swipe_range(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes,
                                     uint8_t &lowest_channel, uint8_t &highest_channel) {
  lowest_channel = 0;
  highest_channel = 0;
  const uint16_t crossed =
      static_cast<uint16_t>(((uart_received_bytes[6] & 0xFF) << 8) | (uart_received_bytes[7] & 0xFF));
  for (uint8_t ch = 1; ch <= TOUCH_MAX_POSITION; ch++) {
    if ((crossed & (1U << (ch - 1))) == 0)
      continue;  // Channel not crossed
    if (lowest_channel == 0)
      lowest_channel = ch;
    highest_channel = ch;
  }  // for ch
}

/**
 * @brief Extracts the touch position from a press/release frame.
 *
 * Swipe and multi-touch frames are handled in get_touch_point() and never reach this function.
 *
 * @param uart_received_bytes Raw frame bytes.
 * @return Touch position reported by the touch panel.
 */
int TxUltimateEasy::get_touch_position_x(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes) {
  switch (uart_received_bytes[4]) {
    case TOUCH_STATE_RELEASE:
      return uart_received_bytes[5];

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
    state = (uart_received_bytes[5] == TOUCH_STATE_SWIPE_RIGHT)  ? TOUCH_STATE_SWIPE_RIGHT
            : (uart_received_bytes[5] == TOUCH_STATE_SWIPE_LEFT) ? TOUCH_STATE_SWIPE_LEFT
                                                                 : state;
  }
  return state;
}

TouchPoint TxUltimateEasy::get_touch_point(const std::array<int, UART_RECEIVED_BYTES_SIZE> &uart_received_bytes) {
  TouchPoint tp;
  tp.state = this->get_touch_state(uart_received_bytes);

  if (tp.state == TOUCH_STATE_SWIPE_LEFT || tp.state == TOUCH_STATE_SWIPE_RIGHT) {
    // Swipes report a crossed-channel bitmap instead of a single position (tp.x stays -1)
    uint8_t lowest = 0;
    uint8_t highest = 0;
    this->get_swipe_range(uart_received_bytes, lowest, highest);
    const bool swipe_right = (tp.state == TOUCH_STATE_SWIPE_RIGHT);
    tp.swipe_from = swipe_right ? lowest : highest;
    tp.swipe_to = swipe_right ? highest : lowest;
    if (tp.swipe_from > 0) {  // Empty bitmap: keep buttons at 0 (unknown)
      tp.swipe_from_button = this->get_button_from_position(tp.swipe_from);
      tp.swipe_to_button = this->get_button_from_position(tp.swipe_to);
    }  // if (tp.swipe_from > 0)
  } else if (tp.state != TOUCH_STATE_MULTI_TOUCH) {
    // Multi-touch frames carry the 0x0B marker in byte 5, not a position (tp.x stays -1)
    tp.x = this->get_touch_position_x(uart_received_bytes);
  }  // if (tp.state ...)

  if (tp.x >= 0)
    tp.button = this->get_button_from_position(static_cast<uint8_t>(tp.x));

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

}  // namespace tx_ultimate_easy
}  // namespace esphome

#endif  // TX_ULTIMATE_EASY_HW_TOUCH
