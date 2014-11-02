#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_L3GD20_U.h>
#include <Adafruit_LSM303_U.h>

/* Assign a unique ID to this sensor at the same time */
Adafruit_L3GD20_Unified gyro = Adafruit_L3GD20_Unified(20);
Adafruit_LSM303_Accel_Unified accel = Adafruit_LSM303_Accel_Unified(54321);
Adafruit_LSM303_Mag_Unified mag = Adafruit_LSM303_Mag_Unified(12345);

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

void setup(void) 
{
  Serial.begin(115200);
  // -------- GYROSCOPE TEST -----------
  Serial.println("Gyroscope Test"); Serial.println("");
  
  /* Enable auto-ranging */
  gyro.enableAutoRange(true);
  
  /* Initialise the sensor */
  if(!gyro.begin())
  {
    /* There was a problem detecting the L3GD20 ... check your connections */
    Serial.println("Ooops, no L3GD20 detected ... Check your wiring!");
    while(1);
  }
  
  // ------- ACCELEROMETER TEST ---------
  Serial.println("Accelerometer Test"); Serial.println("");
  
  /* Initialise the sensor */
  if(!accel.begin())
  {
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
  
  /* Display some basic information on all sensors */
  displaySensorDetails();
}

void loop(void) 
{
  /* Get a new sensor event */ 
  sensors_event_t event_gyro; 
  gyro.getEvent(&event_gyro);
  sensors_event_t event_accel; 
  accel.getEvent(&event_accel);
  sensors_event_t event_mag; 
  mag.getEvent(&event_mag);
 
  /* Display the results (speed is measured in rad/s) */
  Serial.print("Xgyro: "); Serial.print(event_gyro.gyro.x,4); Serial.print("  ");
  Serial.print("Ygyro: "); Serial.print(event_gyro.gyro.y,4); Serial.print("  ");
  Serial.print("Zgyro: "); Serial.print(event_gyro.gyro.z,4); Serial.print("  ");
  Serial.println("rad/s ");
  delay(500);
  
  /* Display the results (acceleration is measured in m/s^2) */
  Serial.print("X: "); Serial.print(event_accel.acceleration.x); Serial.print("  ");
  Serial.print("Y: "); Serial.print(event_accel.acceleration.y); Serial.print("  ");
  Serial.print("Z: "); Serial.print(event_accel.acceleration.z); Serial.print("  ");Serial.println("m/s^2 ");
  delay(500);
  
  /* Display the results (magnetic vector values are in micro-Tesla (uT)) */
  Serial.print("Xmag: "); Serial.print(event_mag.magnetic.x); Serial.print("  ");
  Serial.print("Ymag: "); Serial.print(event_mag.magnetic.y); Serial.print("  ");
  Serial.print("Zmag: "); Serial.print(event_mag.magnetic.z); Serial.print("  ");Serial.println("uT");
  delay(500);
}
