#include <opencv\cv.h>
#include <opencv\highgui.h>
#include <iostream>

using namespace std;
using namespace cv;

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
	cout <<countCameras();
	//create matrix to store image
	Mat image1;
	Mat image2;
	// initialize capture
	VideoCapture cap1;
	//VideoCapture cap2;
	cap1.open(0);
	//cap2.open(1);

	//create window to show image
	namedWindow("window1", 1);

	//namedWindow("window2", 1);

	while(1){
		cap1>>image1;
		//cap2>>image2;
		// print to screen
		imshow("window1",image1);
		//imshow("window2",image2);

		//delay 33ms
		waitKey(33);
	}
}


