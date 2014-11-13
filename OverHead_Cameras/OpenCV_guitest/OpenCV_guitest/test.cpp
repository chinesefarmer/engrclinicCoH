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

Scalar findBox(Mat frame, int &lowH, int &highH, int &lowS, int &highS, int &lowV, int &highV)
{
	//Change and filter
	Mat hsvFrame, threshFrame;
	cvtColor(frame, hsvFrame, CV_RGB2HSV);
	inRange(hsvFrame,Scalar(lowH,lowS,lowV), Scalar(highH,highS,highV), threshFrame);
	//Smoothing Functions
	erode(threshFrame, threshFrame, getStructuringElement(MORPH_ELLIPSE,Size(5,5)));// remove objects
	dilate(threshFrame,threshFrame, getStructuringElement(MORPH_ELLIPSE,Size(5,5)));
		
	dilate(threshFrame,threshFrame, getStructuringElement(MORPH_ELLIPSE,Size(5,5)));// fill gaps
	erode(threshFrame, threshFrame, getStructuringElement(MORPH_ELLIPSE,Size(5,5)));
	//Find Rectangel
	//vector<vector<Point>> contoursFound;
	//findContours(threshFrame, contoursFound, CV_RETR_EXTERNAL,CV_CHAIN_APPROX_SIMPLE);
	//Scalar color( rand()&255, rand()&255, rand()&255 );
	//drawContours(threshFrame,contoursFound,-2, color, CV_FILLED,8);
	//Display Image

	imshow("Thresholded Image", threshFrame);
	imshow("Original", frame);

	return Scalar(0,0);
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



int main(){
	cout << "here it starts"<<endl;
//	cout <<countCameras();
	//create matrix to store image
	Mat image0;
	Mat frame, threshFrame;
	
	// initialize capture
	VideoCapture cap0(0);

	cap0.open(0);
	cout<<cap0.isOpened()<<endl;

	namedWindow("Control", CV_WINDOW_AUTOSIZE); //create a window called "Control"
	
	//Inital values for lower,higher bounds for HSV.
	int lowH = 68;
	int highH = 131;

	int lowS = 89; 
	int highS = 255;

	int lowV = 124;
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
		Scalar box1=findBox(image0, lowH, highH, lowS, highS, lowV, highV);
		//delay 33ms
		waitKey(33);
	}
}


