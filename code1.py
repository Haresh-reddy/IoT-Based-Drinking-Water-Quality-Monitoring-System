#define BLYNK_PRINT Serial

#include <WiFi.h>
#include <BlynkSimpleEsp32.h>
#include <DFRobotDFPlayerMini.h>
#include <HardwareSerial.h>

#define BLYNK_TEMPLATE_ID "TMPL3oBWx9P0u"
#define BLYNK_TEMPLATE_NAME "Water monitoring"
#define BLYNK_AUTH_TOKEN "YOUR_AUTH_TOKEN"

char ssid[] = "Hii";
char pass[] = "12345678";

#define PH_PIN 34
#define TURB_PIN 35
#define TDS_PIN 32
#define DF_RX 16
#define DF_TX 17

float ph_min = 6.5;
float ph_max = 8.5;
float turb_max = 5.0;
float tds_max = 500.0;

float ph_offset = 0.0;
float turb_clear_voltage = 2.75;
float tds_factor = 0.13;

HardwareSerial dfSerial(2);
DFRobotDFPlayerMini player;
BlynkTimer timer;

int lastErrorCode = 0;
unsigned long lastAudioTime = 0;

float readVoltage(int pin)
{
    long sum = 0;

    for (int i = 0; i < 30; i++)
    {
        sum += analogRead(pin);
        delay(5);
    }

    float avg = sum / 30.0;
    return avg * (3.3 / 4095.0);
}

void sendData()
{
    float phVoltage = readVoltage(PH_PIN);
    float turbVoltage = readVoltage(TURB_PIN);
    float tdsVoltage = readVoltage(TDS_PIN);

    float pH = 7 + ((2.5 - phVoltage) * 3.5) + ph_offset;

    if (pH < 0) pH = 0;
    if (pH > 14) pH = 14;

    float turbidity = (turb_clear_voltage - turbVoltage) * 300;

    if (turbidity < 0) turbidity = 0;

    float tds_raw = (tdsVoltage / 2.3) * 1000;
    float tds = tds_raw * tds_factor;

    Serial.println("------ Water Data ------");
    Serial.print("pH: ");
    Serial.println(pH);

    Serial.print("Turbidity: ");
    Serial.println(turbidity);

    Serial.print("TDS: ");
    Serial.println(tds);

    Serial.println("------------------------");

    Blynk.virtualWrite(V0, pH);
    Blynk.virtualWrite(V1, turbidity);
    Blynk.virtualWrite(V2, tds);

    int errorCode = 0;

    if (pH < ph_min || pH > ph_max)
    {
        errorCode = 4;
    }
    else if (turbidity > turb_max)
    {
        errorCode = 5;
    }
    else if (tds > tds_max)
    {
        errorCode = 3;
    }

    if (errorCode != 0)
    {
        Serial.println("Status: UNSAFE");
        Blynk.virtualWrite(V3, 1);

        if (errorCode != lastErrorCode ||
            (millis() - lastAudioTime > 10000))
        {
            if (errorCode != lastErrorCode)
            {
                player.play(1);
                delay(1200);
                player.play(2);
                delay(1500);
            }

            player.play(errorCode);
            lastAudioTime = millis();
        }
    }
    else
    {
        Serial.println("Status: SAFE");
        Blynk.virtualWrite(V3, 0);
    }

    lastErrorCode = errorCode;
}

void setup()
{
    Serial.begin(115200);

    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);

    dfSerial.begin(9600, SERIAL_8N1, DF_RX, DF_TX);

    if (!player.begin(dfSerial, true, false))
    {
        Serial.println("DFPlayer not detected. Check connections.");
    }

    player.volume(25);

    Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);

    Serial.println("System Starting...");

    timer.setInterval(5000L, sendData);
}

void loop()
{
    Blynk.run();
    timer.run();
}