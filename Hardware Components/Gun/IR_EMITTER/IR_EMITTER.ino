#include <IRremote.h> 

#define BUTTON_PIN 2                                      
#define SEND_PIN 3
#define BUZZER_PIN 4

#define PLAY1_IR_SIGNAL 0x96
#define PLAY1_IR_ADDRES 0x1103
#define BAUD_RATE 9600

void setup()  
{  
  pinMode(BUTTON_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), button_isr, FALLING);
  IrSender.begin(SEND_PIN); // Initializes IR sender
}  
void loop()  
{  

}  

void disable_isr()
{
  EIMSK &= 0b00000010;
}

void enable_isr()
{
  EIFR = 0b00000001;
  EIMSK |= 0b00000001;
}

void sound_space_gun()
{
  for(int i=200;i<900;i++)
  {
    digitalWrite(BUZZER_PIN, HIGH);
    delayMicroseconds(i);
    digitalWrite(BUZZER_PIN, LOW);
    delayMicroseconds(i);
  }
}

void button_isr()
{
  disable_isr();
  shoot_IR();
  sound_space_gun();
  enable_isr();
}

void shoot_IR()
{
  IrSender.sendNEC(PLAY1_IR_ADDRES, PLAY1_IR_SIGNAL, true);
}


