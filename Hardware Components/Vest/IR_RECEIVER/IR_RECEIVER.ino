#include <IRremote.h> // >v3.0.0
                                           
#define PIN_RECV 3
#define LED_PIN 2

#define PLAYER1_IR_SIGNAL_ADDRESS 0x1103
#define PLAYER1_IR_SIGNAL_COMMAND 0x96
#define BAUD_RATE 115200

#define VEST_DATA               0x05
#define PLAYER_ID              0x01 //0x01 or 0x02
#define PAD_BYTE               0x00
#define REQUEST_H              0x48

int health_pt = 100;

int message_id = 0;
uint8_t ack_h[20] = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x30, 
                    0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x40};
bool handshake_done = false;

void blinkLed(int time) 
{
  digitalWrite(LED_PIN, HIGH);
  delay(500 - 5 * time);
  digitalWrite(LED_PIN, LOW);
  delay(time * 5);
}

void flashLED()
{
  for(int i=0;i<5;i++)
  {
    digitalWrite(LED_PIN, LOW);
    delay(50);
    digitalWrite(LED_PIN, HIGH);
    delay(50);
  }
  digitalWrite(LED_PIN, LOW);
}

void setup()  
{  
  Serial.begin(BAUD_RATE); //initialize serial connection to print on the Serial Monitor of the Arduino IDE
  IrReceiver.begin(PIN_RECV); // Initializes the IR receiver object
  pinMode(LED_PIN, OUTPUT);
}  
                               
void loop()  
{  
  if (Serial.available()) {
    if (Serial.read() == REQUEST_H) {
      printHandshakeAck();
      handshake_done = true;
    }
  }
  
  if (IrReceiver.decode()) {
    // Serial.println("Received something...");    
    // IrReceiver.printIRResultShort(&Serial); // Prints a summary of the received data
    // Serial.println(IrReceiver.decodedIRData.decodedRawData, HEX);
    if((IrReceiver.decodedIRData.address == PLAYER1_IR_SIGNAL_ADDRESS) && 
      (IrReceiver.decodedIRData.command == PLAYER1_IR_SIGNAL_COMMAND))
    {
      flashLED();
      send_data();
      health_pt -= 10; 
    }
    IrReceiver.resume(); // Important, enables to receive the next IR signal
  }  

  blinkLed(100-health_pt);
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
