/*
#include <opencv2\opencv.hpp>
#include <opencv\cv.h>
#include <opencv\highgui.h>
#include <iostream>
#include <thread> 

using namespace std;
using namespace cv;

std::list<Mat> images;
std::list<VideoCapture> cameras;

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

int colorTrack(int camNum){
	while(1){
		for (int i=0; i=camNum; ++i){
			cap1>>cameras[0]
			cap1>>image1;
			//cap2>>image2;
			// print to screen
			imshow("window1",image1);
			//imshow("window2",image2);

			//delay 33ms
			waitKey(33);
		}
	}
}


int main(){
	cout << "here it starts"<<endl;
//	cout <<countCameras();
	//create matrix to store image
	
	std::list<Mat>::iterator im_it=images.begin();
	Mat image;
	images.insert(im_it,image);
	
	// initialize capture
	VideoCapture cap;
	cap.open(0);
	std::this_thread::sleep_for (std::chrono::seconds(1));

	//create window to show image
	namedWindow("window1", 1);
	colorTrack(1);

	//namedWindow("window2", 1);


}

*/