/* SI1143_proximity_demo.ino
 * http://moderndevice.com/product/si1143-proximity-sensors/
 * Reads the Proximity Sensor and either prints raw LED data or angular data 
 * depending the options chosen in the #define's below
 * Paul Badger, Gavin Atkinson, Jean-Claude Wippler  2013
 */

//$ Comments mean that I commented out a normal print line for the purpose of interfacing with
//python.

/*
  For Arduino users use the following pins for various ports
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
 
unsigned long lastMillis, red, IR1, IR2;
PortI2C myBus (PORT_FOR_SI114);
//pulse is of type PulsePlug, defined in header file
PulsePlug pulse (myBus); 

void setup () {
    Serial.begin(57600);

    if (!pulse.isPresent()) {
        Serial.print("No SI114x found on Port ");
        Serial.println(PORT_FOR_SI114);
    }
    
    Serial.begin(57600);
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

void loop(){
  unsigned long total=0, start;
  int i=0;
  red = 0;
  IR1 = 0;
  IR2 = 0;
  total = 0;
  //Records start time of looping
  start = millis();

  while (i < samples){ 
    pulse.fetchLedData();
   //Adding up current values over 4 samples
    red += pulse.ps1;
    IR1 += pulse.ps2;
    IR2 += pulse.ps3;
    i++;  
    }
      
  red = red / i;  // get average (red+red+red+red/4)
  IR1 = IR1 / i;
  IR2 = IR2 / i;
  total = red + IR1 + IR2;
  
  int sensorValue = analogRead(A0);
  // Convert the analog reading (which goes from 0 - 1023) to a voltage (0 - 5V):
  float voltage = sensorValue;// * (5.0 / 1023.0);
  //Printing the raw LED values, der
  //For the python script, I'm sending the raw values separated by tabs.
  Serial.print(red);
  Serial.print("\t"); //prints tab
  Serial.print(IR1);
  Serial.print("\t");
  Serial.print(IR2);
  Serial.print("\t");
  Serial.println(voltage);
                               
  delay(10);                                                                                              
}
