#include "Wire.h" // This library allows you to communicate with I2C devices.

////////////////////////////// IMU PRE_COMPILE DEFINES //////////////////////////////////////
#define MPU_ADDR              0x68
#define SEND_FREQ             50 // Hz
#define LOOP_TIME             ((1.0f / SEND_FREQ) * 1000) // ms
#define BAUD_RATE             115200
/////////////////////////////////////////////////////////////////////////////////////////////
#define LED_GND               3
#define LED_PIN               4
////////////////////////////// IMU  PREPROCESS DEFINES///////////////////////////////////////
#define GRAVITY_RAW_READING   16384
#define CALIBRATE_SAMPLE_NUM  1000
#define IMU_AG_SCALE_FACTOR   1000
#define IMU_AG_SUM_THRESHOLD  500
#define IMU_AG_PROD_THRESHOLD 1000
#define IMU_NO_MOVE_THRESHOLD 50
/////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////// HANDSHAKE PRE_COMPILE DEFINES ////////////////////////////////
#define IMU_DATA               0x06
#define PLAYER_ID              0x02 //0x01 or 0x02
#define PAD_BYTE               0x00
#define REQUEST_H              0x48
/////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////// HANDSHAKE PRE_COMPILE VARIABELS //////////////////////////////
int message_id = 0;
uint8_t ack_h[20] = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x30, 
                    0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x40};
bool handshake_done = false;
uint8_t package[20];
/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////// IMU RAW DATA VARIABLES //////////////////////////////////////
int16_t accelerometer_x, accelerometer_y, accelerometer_z; 
int16_t gyro_x, gyro_y, gyro_z; 
int16_t temperature; 
/////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////// IMU CALIBRATION VARIABLES ////////////////////////////////////
long accelerometer_x_cal, accelerometer_y_cal, accelerometer_z_cal; 
long gyro_x_cal, gyro_y_cal, gyro_z_cal; 
float accelerometer_x_scaled, accelerometer_y_scaled, accelerometer_z_scaled; 
float gyro_x_scaled, gyro_y_scaled, gyro_z_scaled;
int no_movement_count = IMU_NO_MOVE_THRESHOLD;
/////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////// IMU PREPROCESS VARIABLES /////////////////////////////////////
int16_t accelerometer_x_processed, accelerometer_y_processed, accelerometer_z_processed; 
int16_t gyro_x_processed, gyro_y_processed, gyro_z_processed;
unsigned long imu_time ; 
/////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////// MAIN FUNCTION/////////////////////////////////////////////////
void setup() 
{
  Serial.begin(BAUD_RATE);//initial the Serial
  pinMode(LED_GND,OUTPUT);
  pinMode(LED_PIN,OUTPUT);
  digitalWrite(LED_GND,LOW);
  digitalWrite(LED_PIN,HIGH);
  setup_IMU();
  calibrate_IMU();
  digitalWrite(LED_PIN,LOW);
}

void loop()
{
  if (!handshake_done) {
    if (Serial.available()) {
      if (Serial.read() == REQUEST_H) {
        printHandshakeAck();
        handshake_done = true;
      }
    }
  }
  
  if(handshake_done)
  { 
    read_IMU_data();
    preprocess_IMU_data();

    if(!is_movement_detected())
    {
      accelerometer_x_processed = 0;
      accelerometer_y_processed = 0;
      accelerometer_z_processed = 0;
      gyro_x_processed = 0;
      gyro_y_processed = 0;
      gyro_z_processed = 0;
    }

    imu_time = millis();
    
    package[19] = (uint8_t) getChecksum();
    package[18] = ((uint8_t *) &gyro_z_processed) [0];
    package[17] = ((uint8_t *) &gyro_z_processed) [1];
    package[16] = ((uint8_t *) &gyro_y_processed) [0];
    package[15] = ((uint8_t *) &gyro_y_processed) [1];
    package[14] = ((uint8_t *) &gyro_x_processed) [0];
    package[13] = ((uint8_t *) &gyro_x_processed) [1];
    package[12] = ((uint8_t *) &accelerometer_z_processed) [0];
    package[11] = ((uint8_t *) &accelerometer_z_processed) [1];
    package[10] = ((uint8_t *) &accelerometer_y_processed) [0];
    package[9] = ((uint8_t *) &accelerometer_y_processed) [1];
    package[8] = ((uint8_t *) &accelerometer_x_processed) [0];
    package[7] = ((uint8_t *) &accelerometer_x_processed) [1];
    package[6] = ((uint8_t *) &imu_time) [0];
    package[5] = ((uint8_t *) &imu_time) [1];
    package[4] = ((uint8_t *) &imu_time) [2];
    package[3] = ((uint8_t *) &imu_time) [3];
    package[2] = (uint8_t) PLAYER_ID;
    package[1] = (uint8_t) message_id;
    package[0] = (uint8_t) IMU_DATA;

    Serial.write (package, 20);                              
    message_id++;
    delay(LOOP_TIME);
  }
  
}
/////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////// IMU FUNTIONS DEFINES//////////////////////////////////////////
void setup_IMU()
{
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR); // Begins a transmission to the I2C slave (GY-521 board)
  Wire.write(0x6B); // PWR_MGMT_1 register
  Wire.write(0); // set to zero (wakes up the MPU-6050)
  Wire.endTransmission(true);
}

void read_IMU_data()
{
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B); // starting with register 0x3B (ACCEL_XOUT_H) [MPU-6000 and MPU-6050 Register Map and Descriptions Revision 4.2, p.40]
  Wire.endTransmission(false); // the parameter indicates that the Arduino will send a restart. As a result, the connection is kept active.
  Wire.requestFrom(MPU_ADDR, 7*2, true); // request a total of 7*2=14 registers

  // "Wire.read()<<8 | Wire.read();" means two registers are read and stored in the same variable
  accelerometer_x = Wire.read()<<8 | Wire.read(); // reading registers: 0x3B (ACCEL_XOUT_H) and 0x3C (ACCEL_XOUT_L)
  accelerometer_y = Wire.read()<<8 | Wire.read(); // reading registers: 0x3D (ACCEL_YOUT_H) and 0x3E (ACCEL_YOUT_L)
  accelerometer_z = Wire.read()<<8 | Wire.read(); // reading registers: 0x3F (ACCEL_ZOUT_H) and 0x40 (ACCEL_ZOUT_L)
  temperature = Wire.read()<<8 | Wire.read(); // reading registers: 0x41 (TEMP_OUT_H) and 0x42 (TEMP_OUT_L)
  gyro_x = Wire.read()<<8 | Wire.read(); // reading registers: 0x43 (GYRO_XOUT_H) and 0x44 (GYRO_XOUT_L)
  gyro_y = Wire.read()<<8 | Wire.read(); // reading registers: 0x45 (GYRO_YOUT_H) and 0x46 (GYRO_YOUT_L)
  gyro_z = Wire.read()<<8 | Wire.read(); // reading registers: 0x47 (GYRO_ZOUT_H) and 0x48 (GYRO_ZOUT_L)
}

void calibrate_IMU()
{
  reset_cal_bias();
  delay(100);
  for(int i = 0; i < CALIBRATE_SAMPLE_NUM; i++)
  {
    read_IMU_data();
    accelerometer_x_cal += accelerometer_x;
    accelerometer_y_cal += accelerometer_y;
    accelerometer_z_cal += (accelerometer_z + GRAVITY_RAW_READING);
    gyro_x_cal += gyro_x;
    gyro_y_cal += gyro_y;
    gyro_z_cal += gyro_z; 
    delay(10);
  }
  accelerometer_x_cal /= CALIBRATE_SAMPLE_NUM;
  accelerometer_y_cal /= CALIBRATE_SAMPLE_NUM;
  accelerometer_z_cal /= CALIBRATE_SAMPLE_NUM;
  gyro_x_cal /= CALIBRATE_SAMPLE_NUM;
  gyro_y_cal /= CALIBRATE_SAMPLE_NUM;
  gyro_z_cal /= CALIBRATE_SAMPLE_NUM; 
}

void reset_cal_bias()
{
  accelerometer_x_cal = 0;
  accelerometer_y_cal = 0;
  accelerometer_z_cal = 0;
  gyro_x_cal = 0;
  gyro_y_cal = 0;
  gyro_z_cal = 0; 
}

void preprocess_IMU_data()
{
  accelerometer_x_processed = (accelerometer_x - accelerometer_x_cal) ;
  accelerometer_y_processed = (accelerometer_y - accelerometer_y_cal) ;
  accelerometer_z_processed = (accelerometer_z - accelerometer_z_cal) ;
  gyro_x_processed = (gyro_x - gyro_x_cal) ;
  gyro_y_processed = (gyro_y - gyro_y_cal) ;
  gyro_z_processed = (gyro_z - gyro_z_cal) ;
}

void scale_IMU_data()
{
  accelerometer_x_scaled = 1.0f * accelerometer_x_processed / IMU_AG_SCALE_FACTOR;
  accelerometer_y_scaled = 1.0f * accelerometer_y_processed / IMU_AG_SCALE_FACTOR;
  accelerometer_z_scaled = 1.0f * accelerometer_z_processed / IMU_AG_SCALE_FACTOR;
  gyro_x_scaled = 1.0f * gyro_x_processed / IMU_AG_SCALE_FACTOR;
  gyro_y_scaled = 1.0f * gyro_y_processed / IMU_AG_SCALE_FACTOR;
  gyro_z_scaled = 1.0f * gyro_z_processed / IMU_AG_SCALE_FACTOR;
}

bool is_movement_detected()
{
  scale_IMU_data();
  float acc_sqrt = 1.0f * sqrt(accelerometer_x_scaled * accelerometer_x_scaled + 
                        accelerometer_y_scaled * accelerometer_y_scaled +
                        accelerometer_z_scaled * accelerometer_z_scaled);

  float gyro_sqrt = 1.0f * sqrt(gyro_x_scaled * gyro_x_scaled + 
                          gyro_y_scaled * gyro_y_scaled +
                          gyro_z_scaled * gyro_z_scaled);
  
  long acc_prod = sqrt(accelerometer_x_scaled * accelerometer_x_scaled) *
                  sqrt(accelerometer_y_scaled * accelerometer_y_scaled) * 
                  sqrt(accelerometer_z_scaled * accelerometer_z_scaled);

  long gyro_prod = sqrt(gyro_x_scaled * gyro_x_scaled) *
                    sqrt(gyro_y_scaled * gyro_y_scaled) * 
                    sqrt(gyro_z_scaled * gyro_z_scaled);     

  if (( acc_sqrt * gyro_sqrt > IMU_AG_SUM_THRESHOLD) && (acc_prod > IMU_AG_PROD_THRESHOLD || gyro_prod > IMU_AG_PROD_THRESHOLD))
  {
    no_movement_count = 0;
    return true;
  }

  if (( acc_sqrt * gyro_sqrt > IMU_AG_SUM_THRESHOLD/4) && (acc_prod > IMU_AG_PROD_THRESHOLD/4 || gyro_prod > IMU_AG_PROD_THRESHOLD/4))
  {
    no_movement_count++;
  }
  else
  {
    no_movement_count = no_movement_count + 2;
  }
  
  if(no_movement_count >= IMU_NO_MOVE_THRESHOLD)
  {
    no_movement_count = IMU_NO_MOVE_THRESHOLD;
    return false;
  }

  return true;
}

void print_IMU_raw_data()
{
  Serial.print(accelerometer_x); Serial.print(" "); 
  Serial.print(accelerometer_y); Serial.print(" "); 
  Serial.print(accelerometer_z); Serial.print(" "); 
  Serial.print(gyro_x); Serial.print(" "); 
  Serial.print(gyro_y); Serial.print(" "); 
  Serial.print(gyro_z); Serial.println(" "); 
}

void print_IMU_cal_data()
{
  Serial.print(accelerometer_x_cal); Serial.print(" "); 
  Serial.print(accelerometer_y_cal); Serial.print(" "); 
  Serial.print(accelerometer_z_cal); Serial.print(" "); 
  Serial.print(gyro_x_cal); Serial.print(" "); 
  Serial.print(gyro_y_cal); Serial.print(" "); 
  Serial.print(gyro_z_cal); Serial.println(" "); 
}

void print_IMU_processed_data()
{
  Serial.print(accelerometer_x_processed); Serial.print(" "); 
  Serial.print(accelerometer_y_processed); Serial.print(" "); 
  Serial.print(accelerometer_z_processed); Serial.print(" "); 
  Serial.print(gyro_x_processed); Serial.print(" "); 
  Serial.print(gyro_y_processed); Serial.print(" "); 
  Serial.print(gyro_z_processed); Serial.println(" "); 
}

void printHandshakeAck() {
  for (int i = 0; i < 20; i++) {
    Serial.write(ack_h[i]);
  }
}

uint8_t getChecksum() {  
  uint8_t sum = 0;
  uint8_t* data;
    
  sum ^= IMU_DATA;
  sum ^= message_id;
  sum ^= PLAYER_ID;

  data = ((uint8_t*) &imu_time);
  sum ^= data[0];
  sum ^= data[1];
  sum ^= data[2];
  sum ^= data[3];

  data = ((uint8_t*) &accelerometer_x_processed);
  sum ^= data[0];
  sum ^= data[1];

  data = ((uint8_t*) &accelerometer_y_processed);
  sum ^= data[0];
  sum ^= data[1];

  data = ((uint8_t*) &accelerometer_z_processed);
  sum ^= data[0];
  sum ^= data[1];

  data = ((uint8_t*) &gyro_x_processed);
  sum ^= data[0];
  sum ^= data[1];

  data = ((uint8_t*) &gyro_y_processed);
  sum ^= data[0];
  sum ^= data[1];

  data = ((uint8_t*) &gyro_z_processed);
  sum ^= data[0];
  sum ^= data[1];

  return sum;
}
/////////////////////////////////////////////////////////////////////////////////////////////
