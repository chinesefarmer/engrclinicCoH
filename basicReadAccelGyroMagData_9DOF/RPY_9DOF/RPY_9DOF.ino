#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_L3GD20_U.h>
#include <Adafruit_LSM303_U.h>

// Create sensor instances.
Adafruit_L3GD20_Unified gyro = Adafruit_L3GD20_Unified(20);
Adafruit_LSM303_Accel_Unified accel = Adafruit_LSM303_Accel_Unified(54321);
Adafruit_LSM303_Mag_Unified mag = Adafruit_LSM303_Mag_Unified(12345);

// global variables
float gyroDriftX, gyroDriftY, gyroDriftZ, gX, gY, gZ;
float nextR, nextP, nextY, prevR, prevP, prevY;
float roll, pitch, yaw;
int n;
const float frequencyLoop = 5;
const float PI_F = 3.14159265F;
const float calibrationNo = 300;

void displaySensorDetails(void)
{
  sensor_t sensor_gyro;
  gyro.getSensor(&sensor_gyro);
  Serial.println("------------------------------------");
  Serial.print  ("Sensor:       "); Serial.println(sensor_gyro.name);
  Serial.print  ("Driver Ver:   "); Serial.println(sensor_gyro.version);
  Serial.print  ("Unique ID:    "); Serial.println(sensor_gyro.sensor_id);
  Serial.print  ("Max Value:    "); Serial.print(sensor_gyro.max_value); Serial.println(" rad/s");
  Serial.print  ("Min Value:    "); Serial.print(sensor_gyro.min_value); Serial.println(" rad/s");
  Serial.print  ("Resolution:   "); Serial.print(sensor_gyro.resolution); Serial.println(" rad/s");  
  Serial.println("------------------------------------");
  Serial.println("");
  delay(500);
  sensor_t sensor_accel;
  accel.getSensor(&sensor_accel);
  Serial.println("------------------------------------");
  Serial.print  ("Sensor:       "); Serial.println(sensor_accel.name);
  Serial.print  ("Driver Ver:   "); Serial.println(sensor_accel.version);
  Serial.print  ("Unique ID:    "); Serial.println(sensor_accel.sensor_id);
  Serial.print  ("Max Value:    "); Serial.print(sensor_accel.max_value); Serial.println(" m/s^2");
  Serial.print  ("Min Value:    "); Serial.print(sensor_accel.min_value); Serial.println(" m/s^2");
  Serial.print  ("Resolution:   "); Serial.print(sensor_accel.resolution); Serial.println(" m/s^2");  
  Serial.println("------------------------------------");
  Serial.println("");
  delay(500);
  sensor_t sensor_mag;
  mag.getSensor(&sensor_mag);
  Serial.println("------------------------------------");
  Serial.print  ("Sensor:       "); Serial.println(sensor_mag.name);
  Serial.print  ("Driver Ver:   "); Serial.println(sensor_mag.version);
  Serial.print  ("Unique ID:    "); Serial.println(sensor_mag.sensor_id);
  Serial.print  ("Max Value:    "); Serial.print(sensor_mag.max_value); Serial.println(" uT");
  Serial.print  ("Min Value:    "); Serial.print(sensor_mag.min_value); Serial.println(" uT");
  Serial.print  ("Resolution:   "); Serial.print(sensor_mag.resolution); Serial.println(" uT");  
  Serial.println("------------------------------------");
  Serial.println("");
  delay(500);
}

void setup()
{
  roll = 0; pitch = 0; yaw = 0; n = 0;
  nextR = 0; nextP = 0; nextY = 0; prevR = 0; prevP = 0; prevY = 0;
  gyroDriftX = 0; gyroDriftY = 0; gyroDriftZ = 0; 
  Serial.begin(115200);
  
  // -------- GYROSCOPE TEST -----------
  Serial.println("Gyroscope Test"); Serial.println("");
   /* Enable auto-ranging */
  gyro.enableAutoRange(true);
  /* Initialise the sensor */
  if(!gyro.begin()){
    /* There was a problem detecting the L3GD20 ... check your connections */
    Serial.println("Ooops, no L3GD20 detected ... Check your wiring!");
    while(1);
  }
  
  // ------- ACCELEROMETER TEST ---------
  Serial.println("Accelerometer Test"); Serial.println("");
  /* Initialise the sensor */
  if(!accel.begin()){
    /* There was a problem detecting the ADXL345 ... check your connections */
    Serial.println("Ooops, no LSM303 detected ... Check your wiring!");
    while(1);
  }
  
  // ------- MAGNETOMETER TEST ----------
  Serial.println("Magnetometer Test"); Serial.println("");
  /* Enable auto-gain */
  mag.enableAutoRange(true);
  /* Initialise the sensor */
  if(!mag.begin())
  {
    /* There was a problem detecting the LSM303 ... check your connections */
    Serial.println("Ooops, no LSM303 detected ... Check your wiring!");
    while(1);
  }
 // Basic info for sensors
  displaySensorDetails();
}

void loop(void)
{
  sensors_event_t event_gyro; 
  gyro.getEvent(&event_gyro);
  sensors_event_t accel_event; 
  accel.getEvent(&accel_event);
  sensors_event_t mag_event; 
  mag.getEvent(&mag_event);
  
  if (n < 5){
    n++;
    delay(10);
  }
  else if(n < calibrationNo){
    Serial.println("Loop1");
    n++;
    gyroDriftX += -1*event_gyro.gyro.x;
    gyroDriftY += -1*event_gyro.gyro.y;
    gyroDriftZ += -1*event_gyro.gyro.z;
    delay(10);
  }
  
  
  else if (n == calibrationNo){
    Serial.println("Loop2");
    n++;
    gyroDriftX /= calibrationNo;
    gyroDriftY /= calibrationNo;
    gyroDriftZ /= calibrationNo;
    delay(10);
  }
  else{

  // roll: Rotation around the X-axis. -180 <= roll <= 180                                          
  // a positive roll angle is defined to be a clockwise rotation about the positive X-axis          
  //                                                                                                
  //                    y                                                                           
  //      roll = atan2(---)                                                                         
  //                    z                                                                           
  //                                                                                                
  // where:  y, z are returned value from accelerometer sensor                                      
  roll = (float)atan2(accel_event.acceleration.y, accel_event.acceleration.z);

  // pitch: Rotation around the Y-axis. -180 <= roll <= 180                                         
  // a positive pitch angle is defined to be a clockwise rotation about the positive Y-axis         
  //                                                                                                
  //                                 -x                                                             
  //      pitch = atan(-------------------------------)                                             
  //                    y * sin(roll) + z * cos(roll)                                               
  //                                                                                                
  // where:  x, y, z are returned value from accelerometer sensor                                   
  if (accel_event.acceleration.y * sin(roll) + accel_event.acceleration.z * cos(roll) == 0)
    pitch = accel_event.acceleration.x > 0 ? (PI_F / 2) : (-PI_F / 2);
  else
    pitch = (float)atan(-accel_event.acceleration.x / (accel_event.acceleration.y * sin(roll) + \
                                                                     accel_event.acceleration.z * cos(roll)));

  // heading: Rotation around the Z-axis. -180 <= roll <= 180                                       
  // a positive heading angle is defined to be a clockwise rotation about the positive Z-axis       
  //                                                                                                
  //                                       z * sin(roll) - y * cos(roll)                            
  //   heading = atan2(--------------------------------------------------------------------------)  
  //                    x * cos(pitch) + y * sin(pitch) * sin(roll) + z * sin(pitch) * cos(roll))   
  //                                                                                                
  // where:  x, y, z are returned value from magnetometer sensor                                    
  yaw = (float)atan2(mag_event.magnetic.z * sin(roll) - mag_event.magnetic.y * cos(roll), \
                                      mag_event.magnetic.x * cos(pitch) + \
                                      mag_event.magnetic.y * sin(pitch) * sin(roll) + \
                                      mag_event.magnetic.z * sin(pitch) * cos(roll));
 
  gX = abs(event_gyro.gyro.x + gyroDriftX);
  gY = abs(event_gyro.gyro.y + gyroDriftY);
  gZ = abs(event_gyro.gyro.z + gyroDriftZ);
  
  prevR = nextR;
  prevP = nextP;
  prevY = nextY;
  
  nextR = (prevR + roll * gX) / (1 + gX);
  nextP = (prevP + pitch * gY) / (1 + gY);
  nextY = (prevY + yaw * gZ) / (1+gZ); 


  // Use the simple AHRS function to get the current orientation.
  if (true)
  {
    /* 'orientation' should have valid .roll and .pitch fields */
    Serial.print(F("Orientation: "));
    Serial.print(nextR*180/PI_F);
    Serial.print(F(" "));
    Serial.print(-1*nextP*180/PI_F);
    Serial.print(F(" "));
    Serial.print(nextY*180/PI_F);
    Serial.println(F(""));
  }
  
  delay(10);
  }
}


