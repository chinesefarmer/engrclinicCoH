#include <opencv\cv.h>
#include <opencv\highgui.h>
#include <iostream>
#include <thread> 
#include <list>
/*
Using the PS3 Camera, the lens focal length is 210mm
Data can be found in http://commons.wikimedia.org/wiki/File:PlayStation-Eye.jpg
http://www.engadget.com/products/sony/playstation/eye/specs/
*/

using namespace std;
using namespace cv;

int main(){
	cout << "here it starts"<<endl;
//	cout <<countCameras();
	//create matrix to store image
	Mat image0;
	Mat image1;
	
	// initialize capture
	VideoCapture cap0(0);
	VideoCapture cap1(1);
	cap0.open(0);
	cout<<cap0.isOpened()<<endl;
	//sleep
	this_thread::sleep_for (chrono::milliseconds(1));
	cap1.open(1);
	cout<<cap1.isOpened()<<endl;
	//create window to show image
	namedWindow("window1", 0);
	namedWindow("window2", 1);
	
	int lowH = 0;
	int highH = 179;

	int lowS = 0; 
	int highS = 255;

	int lowV = 0;
	int highV = 255;

	//Create trackbars in "Control" window
	cvCreateTrackbar("LowH", "Control", &lowH, 179); //Hue (0 - 179)
	cvCreateTrackbar("HighH", "Control", &highH, 179);

	cvCreateTrackbar("LowS", "Control", &lowS, 255); //Saturation (0 - 255)
	cvCreateTrackbar("HighS", "Control", &highS, 255);

	cvCreateTrackbar("LowV", "Control", &lowV, 255); //Value (0 - 255)
	cvCreateTrackbar("HighV", "Control", &highV, 255);

	while(1){
		cap0>>image0;
		//this_thread::sleep_for (chrono::milliseconds(1));
		cap1>>image1;
		// print to screen
		//findBox(image0, lowH, highH, lowS, highS, lowV, highV);
		imshow("window1",image0);
		//delay 33ms
		waitKey(33);
	}
}


int findBox(Mat frame, int &lowH, int &highH, int &lowS, int &highS, int &lowV, int &highV)
{
	Mat hsvFrame, threshFrame;
	cvtColor(frame, hsvFrame, CV_RGB2HSV);
	//inRange(hsvFrame,)
	return 0;
}


int countCameras(){
   VideoCapture temp_camera;
   int maxTested = 10;
   for (int i = 0; i < maxTested; i++){
	   cv::VideoCapture temp_camera(i);
	   bool res = (!temp_camera.isOpened());
	   temp_camera.release();
	   if (res){
			return i;
	   }
   }
}
