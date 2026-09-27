// Passive CAN (RV-C) sniffer for the SRNE bus.
//
// The TWAI controller runs in LISTEN_ONLY mode: it never transmits and never
// sends ACK bits, so it cannot disturb the CU2 <-> device traffic.
// Frames are printed over USB as:
//
//   C <millis> <29-bit id hex> <data hex bytes>
//
// which tools/rvc_sniff.py --esp32 understands.

#include <Arduino.h>
#include "driver/twai.h"

#ifndef CAN_TX_PIN
#define CAN_TX_PIN 5  // transceiver TXD (driver requires a pin even in listen-only)
#endif
#ifndef CAN_RX_PIN
#define CAN_RX_PIN 4  // transceiver RXD
#endif

void setup() {
  Serial.begin(921600);

  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(
      (gpio_num_t)CAN_TX_PIN, (gpio_num_t)CAN_RX_PIN, TWAI_MODE_LISTEN_ONLY);
  g.rx_queue_len = 64;
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();  // RV-C
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  if (twai_driver_install(&g, &t, &f) != ESP_OK || twai_start() != ESP_OK) {
    Serial.println("# TWAI start failed");
    return;
  }
  Serial.println("# CAN listen-only, 250 kbps");
}

void loop() {
  twai_message_t msg;
  if (twai_receive(&msg, pdMS_TO_TICKS(100)) != ESP_OK) return;
  if (!msg.extd) {
    Serial.printf("# std id %03lx\n", (unsigned long)msg.identifier);
    return;
  }
  Serial.printf("C %lu %08lx", (unsigned long)millis(), (unsigned long)msg.identifier);
  for (int i = 0; i < msg.data_length_code; i++) Serial.printf(" %02x", msg.data[i]);
  Serial.print('\n');
}
