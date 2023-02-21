#include <FastLED.h>

#define LED_PIN     6
#define LED_POWER   8
#define NUM_LEDS    7

CRGB leds[NUM_LEDS];

void setup() 
{
  health_bar_setup();
  
}

void loop() 
{ 
  health_bar_blink();
  health_bar_display(10);
  delay(1500);
  // for(int i=100; i>=0; i-=10)
  // {
  //   health_bar_blink();
  //   health_bar_display(i);
  //   delay(1500);
  // }
}

void health_bar_setup()
{
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  pinMode(LED_POWER, OUTPUT);
  digitalWrite(LED_POWER, HIGH);
}

void health_bar_blink()
{
  for (int i=0; i<3; i++)
  {
    for(int j=0;j<NUM_LEDS;j++)
    {
      leds[j] = CRGB(255,0,0);
    }
    FastLED.show();
    delay(50);
    for(int j=0; j<NUM_LEDS; j++)
    {
      leds[j] = CRGB(0,0,0);
    }
    FastLED.show();
    delay(50);
  }
}

void health_bar_display(int hp)
{
  int num_led_up = 1.0f * hp / 100 * NUM_LEDS + 1;
  int green_value = 1.0f * hp / 100 * 255;
  int red_value = 1.0f * (100 - hp) / 100 * 255;
  for(int i=0; i<num_led_up; i++)
  {
    leds[i] = CRGB(red_value,green_value,0);
  }
  for(int i=num_led_up; i<NUM_LEDS; i++)
  {
    leds[i] = CRGB(0,0,0);
  }
  FastLED.show();
}