#include <primitive_lcd.h>

PrimitiveLCD::PrimitiveLCD() : LGFX() {
  lcdMutex = xSemaphoreCreateMutex();
  init();
}

void PrimitiveLCD::drawJpg(const uint8_t *jpg_data, size_t jpg_len, uint16_t x, uint16_t y, uint16_t maxWidth, uint16_t maxHeight, uint16_t offX, uint16_t offY, jpeg_div_t scale) {
  if (lockLcd()) {
    drawJpg(jpg_data, jpg_len, x, y, maxWidth, maxHeight, offX, offY, scale);
    unlockLcd();
  }
}

void PrimitiveLCD::qrcode(const char *string, uint16_t x, uint16_t y, uint8_t width, uint8_t version) {
  if (lockLcd()) {
    qrcode(string, x, y, width, version);
    unlockLcd();
  }
}

void PrimitiveLCD::printColorText(const String& input) {
  String text = input;
  uint16_t textColor = color565(255, 255, 255); // Default text color: white
  uint16_t bgColor = color565(0, 0, 0);         // Default background color: black
  int index = 0;
  if (lockLcd()) {
  while (index < text.length()) {
      if (text.charAt(index) == '\x1b' && text.charAt(index + 1) == '[') {
        int mIndex = text.indexOf('m', index);
        if (mIndex != -1) {
          String seq = text.substring(index + 2, mIndex);
          int code = seq.toInt();
          if (seq.startsWith("4")) {
            bgColor = colorMap(code, true);
          } else if (seq.startsWith("3")) {
            textColor = colorMap(code, false);
          }
          text.remove(index, mIndex - index + 1);
          continue;
        }
      }
      setTextColor(textColor, bgColor);
      print(text.charAt(index));
      index++;
    }
    unlockLcd();
  }
}

void PrimitiveLCD::fillScreen(uint16_t color) {
  if (lockLcd()) {
    fillScreen(color);
    unlockLcd();
  }
}

void PrimitiveLCD::fillRect(int x1, int y1, int w, int h, uint16_t color) {
  if (lockLcd()) {
    fillRect(x1, y1, w, h, color);
    unlockLcd();
  }
}

void PrimitiveLCD::drawRect(int x1, int y1, int w, int h, uint16_t color) {
  if (lockLcd()) {
    drawRect(x1, y1, w, h, color);
    unlockLcd();
  }
}

void PrimitiveLCD::drawLine(int x1, int y1, int x2, int y2, uint16_t color){
  if (lockLcd()) {
    drawLine(x1, y1, x2, y2, color);
    unlockLcd();
  }
};

void PrimitiveLCD::drawPixel(int x, int y, uint16_t color){
  if (lockLcd()) {
    drawPixel(x, y, color);
    unlockLcd();
  }
};

void PrimitiveLCD::setCursor(int x, int y){
  if (lockLcd()) {
    setCursor(x,y);
    unlockLcd();
  }
};

void PrimitiveLCD::setRotation(int lcd_rotation){
  if (lockLcd()) {
    setRotation(lcd_rotation);
    unlockLcd();
  }
}

void PrimitiveLCD::clear(){
  if (lockLcd()) {
    clear();
    unlockLcd();
  }
}

void PrimitiveLCD::setTextSize(float text_size){
  if (lockLcd()) {
    setTextSize(text_size);
    unlockLcd();
  }
}

uint16_t PrimitiveLCD::colorMap(int code, bool isBackground) {
  if (isBackground) {
    switch (code) {
    case 40: return color565(0, 0, 0);     // Black
    case 41: return color565(255, 0, 0);   // Red
    case 42: return color565(0, 255, 0);   // Green
    case 43: return color565(255, 255, 0); // Yellow
    case 44: return color565(0, 0, 255);   // Blue
    case 45: return color565(255, 0, 255); // Magenta
    case 46: return color565(0, 255, 255); // Cyan
    case 47: return color565(255, 255, 255); // White
    case 49: return color565(0, 0, 0);     // Default (Black)
    default: return color565(0, 0, 0);
    }
  } else {
    switch (code) {
    case 30: return color565(0, 0, 0);     // Black
    case 31: return color565(255, 0, 0);   // Red
    case 32: return color565(0, 255, 0);   // Green
    case 33: return color565(255, 255, 0); // Yellow
    case 34: return color565(0, 0, 255);   // Blue
    case 35: return color565(255, 0, 255); // Magenta
    case 36: return color565(0, 255, 255); // Cyan
    case 37: return color565(255, 255, 255); // White
    case 39: return color565(255, 255, 255); // Default (White)
    default: return color565(255, 255, 255);
    }
  }
}
  
bool PrimitiveLCD::lockLcd() {
  // ミューテックスのロックを試みる（最大100ms待機）
  return xSemaphoreTake(lcdMutex, pdMS_TO_TICKS(100)) == pdTRUE;
}

void PrimitiveLCD::unlockLcd() {
  // ミューテックスを解放
  xSemaphoreGive(lcdMutex);
}
