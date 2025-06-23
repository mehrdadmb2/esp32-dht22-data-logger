#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#include <DHT.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>
#include <time.h>
#include <WebServer.h>
#include <WiFiClientSecure.h>

// ================== Hardware Settings ==================
#define DHTPIN 6
#define DHTTYPE DHT22

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define SSD1306_I2C_ADDRESS 0x3C
#define I2C_SDA 5
#define I2C_SCL 4

#define WIFI_SSID ">><<>><<"
#define WIFI_PASSWORD "MEHRdAd"

// Only use SWITCH_PIN_1 (pin 8) for page switching.
#define SWITCH_PIN_1 8
#define RGB_PIN 3
#define NUM_PIXELS 1
#define WHITE_LED_PIN 14
#define DISABLE_RGB_PIN 12

// ================== Global Objects and Variables ==================
DHT dht(DHTPIN, DHTTYPE);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_NeoPixel strip(NUM_PIXELS, RGB_PIN, NEO_GRB + NEO_KHZ800);
WebServer server(80);

float temp = 0.0, humidity = 0.0;
float internetTemp = 0.0, internetHumidity = 0.0; // reserved for potential use
float lastBuyPrice = 0.0, lastSellPrice = 0.0, lastGoldPrice = 0.0;

int currentPage = 1;
bool dataFetched = false;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

// Update internet data every 10 minutes
unsigned long lastUpdateTime = 0;
// به روزرسانی هر ۶ ساعت (۶ ساعت = 21600000 میلی‌ثانیه)
unsigned long updateInterval = 21600000; 
bool isFirstUpdate = true;

const IPAddress pingIP(8, 8, 8, 8);

// ------------------ Ping Caching ------------------
unsigned long lastPingUpdate = 0; // last ping update time
long cachedPing = -1;           // cached ping result
const unsigned long pingCacheInterval = 60000; // 1 minute

// ------------------ Simple Ping Function ------------------
long simplePing(IPAddress target, uint16_t port = 53, uint32_t timeout = 1000) {
  WiFiClient client;
  unsigned long startTime = millis();
  while (!client.connect(target, port)) {
    if (millis() - startTime > timeout) {
      return -1; // ping failed
    }
    delay(10);
  }
  unsigned long pingTime = millis() - startTime;
  client.stop();
  return pingTime;
}

// ================== Web Helper Functions ==================
void handleData() {
  DynamicJsonDocument doc(1024);
  doc["localTemperature"] = temp;
  doc["localHumidity"] = humidity;
  doc["internetTemperature"] = internetTemp;
  doc["internetHumidity"] = internetHumidity;
  doc["buy_price"] = lastBuyPrice;
  doc["sell_price"] = lastSellPrice;
  doc["gold_price"] = lastGoldPrice;
  
  // استفاده از کش پینگ به جای اجرای هر بار تابع پینگ
  if (millis() - lastPingUpdate > pingCacheInterval) {
    cachedPing = simplePing(pingIP);
    lastPingUpdate = millis();
  }
  if (cachedPing < 0) {
    doc["ping"] = "Fail";
  } else {
    doc["ping"] = cachedPing;
  }

  // کاهش فراوانی WiFi.scanNetworks() برای جلوگیری از بار اضافی
  static unsigned long lastNetworkScan = 0;
  if (millis() - lastNetworkScan > 30000) { // هر 30 ثانیه یکبار
    JsonArray devices = doc.createNestedArray("devices");
    int n = WiFi.scanNetworks();
    for (int i = 0; i < n; i++) {
      JsonObject dev = devices.createNestedObject();
      dev["name"] = WiFi.SSID(i);
      dev["mac"] = WiFi.BSSIDstr(i);
    }
    lastNetworkScan = millis();
  }
  
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    char timeStr[9];
    strftime(timeStr, sizeof(timeStr), "%H:%M:%S", &timeinfo);
    doc["time"] = timeStr;
    char dateStr[11];
    strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", &timeinfo);
    doc["date"] = dateStr;
  } else {
    doc["time"] = "N/A";
    doc["date"] = "N/A";
  }
  
  String jsonResponse;
  serializeJson(doc, jsonResponse);
  server.send(200, "application/json", jsonResponse);
}

void handleRoot() {
  String html = "<!DOCTYPE html><html lang='en'>"
                "<head>"
                "<meta charset='UTF-8'>"
                "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                "<title>ESP32 Sensor Data</title>"
                "<style>"
                "body { margin:0; padding:0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #f5f5f5; }"
                ".container { padding: 20px; max-width: 800px; margin: auto; }"
                "h1 { text-align: center; margin-bottom: 20px; }"
                ".grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); grid-gap: 20px; }"
                ".card { background: #1e1e1e; border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }"
                ".label { font-size: 14px; font-weight: bold; }"
                ".value { font-size: 16px; margin-top: 5px; }"
                "button { padding: 10px 15px; margin: 10px auto; display: block; border: none; border-radius: 4px; background-color: #2196F3; color: white; font-size: 16px; cursor: pointer; }"
                "button:hover { background-color: #1976D2; }"
                "ul { list-style-type: none; padding: 0; margin: 0; }"
                "@media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }"
                "</style>"
                "</head>"
                "<body>"
                "<div class='container'>"
                "<h1>ESP32 Sensor Data</h1>"
                "<div class='grid'>"
                "<div class='card'><div class='label'>Local Temp:</div><div id='temp' class='value'>-- C</div></div>"
                "<div class='card'><div class='label'>Local Humidity:</div><div id='humidity' class='value'>-- %</div></div>"
                // Page 1: local sensor data and prices
                "<div class='card'><div class='label'>USD to IRR:</div><div id='buy' class='value'>-- IRR</div></div>"
                "<div class='card'><div class='label'>USD to IRR:</div><div id='sell' class='value'>-- IRR</div></div>"
                "<div class='card'><div class='label'>Gold (IRR):</div><div id='gold' class='value'>-- IRR</div></div>"
                "<div class='card'><div class='label'>Ping:</div><div id='ping' class='value'>--</div></div>"
                // New cards for internet weather data
                "<div class='card'><div class='label'>Internet Temp:</div><div id='internetTemp' class='value'>-- C</div></div>"
                "<div class='card'><div class='label'>Internet Humidity:</div><div id='internetHumidity' class='value'>-- %</div></div>"
                "<div class='card'><div class='label'>Time:</div><div id='time' class='value'>--:--:--</div></div>"
                "<div class='card'><div class='label'>Date:</div><div id='date' class='value'>--/--/----</div></div>"
                "</div>"  // end grid
                "<button onclick='fetchData()'>Refresh Now</button>"
                "</div>"  // end container
                "<script>"
                "function fetchData(){"
                "  fetch('/data')"
                "    .then(response => response.json())"
                "    .then(data => {"
                "      document.getElementById('temp').innerText = data.localTemperature + ' C';"
                "      document.getElementById('humidity').innerText = data.localHumidity + ' %';"
                "      document.getElementById('buy').innerText = data.buy_price + ' IRR';"
                "      document.getElementById('sell').innerText = data.sell_price + ' IRR';"
                "      document.getElementById('gold').innerText = data.gold_price + ' IRR';"
                "      document.getElementById('ping').innerText = data.ping;"
                "      document.getElementById('internetTemp').innerText = data.internetTemperature + ' C';"
                "      document.getElementById('internetHumidity').innerText = data.internetHumidity + ' %';"
                "      document.getElementById('time').innerText = data.time;"
                "      document.getElementById('date').innerText = data.date;"
                "    })"
                "    .catch(err => console.error(err));"
                "}"
                "setInterval(fetchData, 5000);"
                "window.onload = fetchData;"
                "</script>"
                "</body></html>";
  server.send(200, "text/html", html);
}

// ================== WiFi and Data Retrieval Functions ==================
void connectToWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  unsigned long startAttemptTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 20000) {
    delay(500);
    Serial.print(".");
  }
  if(WiFi.status() == WL_CONNECTED){
    Serial.println("\nWiFi connected!");
  } else {
    Serial.println("\nWiFi connection failed. Restarting...");
    ESP.restart(); // restart if not connected
  }
}

void updateDHTData() {
  temp = dht.readTemperature();
  humidity = dht.readHumidity();
  if (isnan(temp) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor!");
  }
}

void fetchWeatherData() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected. Skipping weather fetch.");
    return;
  }
  HTTPClient http;
  String weatherURL = "http://api.openweathermap.org/data/2.5/weather?q=Shiraz&appid=f768d5b78078094d0b5720a1876353a2&units=metric";
  http.begin(weatherURL);
  int httpCode = http.GET();
  if (httpCode > 0) {
    String payload = http.getString();
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, payload);
    if(!error) {
      internetTemp = doc["main"]["temp"];
      internetHumidity = doc["main"]["humidity"];
    } else {
      Serial.println("JSON parse error in weather data");
      internetTemp = 0;
      internetHumidity = 0;
    }
  } else {
    Serial.println("Error on HTTP request for weather data");
    internetTemp = 0;
    internetHumidity = 0;
  }
  http.end();
}

void fetchPrices() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    // استفاده از وب سرویس نواسان با کلید API داده شده
    String url = "http://api.navasan.tech/latest/?api_key=freeT9cMd0c1xllrZwm29QF4EOQClmzM";
    http.begin(url);
    int httpResponseCode = http.GET();
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Navasan API response:");
      Serial.println(response);
      DynamicJsonDocument doc(4096);
      DeserializationError error = deserializeJson(doc, response);
      if (!error) {
        // دریافت قیمت دلار به صورت خرید و فروش از دلار تهران
        lastBuyPrice = doc["usd_buy"]["value"].as<float>();
        lastSellPrice = doc["usd_sell"]["value"].as<float>();
        // دریافت قیمت طلای ۱۸ عیار
        lastGoldPrice = doc["18ayar"]["value"].as<float>();
      } else {
        Serial.println("JSON parse error in Navasan API response");
        lastBuyPrice = 0;
        lastSellPrice = 0;
        lastGoldPrice = 0;
      }
    } else {
      Serial.printf("Error retrieving Navasan API data, code: %d\n", httpResponseCode);
      lastBuyPrice = 0;
      lastSellPrice = 0;
      lastGoldPrice = 0;
    }
    http.end();
  }
}

// ================== OLED Display Functions ==================
void displayPage1() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  display.setCursor(0, 0);
  display.print("Temp: ");
  display.print(temp);
  display.print(" C");
  
  display.setCursor(0, 10);
  display.print("Humidity: ");
  display.print(humidity);
  display.print(" %");
  
  int boxX = 0, boxY = 20, boxWidth = 128, boxHeight = 12;
  display.drawRect(boxX, boxY, boxWidth, boxHeight, SSD1306_WHITE);
  
  display.setTextWrap(false);
  
  struct tm timeinfo;
  char timeStr[9] = "00:00:00";
  char dateStr[11] = "00/00/0000";
  if (getLocalTime(&timeinfo)) {
    strftime(timeStr, sizeof(timeStr), "%H:%M:%S", &timeinfo);
    strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", &timeinfo);
  }
  
  // Marquee text with IRR unit for prices
  String marqueeText = String(dateStr) + " " + String(timeStr) +
                       " | USD: " + String(lastBuyPrice, 2) + " IRR" +
                       " | GOLD: " + String(lastGoldPrice, 2) + " IRR   ";
  
  int16_t x1, y1;
  uint16_t textWidth, textHeight;
  display.getTextBounds(marqueeText, 0, 0, &x1, &y1, &textWidth, &textHeight);
  
  static int scrollOffset = 0;
  display.setCursor(boxX - scrollOffset, boxY + (boxHeight - textHeight) / 2);
  display.print(marqueeText);
  
  scrollOffset++;
  if (scrollOffset > textWidth) {
    scrollOffset = 0;
  }
  
  display.display();
}

void displayPage2() {
  // Page 2 now displays only USD (buy price), GOLD (gold price), and PING
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  display.setCursor(0, 0);
  display.print("USD: ");
  display.print(lastBuyPrice, 2);
  display.print(" IRR");
  
  display.setCursor(0, 10);
  display.print("GOLD: ");
  display.print(lastGoldPrice, 2);
  display.print(" IRR");
  
  display.setCursor(0, 20);
  if(cachedPing < 0) {
    display.print("PING: Fail");
  } else {
    display.print("PING: ");
    display.print(cachedPing);
    display.print(" ms");
  }
  
  display.display();
}

// ================== LED and NeoPixel Functions ==================
void blinkWhiteLED() {
  digitalWrite(WHITE_LED_PIN, HIGH);
  delay(200);
  digitalWrite(WHITE_LED_PIN, LOW);
  delay(200);
}

void RGBtemp() {
  float currentTemp = (internetTemp != 0.0) ? internetTemp : temp;
  #ifdef RGB_BUILTIN
    if (currentTemp < 15) {
      neopixelWrite(RGB_BUILTIN, 0, 0, 255);  // Blue
    }
    else if (currentTemp >= 15 && currentTemp <= 25) {
      neopixelWrite(RGB_BUILTIN, 0, 255, 0);  // Green
    }
    else {
      neopixelWrite(RGB_BUILTIN, 255, 0, 0);  // Red
    }
  #endif
}

void PowerON() {
  int lED = 1;
  #ifdef RGB_BUILTIN
  if (lED == 1) {
    digitalWrite(RGB_BUILTIN, HIGH);
    delay(100);
    digitalWrite(RGB_BUILTIN, LOW);
    delay(100);
    neopixelWrite(RGB_BUILTIN, 255, 0, 0);
    delay(100);
    neopixelWrite(RGB_BUILTIN, 0, 255, 0);
    delay(100);
    neopixelWrite(RGB_BUILTIN, 0, 0, 255);
  } else {
    neopixelWrite(RGB_BUILTIN, 0, 0, 0);
    delay(1000);
  }
  #endif
}

// ================== Setup and Loop ==================
void setup() {
  Serial.begin(115200);
  Wire.begin(I2C_SDA, I2C_SCL);
  pinMode(SWITCH_PIN_1, INPUT_PULLUP);
  pinMode(WHITE_LED_PIN, OUTPUT);
  pinMode(DISABLE_RGB_PIN, INPUT_PULLUP);

  if (!display.begin(SSD1306_SWITCHCAPVCC, SSD1306_I2C_ADDRESS)) {
    Serial.println("Failed to initialize OLED");
    while (1);
  }
  display.clearDisplay();
  
  dht.begin();
  connectToWiFi();
  
  // Set time to Iran Time (UTC+3:30)
  configTime(3 * 3600 + 30 * 60, 0, "pool.ntp.org", "time.nist.gov");
  
  strip.begin();
  strip.show();
  PowerON();
  
  // Initial data update
  fetchWeatherData();
  fetchPrices();
  dataFetched = true;
  lastUpdateTime = millis();
  
  server.on("/data", HTTP_GET, handleData);
  server.on("/", HTTP_GET, handleRoot);
  server.begin();
  Serial.println("Web server started");
}

void loop() {
  // تغییر صفحه با سوئیچ
  if (digitalRead(SWITCH_PIN_1) == LOW) {
    if (millis() - lastDebounceTime > debounceDelay) {
      currentPage = (currentPage == 1) ? 2 : 1;
      lastDebounceTime = millis();
      blinkWhiteLED();
    }
  }

  // به‌روزرسانی قیمت‌ها هر6 ساعت (21600000 میلی‌ثانیه)
  if(millis() - lastUpdateTime >= 21600000) {  
    fetchPrices();
    lastUpdateTime = millis();
  }

  // به‌روزرسانی صفحه OLED
  if (currentPage == 1) {
    updateDHTData();
    displayPage1();
  } else if (currentPage == 2) {
    displayPage2();
  }

  // مدیریت پین غیرفعال کردن RGB
  if (digitalRead(DISABLE_RGB_PIN) == LOW) {
    #ifdef RGB_BUILTIN
    neopixelWrite(RGB_BUILTIN, 0, 0, 0);
    #endif
  } else {
    #ifdef RGB_BUILTIN
    neopixelWrite(RGB_BUILTIN, 0, 0, 0);
    #endif
  }

  // بررسی اتصال WiFi و اتصال مجدد در صورت لزوم
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  server.handleClient();
  delay(50);
}
