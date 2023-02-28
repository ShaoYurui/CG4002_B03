#include <IRremote.h> 

#define BUTTON_PIN 2                                      
#define SEND_PIN 3
#define BUZZER_PIN 4

#define PLAY1_IR_SIGNAL 0x96
#define PLAY1_IR_ADDRES 0x1103
#define BAUD_RATE 115200

#define GUN_DATA               0x04
#define PLAYER_ID              0x01 //0x01 or 0x02
#define PAD_BYTE               0x00
#define REQUEST_H              0x48

int ammo_count = 6;

int message_id = 0;
uint8_t ack_h[20] = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x30, 
                    0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x40};
bool handshake_done = false;

void setup()  
{  
  Serial.begin(BAUD_RATE);
  pinMode(BUTTON_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), button_isr, FALLING);
  IrSender.begin(SEND_PIN); // Initializes IR sender

  sound_reload();
}  
void loop()  
{  
  if (Serial.available()) 
  {
    if (Serial.read() == REQUEST_H) 
    {
      printHandshakeAck();
      handshake_done = true;
    }
  }
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

void reload()
{
  ammo_count = 6;
  sound_reload();
}

void sound_reload()
{
  for(int j=1000; j>100; j--)
  {
    digitalWrite(BUZZER_PIN, HIGH);
    delayMicroseconds(j);
    digitalWrite(BUZZER_PIN, LOW);
    delayMicroseconds(j);
  }
}

void rand_sound()
{
  for(int i=0; i<20; i++)
  {
    buzzer_tone(random(200,400));
  }
}

void buzzer_tone(int num)
{
  for(int i=0; i<10000/num; i++)
  {
    digitalWrite(BUZZER_PIN, HIGH);
    delayMicroseconds(num);
    digitalWrite(BUZZER_PIN, LOW);
    delayMicroseconds(num);
  }
}

void sound_space_gun()
{
  if (ammo_count <= 0)
  {
    ammo_count = 0;
    rand_sound();
    return ;
  }
  
  for (int i=0; i<(ammo_count+1)/2-1; i++)
  {
    for(int j=1000; j>900; j--)
    {
      digitalWrite(BUZZER_PIN, HIGH);
      delayMicroseconds(j);
      digitalWrite(BUZZER_PIN, LOW);
      delayMicroseconds(j);
    }
  }
  for(int j=200; j<900; j++)
  {
    digitalWrite(BUZZER_PIN, HIGH);
    delayMicroseconds(j);
    digitalWrite(BUZZER_PIN, LOW);
    delayMicroseconds(j);
  }
  ammo_count = ammo_count - 1;
}

void button_isr()
{
  disable_isr();
  shoot_IR();
  send_data();
  sound_space_gun(); 
  enable_isr();
}

void shoot_IR()
{
  if(ammo_count > 0)
  {
    IrSender.sendNEC(PLAY1_IR_ADDRES, PLAY1_IR_SIGNAL, true);  
  }
}

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
  package[0] = (uint8_t) GUN_DATA;

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
  sum ^= GUN_DATA;
  sum ^= message_id;
  sum ^= PLAYER_ID;

  return sum;
}
