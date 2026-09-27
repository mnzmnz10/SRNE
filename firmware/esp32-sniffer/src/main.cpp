// Passive RS485 sniffer for the SRNE bus.
//
// The RS485 transceiver is held in receive mode and the TX pin is not used,
// so this board can never put anything on the bus. Bytes are grouped into
// frames using the Modbus idle gap and printed over USB as:
//
//   F <millis> <hex bytes>
//
// which tools/sniff.py --esp32 understands. Other protocols (non-Modbus)
// are still printed the same way, just without a valid CRC.
//
// Serial commands (USB, 921600 baud):
//   B <baud>   change the bus baud rate (e.g. "B 19200")
//   G <n>      idle gap in character times that ends a frame (default 3.5 -> 4)

#include <Arduino.h>

#ifndef RS485_RX_PIN
#define RS485_RX_PIN 16  // module RO
#endif
#ifndef RS485_DE_RE_PIN
#define RS485_DE_RE_PIN 4  // module DE+RE tied together, held LOW
#endif

static uint32_t busBaud = 9600;
static uint32_t gapChars = 4;
static uint32_t gapUs = 0;

static uint8_t frame[512];
static size_t frameLen = 0;
static uint32_t lastByteUs = 0;
static uint32_t frameStartMs = 0;

static void startBus() {
  Serial2.end();
  Serial2.setRxBufferSize(4096);
  // TX pin -1: the UART has no transmit pin at all.
  Serial2.begin(busBaud, SERIAL_8N1, RS485_RX_PIN, -1);
  // One character = 10 bits at 8N1.
  gapUs = gapChars * 10UL * 1000000UL / busBaud;
  if (gapUs < 1000) gapUs = 1000;
  Serial.printf("# bus %lu baud, gap %lu us\n", (unsigned long)busBaud, (unsigned long)gapUs);
}

static void flushFrame() {
  if (frameLen == 0) return;
  Serial.printf("F %lu", (unsigned long)frameStartMs);
  for (size_t i = 0; i < frameLen; i++) Serial.printf(" %02x", frame[i]);
  Serial.print('\n');
  frameLen = 0;
}

static void handleCommand() {
  static String line;
  while (Serial.available()) {
    char c = Serial.read();
    if (c != '\n') {
      line += c;
      continue;
    }
    line.trim();
    if (line.startsWith("B ")) {
      busBaud = line.substring(2).toInt();
      startBus();
    } else if (line.startsWith("G ")) {
      gapChars = line.substring(2).toInt();
      startBus();
    }
    line = "";
  }
}

void setup() {
  pinMode(RS485_DE_RE_PIN, OUTPUT);
  digitalWrite(RS485_DE_RE_PIN, LOW);
  Serial.begin(921600);
  startBus();
}

void loop() {
  handleCommand();
  while (Serial2.available()) {
    if (frameLen == 0) frameStartMs = millis();
    if (frameLen < sizeof(frame)) frame[frameLen++] = Serial2.read();
    else flushFrame();
    lastByteUs = micros();
  }
  if (frameLen && micros() - lastByteUs > gapUs) flushFrame();
}
