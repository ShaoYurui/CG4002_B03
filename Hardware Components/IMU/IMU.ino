#include "Wire.h" // This library allows you to communicate with I2C devices.

////////////////////////////// IMU PRE_COMPILE DEFINES //////////////////////////////////////
#define MPU_ADDR              0x68
#define SEND_FREQ             50 // Hz
#define LOOP_TIME             ((1.0f / SEND_FREQ) * 1000) // ms
#define BAUD_RATE             115200
/////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////// IMU  PREPROCESS DEFINES///////////////////////////////////////
#define CALIBRATE_SAMPLE_NUM  200
#define ACCE_SCALE_FACTOR     1
#define GYRO_SCALE_FACTOR     1
#define IMU_ACCE_THRESHOLD    (5000/ACCE_SCALE_FACTOR)
#define IMU_GYRO_THRESHOLD    (5000/ACCE_SCALE_FACTOR)
/////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////// HANDSHAKE PRE_COMPILE DEFINES ////////////////////////////////
#define IMU_ACC               0x06
#define IMU_GYRO              0x16
#define PLAYER_ID             0x00 //0x00 or 0x01
#define PAD_BYTE              0x00
int message_id;
int checksum_acc, checksum_gyro;
unsigned long time ;

#define REQUEST_H             0x48
uint8_t ack_h[20] = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x40};
bool handshake_done = false;

/////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////// IMU RAW DATA VARIABLES //////////////////////////////////////
int16_t accelerometer_x, accelerometer_y, accelerometer_z; 
int16_t gyro_x, gyro_y, gyro_z; 
int16_t temperature; 
/////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////// IMU CALIBRATION VARIABLES ////////////////////////////////////
long accelerometer_x_cal, accelerometer_y_cal, accelerometer_z_cal; 
long gyro_x_cal, gyro_y_cal, gyro_z_cal; 
/////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////// IMU PREPROCESS VARIABLES /////////////////////////////////////
int16_t accelerometer_x_processed, accelerometer_y_processed, accelerometer_z_processed; 
int16_t gyro_x_processed, gyro_y_processed, gyro_z_processed; 
/////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////// MAIN FUNCTION/////////////////////////////////////////////////
void setup() 
{
  Serial.begin(BAUD_RATE);//initial the Serial
  setup_IMU();
  calibrate_IMU();
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
    float dummuy = 0;
    if(!is_movement_detected())
    {
      accelerometer_x_processed = 0;
      accelerometer_y_processed = 0;
      accelerometer_z_processed = 0;
      gyro_x_processed = 0;
      gyro_y_processed = 0;
      gyro_z_processed = 0;
    }
    time = millis();

    getChecksum(IMU_ACC);
    getChecksum(IMU_GYRO); 
    
    Serial.write (IMU_ACC);                                   //1
    Serial.write (message_id);                                //1
    Serial.write (PLAYER_ID);                                 //1
    Serial.write (time);                                       //4
    Serial.write (accelerometer_x_processed);                 //2
    Serial.write (accelerometer_y_processed);                 //2
    Serial.write (accelerometer_z_processed);                 //2
    Serial.write (gyro_x_processed);                          //2
    Serial.write (gyro_y_processed);                          //2
    Serial.write (gyro_z_processed);                          //2
    Serial.write (checksum_acc);                              //1

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
  delay(50);
  for(int i = 0; i < CALIBRATE_SAMPLE_NUM; i++)
  {
    read_IMU_data();
    accelerometer_x_cal += accelerometer_x;
    accelerometer_y_cal += accelerometer_y;
    accelerometer_z_cal += accelerometer_z;
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
  accelerometer_x_processed = 1.000f * (accelerometer_x - accelerometer_x_cal) / ACCE_SCALE_FACTOR;
  accelerometer_y_processed = 1.000f * (accelerometer_y - accelerometer_y_cal) / ACCE_SCALE_FACTOR;
  accelerometer_z_processed = 1.000f * (accelerometer_z - accelerometer_z_cal) / ACCE_SCALE_FACTOR;
  gyro_x_processed = 1.000f * (gyro_x - gyro_x_cal) / GYRO_SCALE_FACTOR;
  gyro_y_processed = 1.000f * (gyro_y - gyro_y_cal) / GYRO_SCALE_FACTOR;
  gyro_z_processed = 1.000f * (gyro_z - gyro_z_cal) / GYRO_SCALE_FACTOR;
}

bool is_movement_detected()
{
  
  if (
      (sqrt(accelerometer_x_processed * accelerometer_x_processed + 
            accelerometer_y_processed * accelerometer_y_processed +
            accelerometer_z_processed * accelerometer_z_processed) < IMU_ACCE_THRESHOLD) ||
      ((sqrt(gyro_x_processed * gyro_x_processed + 
            gyro_y_processed * gyro_y_processed +
            gyro_z_processed * gyro_z_processed) < IMU_GYRO_THRESHOLD)))
  {
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

void getChecksum(uint8_t message_type) {  
  uint8_t sum = 0;
  float temp;
  uint8_t* data;
    
  sum ^= message_type;
  sum ^= message_id;
  sum ^= PLAYER_ID;
  if (message_type == IMU_ACC) {
    temp = accelerometer_x_processed;
    data = ((uint8_t*) &temp);
    sum ^= data[0];
    sum ^= data[1];
    sum ^= data[2];
    sum ^= data[3];
    temp = accelerometer_y_processed;
    data = ((uint8_t*) &temp);
    sum ^= data[0];
    sum ^= data[1];
    sum ^= data[2];
    sum ^= data[3];
    temp = accelerometer_z_processed;
    data = ((uint8_t*) &temp);
    sum ^= data[0];
    sum ^= data[1];
    sum ^= data[2];
    sum ^= data[3];

    sum ^= time;

    checksum_acc = sum;
  } else if (message_type == IMU_GYRO) {
    temp = gyro_x_processed;
    data = ((uint8_t*) &temp);
    sum ^= data[0];
    sum ^= data[1];
    sum ^= data[2];
    sum ^= data[3];
    temp = gyro_y_processed;
    data = ((uint8_t*) &temp);
    sum ^= data[0];
    sum ^= data[1];
    sum ^= data[2];
    sum ^= data[3];
    temp = gyro_z_processed;
    data = ((uint8_t*) &temp);
    sum ^= data[0];
    sum ^= data[1];
    sum ^= data[2];
    sum ^= data[3];

    checksum_gyro = sum;
  }  
}
/////////////////////////////////////////////////////////////////////////////////////////////