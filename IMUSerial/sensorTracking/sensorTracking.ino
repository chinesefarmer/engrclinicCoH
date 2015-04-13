/* This code has been adapted to work on the Teensy(from working originally on an Arduino) to work with 
  both the blink sensor and the IMU to print out the sensor information to serial communication.
*/


/* SI1143_proximity_demo.ino
 * http://moderndevice.com/product/si1143-proximity-sensors/
 * Reads the Proximity Sensor and either prints raw LED data or angular data 
 * depending the options chosen in the #define's below
 * Paul Badger, Gavin Atkinson, Jean-Claude Wippler  2013
 */

//$ Comments mean that I commented out a normal print line for the purpose of interfacing with
//python.

/*  
  For Arduino users use the following pins for various ports of the proximity sensor
  **A4 = SDA Pin
  **A5 = SCL Pin
  Don't connect PWR or IRQ
  Connect SDA and SCL to 10k series resistor before connecting to A4 and A5
  Connect Ground.
  Connect 3.3V line to 3.3 volts.
*/

#include <SI114.h>

const int PORT_FOR_SI114 = 0;       // change to the JeeNode port number used, see the pin chart above        
const int samples = 4;            // samples for smoothing 1 to 10 seem useful increase for smoother waveform

// some printing options for experimentation (sketch is about the same)
#define SEND_TO_PROCESSING_SKETCH
#define PRINT_RAW_LED_VALUES           // prints Raw LED values for debug or experimenting
 
unsigned long IR1;
PortI2C myBus (PORT_FOR_SI114);
//pulse is of type PulsePlug, defined in header file
PulsePlug pulse (myBus); 


#include <SPI.h>
//#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_LSM9DS0.h>
// To get the arduino values: https://github.com/adafruit/Adafruit_LSM9DS0_Library

/* This driver uses the Adafruit unified sensor library (Adafruit_Sensor),
   which provides a common 'type' for sensor data and some helper functions.
   
   To use this driver you will also need to download the Adafruit_Sensor
   library and include it in your libraries folder.

   You should also assign a unique ID to this sensor for use with
   the Adafruit Sensor API so that you can identify this particular
   sensor in any data logs, etc.  To assign a unique ID, simply
   provide an appropriate value in the constructor below (12345
   is used by default in this example).
   
   Connections (For default I2C)
   ===========
   Connect SCL to analog 29
   Connect SDA to analog 30
   Connect VDD to 5V DC
   Connect GROUND to common ground

   History
   =======
   2014/JULY/25  - First version (KTOWN)
*/
   
/* Assign a unique base ID for this sensor */   
Adafruit_LSM9DS0 lsm = Adafruit_LSM9DS0(1000);  // Use I2C, ID #1000


/* Or, use Hardware SPI:
  SCK -> SPI CLK
  SDA -> SPI MOSI
  G_SDO + XM_SDO -> tied together to SPI MISO
  then select any two pins for the two CS lines:
*/

#define LSM9DS0_XM_CS 10
#define LSM9DS0_GYRO_CS 9
//Adafruit_LSM9DS0 lsm = Adafruit_LSM9DS0(LSM9DS0_XM_CS, LSM9DS0_GYRO_CS, 1000);

/* Or, use Software SPI:
  G_SDO + XM_SDO -> tied together to the MISO pin!
  then select any pins for the SPI lines, and the two CS pins above
*/

#define LSM9DS0_SCLK 13
#define LSM9DS0_MISO 12
#define LSM9DS0_MOSI 11

//Adafruit_LSM9DS0 lsm = Adafruit_LSM9DS0(LSM9DS0_SCLK, LSM9DS0_MISO, LSM9DS0_MOSI, LSM9DS0_XM_CS, LSM9DS0_GYRO_CS, 1000);


/**************************************************************************/
/*
    Displays some basic information on this sensor from the unified
    sensor API sensor_t type (see Adafruit_Sensor for more information)
*/
/**************************************************************************/
void displaySensorDetails(void)
{
  sensor_t accel, mag, gyro, temp;
  
  lsm.getSensor(&accel, &mag, &gyro, &temp);
  
  Serial.println(F("------------------------------------"));
  Serial.print  (F("Sensor:       ")); Serial.println(accel.name);
  Serial.print  (F("Driver Ver:   ")); Serial.println(accel.version);
  Serial.print  (F("Unique ID:    ")); Serial.println(accel.sensor_id);
  Serial.print  (F("Max Value:    ")); Serial.print(accel.max_value); Serial.println(F(" G"));
  Serial.print  (F("Min Value:    ")); Serial.print(accel.min_value); Serial.println(F(" G"));
  Serial.print  (F("Resolution:   ")); Serial.print(accel.resolution); Serial.println(F(" G"));  
  Serial.println(F("------------------------------------"));
  Serial.println(F(""));

  Serial.println(F("------------------------------------"));
  Serial.print  (F("Sensor:       ")); Serial.println(mag.name);
  Serial.print  (F("Driver Ver:   ")); Serial.println(mag.version);
  Serial.print  (F("Unique ID:    ")); Serial.println(mag.sensor_id);
  Serial.print  (F("Max Value:    ")); Serial.print(mag.max_value); Serial.println(F(" uT"));
  Serial.print  (F("Min Value:    ")); Serial.print(mag.min_value); Serial.println(F(" uT"));
  Serial.print  (F("Resolution:   ")); Serial.print(mag.resolution); Serial.println(F(" uT"));  
  Serial.println(F("------------------------------------"));
  Serial.println(F(""));

  Serial.println(F("------------------------------------"));
  Serial.print  (F("Sensor:       ")); Serial.println(gyro.name);
  Serial.print  (F("Driver Ver:   ")); Serial.println(gyro.version);
  Serial.print  (F("Unique ID:    ")); Serial.println(gyro.sensor_id);
  Serial.print  (F("Max Value:    ")); Serial.print(gyro.max_value); Serial.println(F(" rad/s"));
  Serial.print  (F("Min Value:    ")); Serial.print(gyro.min_value); Serial.println(F(" rad/s"));
  Serial.print  (F("Resolution:   ")); Serial.print(gyro.resolution); Serial.println(F(" rad/s"));  
  Serial.println(F("------------------------------------"));
  Serial.println(F(""));

  Serial.println(F("------------------------------------"));
  Serial.print  (F("Sensor:       ")); Serial.println(temp.name);
  Serial.print  (F("Driver Ver:   ")); Serial.println(temp.version);
  Serial.print  (F("Unique ID:    ")); Serial.println(temp.sensor_id);
  Serial.print  (F("Max Value:    ")); Serial.print(temp.max_value); Serial.println(F(" C"));
  Serial.print  (F("Min Value:    ")); Serial.print(temp.min_value); Serial.println(F(" C"));
  Serial.print  (F("Resolution:   ")); Serial.print(temp.resolution); Serial.println(F(" C"));  
  Serial.println(F("------------------------------------"));
  Serial.println(F(""));
  
  delay(500);
}

/**************************************************************************/
/*
    Configures the gain and integration time for the TSL2561
*/
/**************************************************************************/
void configureSensor(void)
{
  // 1.) Set the accelerometer range
  lsm.setupAccel(lsm.LSM9DS0_ACCELRANGE_2G);
  //lsm.setupAccel(lsm.LSM9DS0_ACCELRANGE_4G);
  //lsm.setupAccel(lsm.LSM9DS0_ACCELRANGE_6G);
  //lsm.setupAccel(lsm.LSM9DS0_ACCELRANGE_8G);
  //lsm.setupAccel(lsm.LSM9DS0_ACCELRANGE_16G);
  
  // 2.) Set the magnetometer sensitivity
  lsm.setupMag(lsm.LSM9DS0_MAGGAIN_2GAUSS);
  //lsm.setupMag(lsm.LSM9DS0_MAGGAIN_4GAUSS);
  //lsm.setupMag(lsm.LSM9DS0_MAGGAIN_8GAUSS);
  //lsm.setupMag(lsm.LSM9DS0_MAGGAIN_12GAUSS);

  // 3.) Setup the gyroscope
  lsm.setupGyro(lsm.LSM9DS0_GYROSCALE_245DPS);
  //lsm.setupGyro(lsm.LSM9DS0_GYROSCALE_500DPS);
  //lsm.setupGyro(lsm.LSM9DS0_GYROSCALE_2000DPS);
}

/**************************************************************************/
/*
    Arduino setup function (automatically called at startup)
*/
/**************************************************************************/
void setup(void) 
{
  Serial.println("Unconnected");                //TESTING
  while (!Serial);  // wait for flora/leonardo
  
  Serial.begin(57600);
  Serial.println(F("LSM9DS0 9DOF Sensor Test")); Serial.println("");
  
  /* Initialise the sensor */
  if(!lsm.begin())
  {
    /* There was a problem detecting the LSM9DS0 ... check your connections */
    Serial.print(F("Ooops, no LSM9DS0 detected ... Check your wiring or I2C ADDR!"));
    while(1);
  }
  
  Serial.println(F("Found LSM9DS0 9DOF"));
  
  /* Display some basic information on this sensor */
  //***not doing this because I don't want to have random text printed
  //displaySensorDetails();
  
  /* Setup the sensor gain and integration time */
  configureSensor();
  
  /* We're ready to go! */
  Serial.println("");
  
      //Enables the pull-up resistor
    digitalWrite(3, HIGH);
    //Write 0.17 to the HW_KEY register for proper operation in Initialization Mode
    pulse.setReg(PulsePlug::HW_KEY, 0x17);  
    
    /*
    MEAS_Rate is an 8-bit compressed value representing a 16-bit integer. The uncompressed
    16-bit value, when multiplied by 31.25microseconds, represents the time duration between
    wake-up periods where measurements are made.
    0x84: The device wakes up every 10 ms (0x140 x 31.25 microseconds)
    */
    pulse.setReg(PulsePlug::MEAS_RATE, 0x84);
    
    /*
    ALS_RATE is an 8-bit compressed value representing a 16-bit multiplier. This multiplier,
    in conjunction with the MEAS_RATE time, represents how often ALS measurements are made.
    0x08: ALS Measurements are made every time the device wakes up (0x0001 x timeValueOf(MEAS_RATE))
    */
    pulse.setReg(PulsePlug::ALS_RATE, 0x08);
    
    /*
    PS_RATE is an 8-bit compressed value representing a 16-bit multiplier. This multiplier, in
    conjuunction with the MEAS_RATE time, represents how often PS Measurements are made.
    0x08: PS Measurements made every time the device wakes up (0x0001 x timeValueOf(MEAS_RATE))
    */
    pulse.setReg(PulsePlug::PS_RATE, 0x08);

    //LEDs encoded as follows: 0000-No Current, 0001-Minimum Current, 1111-Maximum current
    //See Table 3 Performance Characteristics
    pulse.setReg(PulsePlug::PS_LED21, 0x66 );      // LED current for LEDs 1 (red) & 2 (IR1) during PS Measurement
    pulse.setReg(PulsePlug::PS_LED3, 0x06);       // LED current for LED 3 (IR2) during PS Measurement
    pulse.readParam(0x01);
    pulse.writeParam(PulsePlug::PARAM_CH_LIST, 0x77);         //?? datasheet don't make sense :(

    /*
    increasing PARAM_PS_ADC_GAIN will increase the LED on time and ADC window you will see increase in brightness
    of visible LED's, ADC output, & noise datasheet warns not to go beyond 4 because chip or LEDs may be damaged
    
    Nicole's Description: Increases the irLED pulse width and ADC integration time by a factor of
    (2 ^ PS_ADC_GAIN) for all PS Measurements. The irLEDs are configured for 359 mA, so don't enter value above 5
    0x00: ADC Clock is divided by 1
    */
    pulse.writeParam(PulsePlug::PARAM_PS_ADC_GAIN, 0x00);

    //Specified LED pin driven during PS1 and 2 Measurement. Unclear what value 0x21 is...
    pulse.writeParam(PulsePlug::PARAM_PSLED12_SELECT, 0x21);  // select LEDs on for readings see datasheet
    //Assuming LED3 drive enabled during PS3 Measurement
    pulse.writeParam(PulsePlug::PARAM_PSLED3_SELECT, 0x04);   //  3 only
    //0x03: Large IR Photodiode (PS_ADC_MODE = 1 (default)) <- not set so I'm assuming it's in default mode
    pulse.writeParam(PulsePlug::PARAM_PS1_ADCMUX, 0x03);      // Selects ADC Input for PS1 measurement (photodiode select)
    pulse.writeParam(PulsePlug::PARAM_PS2_ADCMUX, 0x03);      // Selects ADC Input for PS2 measurement (photodiode select)
    pulse.writeParam(PulsePlug::PARAM_PS3_ADCMUX, 0x03);      // Selects ADC Input for PS3 measurement (photodiode select)

    pulse.writeParam(PulsePlug::PARAM_PS_ADC_COUNTER, B01110000);    // B01110000 is default   
    //Autonomous Operation Mode, measurements performed automatically w/o requiring explicit host command for
    //every measurement.    
    pulse.setReg(PulsePlug::COMMAND, PulsePlug::PSALS_AUTO_Cmd);     // starts an autonomous read loop (puts
}

/**************************************************************************/
/*
    Arduino loop function, called once 'setup' is complete (your own code
    should go here)
*/
/**************************************************************************/
void loop(void) 
{
  int i=0;
  IR1 = 0;

  while (i < samples){ 
    pulse.fetchLedData();
   //Adding up current values over 4 samples
    //IR1 += pulse.ps2;
    IR1 += pulse.ps1;
    i++;  
    }
      
 // get average (red+red+red+red/4)
  IR1 = IR1 / i;

  //Printing the raw LED values
  //For the python script, I'm sending the raw values separated by tabs.

  Serial.print(IR1);Serial.print("\t");
  
  
  /* Get a new sensor event */ 
  sensors_event_t accel, mag, gyro, temp;

  lsm.getEvent(&accel, &mag, &gyro, &temp); 
//  unsigned long startTime = micros();
  // print out accelleration data
  Serial.print((float)accel.acceleration.x,4); Serial.print("\t");
  Serial.print((float)accel.acceleration.y,4); Serial.print("\t");
  Serial.print((float)accel.acceleration.z,4); Serial.print("\t");
  /*
  Serial.print("Accel X: "); Serial.print(accel.acceleration.x); Serial.print(" ");
  Serial.print("  \tY: "); Serial.print(accel.acceleration.y);       Serial.print(" ");
  Serial.print("  \tZ: "); Serial.print(accel.acceleration.z);     Serial.println("  \tG");
  */

  // print out magnetometer data
  Serial.print((float)mag.magnetic.x,4); Serial.print("\t");
  Serial.print((float)mag.magnetic.y,4); Serial.print("\t");
  Serial.print((float)mag.magnetic.z,4); Serial.print("\t");
  /*
  Serial.print("Magn. X: "); Serial.print(mag.magnetic.x); Serial.print(" ");
  Serial.print("  \tY: "); Serial.print(mag.magnetic.y);       Serial.print(" ");
  Serial.print("  \tZ: "); Serial.print(mag.magnetic.z);     Serial.println("  \tgauss");
  */
  
  // print out gyroscopic data
  Serial.print((float)gyro.gyro.x,4); Serial.print("\t");
  Serial.print((float)gyro.gyro.y,4); Serial.print("\t");
  Serial.println((float)gyro.gyro.z,4);
                               
}
