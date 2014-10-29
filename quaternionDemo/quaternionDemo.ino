#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_L3GD20_U.h>
#include <Adafruit_LSM303_U.h>
#include <Adafruit_9DOF.h>
#include <math.h>

// -------------------- FOR QUATERNION ANALYSIS ----------------

// Definitions
#define sampleFreq	80.0f		// sample frequency in Hz
#define betaDef		0.1f		// 2 * proportional gain

// Variable definitions
volatile float beta = betaDef;								// 2 * proportional gain (Kp)
volatile float q0 = 1.0f, q1 = 0.0f, q2 = 0.0f, q3 = 0.0f;	// quaternion of sensor frame relative to auxiliary frame

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
  
 /*
  // Display the results (speed is measured in rad/s) 
  Serial.print("Xgyro: "); Serial.print(event_gyro.gyro.x); Serial.print("  ");
  Serial.print("Ygyro: "); Serial.print(event_gyro.gyro.y); Serial.print("  ");
  Serial.print("Zgyro: "); Serial.print(event_gyro.gyro.z); Serial.print("  ");
  Serial.println("rad/s ");
  delay(500);
  
  // Display the results (acceleration is measured in m/s^2) 
  Serial.print("X: "); Serial.print(event_accel.acceleration.x); Serial.print("  ");
  Serial.print("Y: "); Serial.print(event_accel.acceleration.y); Serial.print("  ");
  Serial.print("Z: "); Serial.print(event_accel.acceleration.z); Serial.print("  ");Serial.println("m/s^2 ");
  delay(500);
  
  // Display the results (magnetic vector values are in micro-Tesla (uT)) 
  Serial.print("Xmag: "); Serial.print(event_mag.magnetic.x); Serial.print("  ");
  Serial.print("Ymag: "); Serial.print(event_mag.magnetic.y); Serial.print("  ");
  Serial.print("Zmag: "); Serial.print(event_mag.magnetic.z); Serial.print("  ");Serial.println("uT");
  delay(500);
  */
   
    /*
  MadgwickAHRSupdate(event_gyro.gyro.x,    event_gyro.gyro.x,    event_gyro.gyro.z,
                     event_accel.acceleration.x, event_accel.acceleration.y, event_accel.acceleration.z,
                     event_mag.magnetic.x, event_mag.magnetic.y, event_mag.magnetic.z);*/

  MadgwickAHRSupdateIMU(event_gyro.gyro.x,    event_gyro.gyro.x,    event_gyro.gyro.z,
                     event_accel.acceleration.x, event_accel.acceleration.y, event_accel.acceleration.z);
  /*
  // Testing with 0 gyro movement
    MadgwickAHRSupdate(0.0f,    0.0f,    0.0f,
                     event_accel.acceleration.x, event_accel.acceleration.y, event_accel.acceleration.z,
                     event_mag.magnetic.x, event_mag.magnetic.y, event_mag.magnetic.z);

  MadgwickAHRSupdateIMU(0.0f,    0.0f,    0.0f,
                     event_accel.acceleration.x, event_accel.acceleration.y, event_accel.acceleration.z);*/
  
  roll = atan2(2*(q0*q1 + q2*q3), 1 - 2*(q1*q1 + q2*q2));
  pitch = asin(2*(q0*q2 - q3*q1));
  yaw =  atan2(2*(q0*q3 + q1*q2), 1 - 2*(q2*q2 + q3*q3));
  
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
  
    Serial.print("Quaternion values q0: "); Serial.print(q0); Serial.println("  ");
    Serial.print("Quaternion values q1: "); Serial.print(q1); Serial.println("  ");
    Serial.print("Quaternion values q2: "); Serial.print(q2); Serial.println("  ");
    Serial.print("Quaternion values q3: "); Serial.print(q3); Serial.println("  ");
    Serial.print("Quaternion values roll: "); Serial.print(roll); Serial.println("  ");
    Serial.print("Quaternion values pitch: "); Serial.print(pitch); Serial.println("  ");
    Serial.print("Quaternion values yaw: "); Serial.print(yaw); Serial.println("  "); Serial.println(" ");
  }
  else{
    printCount++;
  }
  
}


void MadgwickAHRSupdate(float gx, float gy, float gz, float ax, float ay, float az, float mx, float my, float mz) {
	float recipNorm;
	float s0, s1, s2, s3;
	float qDot1, qDot2, qDot3, qDot4;
	float hx, hy;
	float _2q0mx, _2q0my, _2q0mz, _2q1mx, _2bx, _2bz, _4bx, _4bz, _2q0, _2q1, _2q2, _2q3, _2q0q2, _2q2q3, q0q0, q0q1, q0q2, q0q3, q1q1, q1q2, q1q3, q2q2, q2q3, q3q3;

	// Use IMU algorithm if magnetometer measurement invalid (avoids NaN in magnetometer normalisation)
	if((mx == 0.0f) && (my == 0.0f) && (mz == 0.0f)) {
		MadgwickAHRSupdateIMU(gx, gy, gz, ax, ay, az);
		return;
	}

	// Rate of change of quaternion from gyroscope
	qDot1 = 0.5f * (-q1 * gx - q2 * gy - q3 * gz);
	qDot2 = 0.5f * (q0 * gx + q2 * gz - q3 * gy);
	qDot3 = 0.5f * (q0 * gy - q1 * gz + q3 * gx);
	qDot4 = 0.5f * (q0 * gz + q1 * gy - q2 * gx);

	// Compute feedback only if accelerometer measurement valid (avoids NaN in accelerometer normalisation)
	if(!((ax == 0.0f) && (ay == 0.0f) && (az == 0.0f))) {

		// Normalise accelerometer measurement
		recipNorm = invSqrt(ax * ax + ay * ay + az * az);
		ax *= recipNorm;
		ay *= recipNorm;
		az *= recipNorm;   

		// Normalise magnetometer measurement
		recipNorm = invSqrt(mx * mx + my * my + mz * mz);
		mx *= recipNorm;
		my *= recipNorm;
		mz *= recipNorm;

		// Auxiliary variables to avoid repeated arithmetic
		_2q0mx = 2.0f * q0 * mx;
		_2q0my = 2.0f * q0 * my;
		_2q0mz = 2.0f * q0 * mz;
		_2q1mx = 2.0f * q1 * mx;
		_2q0 = 2.0f * q0;
		_2q1 = 2.0f * q1;
		_2q2 = 2.0f * q2;
		_2q3 = 2.0f * q3;
		_2q0q2 = 2.0f * q0 * q2;
		_2q2q3 = 2.0f * q2 * q3;
		q0q0 = q0 * q0;
		q0q1 = q0 * q1;
		q0q2 = q0 * q2;
		q0q3 = q0 * q3;
		q1q1 = q1 * q1;
		q1q2 = q1 * q2;
		q1q3 = q1 * q3;
		q2q2 = q2 * q2;
		q2q3 = q2 * q3;
		q3q3 = q3 * q3;

		// Reference direction of Earth's magnetic field
		hx = mx * q0q0 - _2q0my * q3 + _2q0mz * q2 + mx * q1q1 + _2q1 * my * q2 + _2q1 * mz * q3 - mx * q2q2 - mx * q3q3;
		hy = _2q0mx * q3 + my * q0q0 - _2q0mz * q1 + _2q1mx * q2 - my * q1q1 + my * q2q2 + _2q2 * mz * q3 - my * q3q3;
		_2bx = sqrt(hx * hx + hy * hy);
		_2bz = -_2q0mx * q2 + _2q0my * q1 + mz * q0q0 + _2q1mx * q3 - mz * q1q1 + _2q2 * my * q3 - mz * q2q2 + mz * q3q3;
		_4bx = 2.0f * _2bx;
		_4bz = 2.0f * _2bz;

		// Gradient decent algorithm corrective step
		s0 = -_2q2 * (2.0f * q1q3 - _2q0q2 - ax) + _2q1 * (2.0f * q0q1 + _2q2q3 - ay) - _2bz * q2 * (_2bx * (0.5f - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx) + (-_2bx * q3 + _2bz * q1) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my) + _2bx * q2 * (_2bx * (q0q2 + q1q3) + _2bz * (0.5f - q1q1 - q2q2) - mz);
		s1 = _2q3 * (2.0f * q1q3 - _2q0q2 - ax) + _2q0 * (2.0f * q0q1 + _2q2q3 - ay) - 4.0f * q1 * (1 - 2.0f * q1q1 - 2.0f * q2q2 - az) + _2bz * q3 * (_2bx * (0.5f - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx) + (_2bx * q2 + _2bz * q0) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my) + (_2bx * q3 - _4bz * q1) * (_2bx * (q0q2 + q1q3) + _2bz * (0.5f - q1q1 - q2q2) - mz);
		s2 = -_2q0 * (2.0f * q1q3 - _2q0q2 - ax) + _2q3 * (2.0f * q0q1 + _2q2q3 - ay) - 4.0f * q2 * (1 - 2.0f * q1q1 - 2.0f * q2q2 - az) + (-_4bx * q2 - _2bz * q0) * (_2bx * (0.5f - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx) + (_2bx * q1 + _2bz * q3) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my) + (_2bx * q0 - _4bz * q2) * (_2bx * (q0q2 + q1q3) + _2bz * (0.5f - q1q1 - q2q2) - mz);
		s3 = _2q1 * (2.0f * q1q3 - _2q0q2 - ax) + _2q2 * (2.0f * q0q1 + _2q2q3 - ay) + (-_4bx * q3 + _2bz * q1) * (_2bx * (0.5f - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx) + (-_2bx * q0 + _2bz * q2) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my) + _2bx * q1 * (_2bx * (q0q2 + q1q3) + _2bz * (0.5f - q1q1 - q2q2) - mz);
		recipNorm = invSqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3); // normalise step magnitude
		s0 *= recipNorm;
		s1 *= recipNorm;
		s2 *= recipNorm;
		s3 *= recipNorm;

		// Apply feedback step
		qDot1 -= beta * s0;
		qDot2 -= beta * s1;
		qDot3 -= beta * s2;
		qDot4 -= beta * s3;
	}

	// Integrate rate of change of quaternion to yield quaternion
	q0 += qDot1 * (1.0f / sampleFreq);
	q1 += qDot2 * (1.0f / sampleFreq);
	q2 += qDot3 * (1.0f / sampleFreq);
	q3 += qDot4 * (1.0f / sampleFreq);

	// Normalise quaternion
	recipNorm = invSqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3);
	q0 *= recipNorm;
	q1 *= recipNorm;
	q2 *= recipNorm;
	q3 *= recipNorm;
}

//---------------------------------------------------------------------------------------------------
// IMU algorithm update

void MadgwickAHRSupdateIMU(float gx, float gy, float gz, float ax, float ay, float az) {
	float recipNorm;
	float s0, s1, s2, s3;
	float qDot1, qDot2, qDot3, qDot4;
	float _2q0, _2q1, _2q2, _2q3, _4q0, _4q1, _4q2 ,_8q1, _8q2, q0q0, q1q1, q2q2, q3q3;

	// Rate of change of quaternion from gyroscope
	qDot1 = 0.5f * (-q1 * gx - q2 * gy - q3 * gz);
	qDot2 = 0.5f * (q0 * gx + q2 * gz - q3 * gy);
	qDot3 = 0.5f * (q0 * gy - q1 * gz + q3 * gx);
	qDot4 = 0.5f * (q0 * gz + q1 * gy - q2 * gx);

	// Compute feedback only if accelerometer measurement valid (avoids NaN in accelerometer normalisation)
	if(!((ax == 0.0f) && (ay == 0.0f) && (az == 0.0f))) {

		// Normalise accelerometer measurement
		recipNorm = invSqrt(ax * ax + ay * ay + az * az);
		ax *= recipNorm;
		ay *= recipNorm;
		az *= recipNorm;   

		// Auxiliary variables to avoid repeated arithmetic
		_2q0 = 2.0f * q0;
		_2q1 = 2.0f * q1;
		_2q2 = 2.0f * q2;
		_2q3 = 2.0f * q3;
		_4q0 = 4.0f * q0;
		_4q1 = 4.0f * q1;
		_4q2 = 4.0f * q2;
		_8q1 = 8.0f * q1;
		_8q2 = 8.0f * q2;
		q0q0 = q0 * q0;
		q1q1 = q1 * q1;
		q2q2 = q2 * q2;
		q3q3 = q3 * q3;

		// Gradient decent algorithm corrective step
		s0 = _4q0 * q2q2 + _2q2 * ax + _4q0 * q1q1 - _2q1 * ay;
		s1 = _4q1 * q3q3 - _2q3 * ax + 4.0f * q0q0 * q1 - _2q0 * ay - _4q1 + _8q1 * q1q1 + _8q1 * q2q2 + _4q1 * az;
		s2 = 4.0f * q0q0 * q2 + _2q0 * ax + _4q2 * q3q3 - _2q3 * ay - _4q2 + _8q2 * q1q1 + _8q2 * q2q2 + _4q2 * az;
		s3 = 4.0f * q1q1 * q3 - _2q1 * ax + 4.0f * q2q2 * q3 - _2q2 * ay;
		recipNorm = invSqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3); // normalise step magnitude
		s0 *= recipNorm;
		s1 *= recipNorm;
		s2 *= recipNorm;
		s3 *= recipNorm;

		// Apply feedback step
		qDot1 -= beta * s0;
		qDot2 -= beta * s1;
		qDot3 -= beta * s2;
		qDot4 -= beta * s3;
	}

	// Integrate rate of change of quaternion to yield quaternion
	q0 += qDot1 * (1.0f / sampleFreq);
	q1 += qDot2 * (1.0f / sampleFreq);
	q2 += qDot3 * (1.0f / sampleFreq);
	q3 += qDot4 * (1.0f / sampleFreq);

	// Normalise quaternion
	recipNorm = invSqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3);
	q0 *= recipNorm;
	q1 *= recipNorm;
	q2 *= recipNorm;
	q3 *= recipNorm;
}

//---------------------------------------------------------------------------------------------------
// Fast inverse square-root
// See: http://en.wikipedia.org/wiki/Fast_inverse_square_root

float invSqrt(float x) {
  
   uint32_t i = 0x5F1F1412 - (*(uint32_t*)&x >> 1);
   float tmp = *(float*)&i;
   return tmp * (1.69000231f - 0.714158168f * x * tmp * tmp);
}
