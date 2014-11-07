#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_L3GD20_U.h>
#include <Adafruit_LSM303_U.h>

/* Assign a unique ID to this sensor at the same time */
Adafruit_L3GD20_Unified gyro = Adafruit_L3GD20_Unified(20);
Adafruit_LSM303_Accel_Unified accel = Adafruit_LSM303_Accel_Unified(54321);
Adafruit_LSM303_Mag_Unified mag = Adafruit_LSM303_Mag_Unified(12345);

// global variables
float gyroDriftX, gyroDriftY, gyroDriftZ;
float roll, pitch, yaw;
int n;

const float frequencyLoop = 5;
const float pi = 3.14159265F;
const float calibrationNo = 300;

/*******
HERE IS THE USUAL GYRO OFFSET:
X: need to +0.023926, +0.024486, +0.024373
Y: need to -0.002802, -0.003123, -0.003111
Z: need to -0.000289, -0.000897, -0.000445
*/


void displaySensorDetails(void)
{
  sensor_t sensor_gyro;
  gyro.getSensor(&sensor_gyro);
}

void setup(void) 
{
  roll = 0; pitch = 0; yaw = 0; n = 0;
  gyroDriftX = 0; gyroDriftY = 0; gyroDriftZ = 0; 
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
  
  /* Display some basic information on all sensors */
  displaySensorDetails();
}

void loop(void) 
{
  // Get a new sensor event 
  sensors_event_t event_gyro; 
  gyro.getEvent(&event_gyro);
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
    if(roll > 180){
      roll = -180;
    }
    else if (roll < -180){
      roll = 180;
    }
    else{
      roll += (event_gyro.gyro.x + gyroDriftX) * 1/frequencyLoop * 180 / pi;
    }
    
    if(roll > 180){
      roll = -180;
    }
    else if (roll < -180){
      roll = 180;
    }
    else{
      pitch += (event_gyro.gyro.y + gyroDriftY) * 1/frequencyLoop * 180 / pi;
    }
    
    if(roll > 180){
      roll = -180;
    }
    else if (roll < -180){
      roll = 180;
    }
    else{
      yaw += (event_gyro.gyro.z + gyroDriftZ) * 1/frequencyLoop * 180 / pi;
    }
    
    Serial.print(F("Orientation: "));
    Serial.print(roll);
    Serial.print(F(" "));
    Serial.print(pitch);
    Serial.print(F(" "));
    Serial.print(yaw);
    Serial.println(F(""));
    delay(100);
  }
}
