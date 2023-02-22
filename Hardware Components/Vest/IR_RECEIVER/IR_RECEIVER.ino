#include <IRremote.h> // >v3.0.0
#include <FastLED.h>
/////////////////////////////////// SERIAL DEFINES //////////////////////////////////////////                                      
#define BAUD_RATE                   115200
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// LED STRIPS DEFINES //////////////////////////////////////                                      
#define PIN_RECV                    3
#define LED_POWER                   A0
#define LED_PIN                     2
#define NUM_LEDS                    7
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// IR SIGNAL DEFINES ///////////////////////////////////////                                      
#define PLAYER1_IR_SIGNAL_ADDRESS   0x1103
#define PLAYER1_IR_SIGNAL_COMMAND   0x96
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// GAME STATUS VARIABELS ///////////////////////////////////                                      
int health_pt = 100;
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// LED STRIPS VARIABELS ////////////////////////////////////                                    
CRGB leds[NUM_LEDS];
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// MAIN FUNCTION////////////////////////////////////////////
void setup()  
{  
  Serial.begin(BAUD_RATE); //initialize serial connection to print on the Serial Monitor of the Arduino IDE
  IrReceiver.begin(PIN_RECV); // Initializes the IR receiver object
  health_bar_setup();
  pinMode(LED_PIN, OUTPUT);
}  
                               
void loop()  
{  
  if (IrReceiver.decode()) {
    if((IrReceiver.decodedIRData.address == PLAYER1_IR_SIGNAL_ADDRESS) && 
      (IrReceiver.decodedIRData.command == PLAYER1_IR_SIGNAL_COMMAND))
    {
      health_bar_blink();
      health_pt -= 10; 
    }
    IrReceiver.resume(); // Important, enables to receive the next IR signal
  }  
  health_bar_display(health_pt);
}  
/////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////// LED STRIPS FUNTIONS DEFINES/////////////////////////////

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
  hp = get_processed_hp(hp);

  int num_led_up = 1.0f * hp / 100 * NUM_LEDS;
  int red_value =  1.0f * (100 - hp) / 100 * 255;
  int green_value = 1.0f * hp / 100 * 255;
  
  if(hp == 10)
  {
    led_strips_display(1,255,0,0);
    return;
  }
  if(hp == 0)
  {
    led_strips_display(NUM_LEDS,255,0,0);
    return;
  }
  led_strips_display(num_led_up,red_value,green_value,0);
}

int get_processed_hp(int hp)
{
  if(hp < 0)
  {
    return 0;
  }
  return (hp / 10 * 10);
}

void led_strips_display(int num, int R, int G, int B)
{
  for(int i=0; i<num; i++)
  {
    leds[i] = CRGB(R,G,B);
  }
  for(int i=num; i<NUM_LEDS; i++)
  {
    leds[i] = CRGB(R,G,B);
  }
  FastLED.show();
}
/////////////////////////////////////////////////////////////////////////////////////////////

