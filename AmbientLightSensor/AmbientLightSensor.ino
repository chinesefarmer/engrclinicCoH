/*
  ReadAnalogVoltage
  Reads an analog input on pin 0, converts it to voltage, and prints the result to the serial monitor.
  Attach the center pin of a potentiometer to pin A0, and the outside pins to +5V and ground.
 
 This example code is in the public domain.
 */

boolean stateCur = false;
float total = 0;                  // the running total
float average = 0;                // the average
int calibTime = 29000; //calibration time
boolean calib = false;

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);

}

// the loop routine runs over and over again forever:
void loop() {
  // read the input on analog pin 0:
  int sensorValue = analogRead(A0);
  // Convert the analog reading (which goes from 0 - 1023) to a voltage (0 - 5V):
  float voltage = sensorValue * (5.0 / 1023.0);

  if(calib == false){
    //The first two seconds set the ambient light level
    for(int index = 1; index < calibTime+1; index ++){
      // add the reading to the total:
      total= total + voltage;
     // delay(0.25);      
      }
     average = total/calibTime;
     calib = true;
     /*
     Serial.print("Average: ");
     Serial.println(average);
     Serial.print("Time (ms): ");
     Serial.println(millis());
     */
  }
  
  //We want to track the light level now.
  else{
    //subtracting the ambient light from the current reading
    float volCorrected = voltage - average;
    Serial.println(voltage);
    // print out the value you read:
    if (volCorrected > 0.03){
      if(stateCur == true){
      }
      else{
        Serial.print("Light: ");
        Serial.println(volCorrected);
        stateCur = true;
      }
    }
    else{
      if(stateCur == false){
      }
      else{
        Serial.print("Dark: ");
        Serial.println(volCorrected);
        stateCur = false;
      }
    }
    //Serial.println(volCorrected);
    //delay(250);
    delay(500);
  }

}
