/* Si1143 Example */


#define sleep  100
#define led1 10
#define led2 11
#define led3 13
#define led4 12

#include <Wire.h>
#include "SI1143.h";

int bias1,bias2,bias3,PS1,PS2,PS3;
int blinktime,counter,counter1,counter2,Ledposition;
unsigned int Light_Reading;
byte LowB,HighB;
bool selected;

void setup()
{
  Serial.begin(9600);
  pinMode(led1, OUTPUT); 
  pinMode(led2, OUTPUT); 
  pinMode(led3, OUTPUT);
  pinMode(led4, OUTPUT); 
  pinMode(50, OUTPUT);
  
  digitalWrite(13, HIGH);
  //Serial.println("writeLEDomgz");
  delay(25);
  Wire.begin(); // join i2c bus (address optional for master)
  delay(25);
  Serial.println("writeLED");
  
  write_reg(HW_KEY, 0x17); // Setting up LED Power to full
  write_reg(PS_LED21,0xFF);
  write_reg(PS_LED3, 0x0F);
  param_set(CHLIST,0b00010111);
  
  Serial.println("DEBUG 1");
  
  char parameter = read_reg(PARAM_RD,1);
// Serial.print("CHLIST = ");
// Serial.println(parameter,BIN);
  Serial.println("DEBUG 1.5");

  delay(1000);
  bias();
  
  Serial.println("DEBUG 2");
  
  counter = 0;
  counter1 = 0;
  counter2 = 0;
  selected = 0;
  blinktime = 75;
}

void loop()
{  
  Serial.println("loop");
  write_reg(COMMAND,0b00000101); // Get a reading
  delay(5);
  
  LowB = read_reg(PS1_DATA0,1); // Read the data for the first LED
  HighB = read_reg(PS1_DATA1,1);
  PS1 = ((HighB * 255) + LowB) - bias1;
  
  LowB = read_reg(PS2_DATA0,1);  // Read the data for the second LED
  HighB = read_reg(PS2_DATA1,1);
  PS2 = (HighB * 255) + LowB - bias2;
  
  LowB = read_reg(PS3_DATA0,1);  // Read the data for the third LED
  HighB = read_reg(PS3_DATA1,1);
  PS3 = (HighB * 255) + LowB - bias3;
  
  Light_Reading = read_light();
  if(Light_Reading >= 330) digitalWrite(led4, HIGH);
  else digitalWrite(led4, LOW);

    if(selected != 1) { 
    if (counter > 10 || counter1 > 10 || counter2 > 10){
      selected = 1;   
      touch_select();
  }
   }
  
  if (PS1 > 200 || PS2 > 200 || PS3 > 200){
      if (PS1 > PS2 && PS1 > PS3){
          if (selected == 0){
          digitalWrite(led1, HIGH);
          digitalWrite(led2, LOW);
          digitalWrite(led3, LOW);
          counter++;
          Ledposition = 1;
          counter1 = 0;
          counter2 = 0;
          }
      }else if(PS2 > PS1 && PS2 > PS3){
          if (selected == 0){
          digitalWrite(led1, LOW);
          digitalWrite(led2, HIGH);
          digitalWrite(led3, LOW);
          counter1++;
          Ledposition = 2;
          counter = 0;
          counter2 = 0;
        }
      }else if(PS3 > PS1 && PS3 > PS2){
          if (selected == 0){
          digitalWrite(led1, LOW);
          digitalWrite(led2, LOW);
          digitalWrite(led3, HIGH);
          counter2++;
          Ledposition = 3;
          counter = 0;
          counter1 = 0;
        }
      }
  }else{
    digitalWrite(led1, LOW);
    digitalWrite(led2, LOW);
    digitalWrite(led3, LOW);
    counter = 0;
    counter1 = 0;
    counter2 = 0;
    selected = 0;
  }
  
  //analogWrite(5, map(Light_Reading, 0, 10000, 0, 255));
  
}

unsigned int read_light(){  // Read light sensor
  write_reg(COMMAND,0b00000110);
  delay(sleep);
  byte LowB = read_reg(ALS_VIS_DATA0,1);
  byte HighB = read_reg(ALS_VIS_DATA1,1);
  return (HighB * 255) + LowB;
}

void param_set(byte address, byte val)  // Set Parameter
{
  write_reg(PARAM_WR, val);
  write_reg(COMMAND, 0xA0|address);
}

char read_reg(unsigned char address, int num_data) // Read a Register
{
  unsigned char data;

  Wire.beginTransmission(IR_ADDRESS);
  Wire.write(address);
  Wire.endTransmission();
  Serial.println("read reg");

  Wire.requestFrom(IR_ADDRESS, num_data);
  Serial.print("Num data is ");  Serial.println(num_data);
  Serial.print("Wire.available is "); Serial.println(Wire.available());
  while(Wire.available() < num_data);
    //Serial.println("omgz while loop");
  
  return Wire.read();
}

void write_reg(byte address, byte val) {  // Write a resigter
  Wire.beginTransmission(IR_ADDRESS); 
  Wire.write(address);      
  Wire.write(val);       
  Wire.endTransmission();     
}

void bias(void){  // Bias during start up
  
  for (int i=0; i<20; i++){
  write_reg(COMMAND,0b00000101);
  delay(50);
  
  byte LowB = read_reg(PS1_DATA0,1);
  byte HighB = read_reg(PS1_DATA1,1);
  
  bias1 += ((HighB * 255) + LowB) / 20;
  
  LowB = read_reg(PS2_DATA0,1);
  HighB = read_reg(PS2_DATA1,1);
  
  bias2 += ((HighB * 255) + LowB) / 20;
  
  LowB = read_reg(PS3_DATA0,1);
  HighB = read_reg(PS3_DATA1,1);
  
  bias3 += ((HighB * 255) + LowB) / 20;
}  
}

void touch_select(){    // just a blink routine for when something is selected
       switch (Ledposition) {
      case 1:
      
      for (int i = 0; i < 4; i++){
        digitalWrite(led1, LOW);
        delay(blinktime);
        digitalWrite(led1, HIGH);
        delay(blinktime);
      }
      break;
      case 2:
      for (int i = 0; i < 4; i++){
        digitalWrite(led2, LOW);
        delay(blinktime);
        digitalWrite(led2, HIGH);
        delay(blinktime);
      }
      break;
      case 3:
      for (int i = 0; i < 4; i++){
        digitalWrite(led3, LOW);
        delay(blinktime);
        digitalWrite(led3, HIGH);
        delay(blinktime);
      }
      break;
    }  
}
