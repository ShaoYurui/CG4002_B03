#include <IRremote.h> // >v3.0.0
#include <FastLED.h>
/////////////////////////////////// PLAYER DEFINES ////////////////////////////////////////// 
#define PLAYER_ID              0x02 //0x01 or 0x02
/////////////////////////////////// LED STRIPS DEFINES ////////////////////////////////////// 
/////////////////////////////////// SERIAL DEFINES //////////////////////////////////////////                                      
#define BAUD_RATE                   115200
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// LED STRIPS DEFINES //////////////////////////////////////                                      
#define PIN_RECV                    3
#define LED_POWER                   4
#define LED_PIN                     2
#define NUM_LEDS                    7
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// IR SIGNAL DEFINES ///////////////////////////////////////                                      
#define PLAYER1_IR_SIGNAL_ADDRESS   0x1103
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// GAME STATUS VARIABELS ///////////////////////////////////                                      
int health_pt = 10;
int shield_pt = 0;
int prev_health_pt = 0;
int prev_shield_pt = 0;
bool is_shield_activated = false;
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// LED STRIPS VARIABELS ////////////////////////////////////                                    
CRGB leds[NUM_LEDS];
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// COMMUNICATION DEFINES ///////////////////////////////////
#define VEST_DATA              0x05
#define PAD_BYTE               0x00
#define REQUEST_H              0x48
#if (PLAYER_ID==0x01)
#define SHOOTER_ID             0x02
#endif
#if (PLAYER_ID==0x02)
#define SHOOTER_ID             0x01
#endif
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// COMMUNICATION VARIABLES /////////////////////////////////
int message_id = 0;
uint8_t ack_h[20] = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x30, 
                    0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x40};
bool handshake_done = false;
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// MAIN FUNCTION////////////////////////////////////////////
void setup()  
{  
  Serial.begin(BAUD_RATE); //initialize serial connection to print on the Serial Monitor of the Arduino IDE
  IrReceiver.begin(PIN_RECV); // Initializes the IR receiver object
  health_bar_setup();
  pinMode(LED_PIN, OUTPUT);
  health_bar_display();
}  
                               
void loop()  
{  
  if (Serial.available()) 
  {
    uint8_t indata = Serial.read();
    if (indata == REQUEST_H) 
    {
      printHandshakeAck();
      handshake_done = true;
    } 
    else if (is_valid_data(indata))
    { //receive hp
      set_health_pt(indata);
      health_bar_display();
    }
  }

  if (IrReceiver.decode()) {
    if((IrReceiver.decodedIRData.address == PLAYER1_IR_SIGNAL_ADDRESS) && 
      (IrReceiver.decodedIRData.command == SHOOTER_ID))
    {
      send_data();
      health_bar_blink(1);
    }
    IrReceiver.resume(); // Important, enables to receive the next IR signal
  }  
}  
/////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////// LED STRIPS FUNTIONS DEFINES/////////////////////////////

void set_health_pt(uint8_t data)
{
  // 0 00 0000 0
  shield_pt = (data >> 5) & 0b011;
  health_pt = (data >> 1) & 0b0001111;

  is_shield_activated = false;
  if (shield_pt > 0)
  {
    is_shield_activated = true;
  }
}

bool is_valid_data(uint8_t data)
{
  if((data >> 7) == 1)
  {
    return true;
  }
  return false;
}

void health_bar_setup()
{
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  pinMode(LED_POWER, OUTPUT);
  digitalWrite(LED_POWER, HIGH);
}

void health_bar_blink(int n)
{
  for (int i=0; i<n; i++)
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

void shield_bar_display(int hp)
{
  led_strips_display(hp*2,0,0,255);
}

void health_bar_display()
{
  if ((prev_health_pt != health_pt) || (prev_shield_pt != shield_pt))
  {
    prev_health_pt = health_pt;
    prev_shield_pt = shield_pt;
    health_bar_blink(2);
  }
  else
  {
    return ;
  }
  if (is_shield_activated)
  {
    shield_bar_display(shield_pt);
    return;
  }
  int hp = get_processed_hp(health_pt);
  int num_led_up = 1.0f * hp / 10 * NUM_LEDS;
  int red_value =  1.0f * (10 - hp) / 10 * 255;
  int green_value = 1.0f * hp / 10 * 255;
  
  if(hp == 1)
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
  return hp;
}

void led_strips_display(int num, int R, int G, int B)
{
  for(int i=0; i<num; i++)
  {
    leds[i] = CRGB(R,G,B);
  }
  for(int i=num; i<NUM_LEDS; i++)
  {
    leds[i] = CRGB(0,0,0);
  }
  FastLED.show();
}
/////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////// COMMUNICATION FUNTIONS DEFINES//////////////////////////

void send_data() {
  uint8_t package[20];
  package[19] = (uint8_t) getChecksum();
  package[18] = (uint8_t) PAD_BYTE;
  package[17] = (uint8_t) PAD_BYTE;
  package[16] = (uint8_t) PAD_BYTE;
  package[15] = (uint8_t) PAD_BYTE;
  package[14] = (uint8_t) PAD_BYTE;
  package[13] = (uint8_t) PAD_BYTE;
  package[12] = (uint8_t) PAD_BYTE;
  package[11] = (uint8_t) PAD_BYTE;
  package[10] = (uint8_t) PAD_BYTE;
  package[9] = (uint8_t) PAD_BYTE;
  package[8] = (uint8_t) PAD_BYTE;
  package[7] = (uint8_t) PAD_BYTE;
  package[6] = (uint8_t) PAD_BYTE;
  package[5] = (uint8_t) PAD_BYTE;
  package[4] = (uint8_t) PAD_BYTE;
  package[3] = (uint8_t) PAD_BYTE;
  package[2] = (uint8_t) PLAYER_ID;
  package[1] = (uint8_t) message_id;
  package[0] = (uint8_t) VEST_DATA;

  Serial.write (package, 20);
  if (message_id == 0) {
    message_id = 1;
  } else {
    message_id = 0;
  }
}

void printHandshakeAck() {
  for (int i = 0; i < 20; i++) {
    Serial.write(ack_h[i]);
  }
}

uint8_t getChecksum() {
  uint8_t sum = 0;
  sum ^= VEST_DATA;
  sum ^= message_id;
  sum ^= PLAYER_ID;

  return sum;
}
/////////////////////////////////////////////////////////////////////////////////////////////
