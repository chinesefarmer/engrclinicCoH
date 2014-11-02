#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_L3GD20_U.h>
#include <Adafruit_LSM303_U.h>
#include <Adafruit_9DOF.h>
#include <math.h>

// -------------------- FOR QUATERNION ANALYSIS ----------------

// System constants
#define deltat 0.001f // sampling period in seconds (shown as 1 ms)
#define gyroMeasError 3.14159265358979 * (5.0f / 180.0f) // gyroscope measurement error in rad/s (shown as 5 deg/s)
#define gyroMeasDrift 3.14159265358979 * (0.2f / 180.0f) // gyroscope measurement error in rad/s/s (shown as 0.2f deg/s/s)
#define beta sqrt(3.0f / 4.0f) * gyroMeasError // compute beta
#define zeta sqrt(3.0f / 4.0f) * gyroMeasDrift // compute zeta

// Global system variables
float a_x, a_y, a_z; // accelerometer measurements
float w_x, w_y, w_z; // gyroscope measurements in rad/s
float m_x, m_y, m_z; // magnetometer measurements
float SEq_1 = 1, SEq_2 = 0, SEq_3 = 0, SEq_4 = 0; // estimated orientation quaternion elements with initial conditions
float b_x = 1, b_z = 0; // reference direction of flux in earth frame
float w_bx = 0, w_by = 0, w_bz = 0; // estimate gyroscope biases error

// Integer counter for print statements
volatile int printCount;
volatile float roll, pitch, yaw;
volatile float accelXprev, accelYprev, accelZprev, magXprev, magYprev, magZprev, gyroXprev, gyroYprev, gyroZprev;
volatile float accelXcur, accelYcur, accelZcur, magXcur, magYcur, magZcur, gyroXcur, gyroYcur, gyroZcur;
// Function declarations
float invSqrt(float x);

// -------------------------------------------------------------


// Assign a unique ID to this sensor at the same time 
Adafruit_9DOF                 dof   = Adafruit_9DOF();
Adafruit_L3GD20_Unified       gyro = Adafruit_L3GD20_Unified(20);
Adafruit_LSM303_Accel_Unified accel = Adafruit_LSM303_Accel_Unified(54321);
Adafruit_LSM303_Mag_Unified   mag = Adafruit_LSM303_Mag_Unified(12345);

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
  
  // Display some basic information on all sensors 
  displaySensorDetails();

}

void loop(void) 
{
  // Get a new sensor event  
  
  
  sensors_event_t event_gyro; 
  sensors_event_t event_accel; 
  sensors_event_t event_mag; 
  sensors_vec_t   orientation;
  
  mag.getEvent(&event_mag);
  gyro.getEvent(&event_gyro);
  accel.getEvent(&event_accel);

  filterUpdate(event_gyro.gyro.x,    event_gyro.gyro.x,    event_gyro.gyro.z,
                     event_accel.acceleration.x, event_accel.acceleration.y, event_accel.acceleration.z,
                     event_mag.magnetic.x, event_mag.magnetic.y, event_mag.magnetic.z);
 
  roll = atan2(2*(SEq_1*SEq_2 + SEq_3*SEq_4), 1 - 2*(SEq_2*SEq_2 + SEq_3*SEq_3))*180;
  pitch = asin(2*(SEq_1*SEq_3 - SEq_4*SEq_2))*180;
  yaw =  atan2(2*(SEq_1*SEq_4 + SEq_2*SEq_3), 1 - 2*(SEq_3*SEq_3 + SEq_4*SEq_4))*180;
  
  if (printCount > 400){
    printCount = 0;
     
   // Display the results (speed is measured in rad/s) 
  Serial.print("Xgyro: "); Serial.print(event_gyro.gyro.x); Serial.print("  ");
  Serial.print("Ygyro: "); Serial.print(event_gyro.gyro.y); Serial.print("  ");
  Serial.print("Zgyro: "); Serial.print(event_gyro.gyro.z); Serial.print("  "); Serial.println("rad/s ");
  
  // Display the results (acceleration is measured in m/s^2) 
  Serial.print("X: "); Serial.print(event_accel.acceleration.x); Serial.print("  ");
  Serial.print("Y: "); Serial.print(event_accel.acceleration.y); Serial.print("  ");
  Serial.print("Z: "); Serial.print(event_accel.acceleration.z); Serial.print("  ");Serial.println("m/s^2 ");
  
  // Display the results (magnetic vector values are in micro-Tesla (uT)) 
  Serial.print("Xmag: "); Serial.print(event_mag.magnetic.x); Serial.print("  ");
  Serial.print("Ymag: "); Serial.print(event_mag.magnetic.y); Serial.print("  ");
  Serial.print("Zmag: "); Serial.print(event_mag.magnetic.z); Serial.print("  ");Serial.println("uT");
  
    Serial.print("Quaternion values SEq_1: "); Serial.print(SEq_1); Serial.println("  ");
    Serial.print("Quaternion values SEq_2: "); Serial.print(SEq_2); Serial.println("  ");
    Serial.print("Quaternion values SEq_3: "); Serial.print(SEq_3); Serial.println("  ");
    Serial.print("Quaternion values SEq_4: "); Serial.print(SEq_4); Serial.println("  ");
    Serial.print("Quaternion values roll: "); Serial.print(roll); Serial.println("  ");
    Serial.print("Quaternion values pitch: "); Serial.print(pitch); Serial.println("  ");
    Serial.print("Quaternion values yaw: "); Serial.print(yaw); Serial.println("  "); Serial.println(" ");
  }
  else{
    printCount++;
  }
  
}
// Function to compute one filter iteration
void filterUpdate(float w_x, float w_y, float w_z, float a_x, float a_y, float a_z, float m_x, float m_y, float m_z)
{
	// local system variables
	float norm; // vector norm
	float SEqDot_omega_1, SEqDot_omega_2, SEqDot_omega_3, SEqDot_omega_4; // quaternion rate from gyroscopes elements
	float f_1, f_2, f_3, f_4, f_5, f_6; // objective function elements
	float J_11or24, J_12or23, J_13or22, J_14or21, J_32, J_33; // objective function Jacobian elements
	float J_41, J_42, J_43, J_44, J_51, J_52, J_53, J_54, J_61, J_62, J_63, J_64; //
	float SEqHatDot_1, SEqHatDot_2, SEqHatDot_3, SEqHatDot_4; // estimated direction of the gyroscope error
	float w_err_x, w_err_y, w_err_z; // estimated direction of the gyroscope error (angular)
	float h_x, h_y, h_z; // computed flux in the earth frame

	// axulirary variables to avoid reapeated calcualtions
	float halfSEq_1 = 0.5f * SEq_1;
	float halfSEq_2 = 0.5f * SEq_2;
	float halfSEq_3 = 0.5f * SEq_3;
	float halfSEq_4 = 0.5f * SEq_4;
	float twoSEq_1 = 2.0f * SEq_1;
	float twoSEq_2 = 2.0f * SEq_2;
	float twoSEq_3 = 2.0f * SEq_3;
	float twoSEq_4 = 2.0f * SEq_4;
	float twob_x = 2.0f * b_x;
	float twob_z = 2.0f * b_z;
	float twob_xSEq_1 = 2.0f * b_x * SEq_1;
	float twob_xSEq_2 = 2.0f * b_x * SEq_2;
	float twob_xSEq_3 = 2.0f * b_x * SEq_3;
	float twob_xSEq_4 = 2.0f * b_x * SEq_4;
	float twob_zSEq_1 = 2.0f * b_z * SEq_1;
	float twob_zSEq_2 = 2.0f * b_z * SEq_2;
	float twob_zSEq_3 = 2.0f * b_z * SEq_3;
	float twob_zSEq_4 = 2.0f * b_z * SEq_4;
	float SEq_1SEq_2;
	float SEq_1SEq_3 = SEq_1 * SEq_3;
	float SEq_1SEq_4;
	float SEq_2SEq_3;
	float SEq_2SEq_4 = SEq_2 * SEq_4;
	float SEq_3SEq_4;
	float twom_x = 2.0f * m_x;
	float twom_y = 2.0f * m_y;
	float twom_z = 2.0f * m_z;

	// normalise the accelerometer measurement
	norm = sqrt(a_x * a_x + a_y * a_y + a_z * a_z);
	a_x /= norm;
	a_y /= norm;
	a_z /= norm;

	// normalise the magnetometer measurement
	norm = sqrt(m_x * m_x + m_y * m_y + m_z * m_z);
	m_x /= norm;
	m_y /= norm;
	m_z /= norm;

	// compute the objective function and Jacobian
	f_1 = twoSEq_2 * SEq_4 - twoSEq_1 * SEq_3 - a_x;
	f_2 = twoSEq_1 * SEq_2 + twoSEq_3 * SEq_4 - a_y;
	f_3 = 1.0f - twoSEq_2 * SEq_2 - twoSEq_3 * SEq_3 - a_z;
	f_4 = twob_x * (0.5f - SEq_3 * SEq_3 - SEq_4 * SEq_4) + twob_z * (SEq_2SEq_4 - SEq_1SEq_3) - m_x;
	f_5 = twob_x * (SEq_2 * SEq_3 - SEq_1 * SEq_4) + twob_z * (SEq_1 * SEq_2 + SEq_3 * SEq_4) - m_y;
	f_6 = twob_x * (SEq_1SEq_3 + SEq_2SEq_4) + twob_z * (0.5f - SEq_2 * SEq_2 - SEq_3 * SEq_3) - m_z;
	J_11or24 = twoSEq_3; // J_11 negated in matrix multiplication
	J_12or23 = 2.0f * SEq_4;
	J_13or22 = twoSEq_1; // J_12 negated in matrix multiplication
	J_14or21 = twoSEq_2;
	J_32 = 2.0f * J_14or21; // negated in matrix multiplication
	J_33 = 2.0f * J_11or24; // negated in matrix multiplication
	J_41 = twob_zSEq_3; // negated in matrix multiplication
	J_42 = twob_zSEq_4;
	J_43 = 2.0f * twob_xSEq_3 + twob_zSEq_1; // negated in matrix multiplication
	J_44 = 2.0f * twob_xSEq_4 - twob_zSEq_2; // negated in matrix multiplication
	J_51 = twob_xSEq_4 - twob_zSEq_2; // negated in matrix multiplication
	J_52 = twob_xSEq_3 + twob_zSEq_1;
	J_53 = twob_xSEq_2 + twob_zSEq_4;
	J_54 = twob_xSEq_1 - twob_zSEq_3; // negated in matrix multiplication
	J_61 = twob_xSEq_3;
	J_62 = twob_xSEq_4 - 2.0f * twob_zSEq_2;
	J_63 = twob_xSEq_1 - 2.0f * twob_zSEq_3;
	J_64 = twob_xSEq_2;

	// compute the gradient (matrix multiplication)
	SEqHatDot_1 = J_14or21 * f_2 - J_11or24 * f_1 - J_41 * f_4 - J_51 * f_5 + J_61 * f_6;
	SEqHatDot_2 = J_12or23 * f_1 + J_13or22 * f_2 - J_32 * f_3 + J_42 * f_4 + J_52 * f_5 + J_62 * f_6;
	SEqHatDot_3 = J_12or23 * f_2 - J_33 * f_3 - J_13or22 * f_1 - J_43 * f_4 + J_53 * f_5 + J_63 * f_6;
	SEqHatDot_4 = J_14or21 * f_1 + J_11or24 * f_2 - J_44 * f_4 - J_54 * f_5 + J_64 * f_6;

	// normalise the gradient to estimate direction of the gyroscope error
	norm = sqrt(SEqHatDot_1 * SEqHatDot_1 + SEqHatDot_2 * SEqHatDot_2 + SEqHatDot_3 * SEqHatDot_3 + SEqHatDot_4 * SEqHatDot_4);
	SEqHatDot_1 = SEqHatDot_1 / norm;
	SEqHatDot_2 = SEqHatDot_2 / norm;
	SEqHatDot_3 = SEqHatDot_3 / norm;
	SEqHatDot_4 = SEqHatDot_4 / norm;

	// compute angular estimated direction of the gyroscope error
	w_err_x = twoSEq_1 * SEqHatDot_2 - twoSEq_2 * SEqHatDot_1 - twoSEq_3 * SEqHatDot_4 + twoSEq_4 * SEqHatDot_3;
	w_err_y = twoSEq_1 * SEqHatDot_3 + twoSEq_2 * SEqHatDot_4 - twoSEq_3 * SEqHatDot_1 - twoSEq_4 * SEqHatDot_2;
	w_err_z = twoSEq_1 * SEqHatDot_4 - twoSEq_2 * SEqHatDot_3 + twoSEq_3 * SEqHatDot_2 - twoSEq_4 * SEqHatDot_1;

	// compute and remove the gyroscope baises
	w_bx += w_err_x * deltat * zeta;
	w_by += w_err_y * deltat * zeta;
	w_bz += w_err_z * deltat * zeta;
	w_x -= w_bx;
	w_y -= w_by;
	w_z -= w_bz;

	// compute the quaternion rate measured by gyroscopes
	SEqDot_omega_1 = -halfSEq_2 * w_x - halfSEq_3 * w_y - halfSEq_4 * w_z;
	SEqDot_omega_2 = halfSEq_1 * w_x + halfSEq_3 * w_z - halfSEq_4 * w_y;
	SEqDot_omega_3 = halfSEq_1 * w_y - halfSEq_2 * w_z + halfSEq_4 * w_x;
	SEqDot_omega_4 = halfSEq_1 * w_z + halfSEq_2 * w_y - halfSEq_3 * w_x;

	// compute then integrate the estimated quaternion rate
	SEq_1 += (SEqDot_omega_1 - (beta * SEqHatDot_1)) * deltat;
	SEq_2 += (SEqDot_omega_2 - (beta * SEqHatDot_2)) * deltat;
	SEq_3 += (SEqDot_omega_3 - (beta * SEqHatDot_3)) * deltat;
	SEq_4 += (SEqDot_omega_4 - (beta * SEqHatDot_4)) * deltat;

	// normalise quaternion
	norm = sqrt(SEq_1 * SEq_1 + SEq_2 * SEq_2 + SEq_3 * SEq_3 + SEq_4 * SEq_4);
	SEq_1 /= norm;
	SEq_2 /= norm;
	SEq_3 /= norm;
	SEq_4 /= norm;

	// compute flux in the earth frame
	SEq_1SEq_2 = SEq_1 * SEq_2; // recompute axulirary variables
	SEq_1SEq_3 = SEq_1 * SEq_3;
	SEq_1SEq_4 = SEq_1 * SEq_4;
	SEq_3SEq_4 = SEq_3 * SEq_4;
	SEq_2SEq_3 = SEq_2 * SEq_3;
	SEq_2SEq_4 = SEq_2 * SEq_4;
	h_x = twom_x * (0.5f - SEq_3 * SEq_3 - SEq_4 * SEq_4) + twom_y * (SEq_2SEq_3 - SEq_1SEq_4) + twom_z * (SEq_2SEq_4 + SEq_1SEq_3);
	h_y = twom_x * (SEq_2SEq_3 + SEq_1SEq_4) + twom_y * (0.5f - SEq_2 * SEq_2 - SEq_4 * SEq_4) + twom_z * (SEq_3SEq_4 - SEq_1SEq_2);
	h_z = twom_x * (SEq_2SEq_4 - SEq_1SEq_3) + twom_y * (SEq_3SEq_4 + SEq_1SEq_2) + twom_z * (0.5f - SEq_2 * SEq_2 - SEq_3 * SEq_3);
	
	// normalise the flux vector to have only components in the x and z
	b_x = sqrt((h_x * h_x) + (h_y * h_y));
	b_z = h_z;
}
//---------------------------------------------------------------------------------------------------
// Fast inverse square-root
// See: http://en.wikipedia.org/wiki/Fast_inverse_square_root

float invSqrt(float x) {
  
   uint32_t i = 0x5F1F1412 - (*(uint32_t*)&x >> 1);
   float tmp = *(float*)&i;
   return tmp * (1.69000231f - 0.714158168f * x * tmp * tmp);
}



