#include <IRremote.h> // >v3.0.0
                                           
#define PIN_RECV 3
#define LED_PIN 2

#define PLAYER1_IR_SIGNAL_ADDRESS 0x1103
#define PLAYER1_IR_SIGNAL_COMMAND 0x96
#define BAUD_RATE 9600

void blinkLed() {
  digitalWrite(LED_PIN, HIGH);
  delay(1000);
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
  if (IrReceiver.decode()) {
    // Serial.println("Received something...");    
    // IrReceiver.printIRResultShort(&Serial); // Prints a summary of the received data
    // Serial.println(IrReceiver.decodedIRData.decodedRawData, HEX);
    if((IrReceiver.decodedIRData.address == PLAYER1_IR_SIGNAL_ADDRESS) && 
      (IrReceiver.decodedIRData.command == PLAYER1_IR_SIGNAL_COMMAND))
    {
       blinkLed();
    }
    IrReceiver.resume(); // Important, enables to receive the next IR signal
  }  
}  

