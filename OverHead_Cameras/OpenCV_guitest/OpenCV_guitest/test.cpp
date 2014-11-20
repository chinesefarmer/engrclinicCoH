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


// Main color finding function
Point findBox(Mat frame, int &lowH, int &highH, int &lowS, int &highS, int &lowV, int &highV)
{
	//Change and filter
	Mat hsvFrame, threshFrame, edgeFrame;
	cvtColor(frame, hsvFrame, CV_RGB2HSV);
	inRange(hsvFrame,Scalar(lowH,lowS,lowV), Scalar(highH,highS,highV), threshFrame);

	//Smoothing Functions
	erode(threshFrame, threshFrame, getStructuringElement(MORPH_ELLIPSE,Size(5,5)));// remove objects
	dilate(threshFrame,threshFrame, getStructuringElement(MORPH_ELLIPSE,Size(5,5)));
	dilate(threshFrame,threshFrame, getStructuringElement(MORPH_ELLIPSE,Size(5,5)));// fill gaps
	erode(threshFrame, threshFrame, getStructuringElement(MORPH_ELLIPSE,Size(5,5)));
	
	//Find Rectangel
	Canny(threshFrame, edgeFrame, 0, 50, 5);
	
	vector<vector<Point>> contoursFound, squares;
	findContours(edgeFrame, contoursFound, CV_RETR_LIST,CV_CHAIN_APPROX_SIMPLE);
	// Test contours            
	vector<Point> approx;// used for finding perfect squares
	vector<Point> maxContour; // initalize max contour
	Point center;
	double maxArea = 0.0;
	for (size_t i = 0; i < contoursFound.size(); i++){
		// approximate contour with accuracy proportional
        // to the contour perimeter
		/*
        approxPolyDP(Mat(contoursFound[i]), approx, arcLength(Mat(contoursFound[i]), true)*0.02, true);
		// Note: absolute value of an area is used because 
		// area may be positive or negative - in accordance with the
		// contour orientation
		if (approx.size() <=5 && fabs(contourArea(Mat(approx))) > 100 &&
           isContourConvex(Mat(approx))){
			   squares.push_back(approx);}*/
		
		double contArea = contourArea(contoursFound[i]);
		if(contArea>1000) {
			if(contArea>maxArea){
				maxArea = contArea;
				maxContour = contoursFound[i];
			}
			squares.push_back(contoursFound[i]);
		}
    }	
	//Draw the contours on the original image
	Scalar color(255, 0, 0);
	if(maxArea !=0){
		Rect bRec = boundingRect(maxContour);
		rectangle(frame, bRec.tl(), bRec.br(), color, 1, 8, 0);
		center = Point(bRec.x + bRec.width/2, bRec.y - bRec.height/2)
	} else {
		cerr<<"Did not find a contour!"<<endl;
	}
	//Display Image
	imshow("Thresholded Image", threshFrame);
	imshow("Canny Image", edgeFrame);
	imshow("Original", frame);

	return center;
}
// Creates trackbar for Hue, Saturation and Value
int createFilterTrackbar(int &lowH, int &highH, int &lowS, int &highS, int &lowV, int &highV){
	namedWindow("Control", CV_WINDOW_AUTOSIZE); //create a window called "Control"
	cvCreateTrackbar("LowH", "Control", &lowH, 179); //Hue (0 - 179)
	cvCreateTrackbar("HighH", "Control", &highH, 179);

	cvCreateTrackbar("LowS", "Control", &lowS, 255); //Saturation (0 - 255)
	cvCreateTrackbar("HighS", "Control", &highS, 255);

	cvCreateTrackbar("LowV", "Control", &lowV, 255); //Value (0 - 255)
	cvCreateTrackbar("HighV", "Control", &highV, 255);
	return 0;
}

// Saving function
VideoWriter& intSave(VideoCapture &cap0, string name){
	double dWidth = cap0.get(CV_CAP_PROP_FRAME_WIDTH); //get the width of frames of the video
	double dHeight = cap0.get(CV_CAP_PROP_FRAME_HEIGHT); //get the height of frames of the video
	Size frameSize(static_cast<int>(dWidth), static_cast<int>(dHeight));
	string videoName = "C:/Users/jyang/Desktop/Code/";
	videoName += name;
	
	VideoWriter saveVideo(videoName,
		CV_FOURCC('M','P','4','2'), 20, frameSize, true); //initialize the VideoWriter object 'P','I','M','1'
	
	if ( !saveVideo.isOpened() ) {//if not initialize the VideoWriter successfully, exit the program
        cerr << "ERROR: Failed to write the video" << endl;
   }
	return saveVideo;
}

int main(){
	cout << "here it starts"<<endl;
	//create matrix to store image
	Mat image0;
	Mat frame, threshFrame;
	
	// initialize frames
	VideoCapture cap0(0);

	cap0.open(0);
	if(!cap0.isOpened()){
		cerr<<"Error: Cannot open video file"<<endl;
		return -1;
	}

	//Initialize frame saving
	//VideoWriter saveVideo = intSave(cap0, "video.avi");
	
	//Inital values for lower,higher bounds for HSV.
	int lowH = 68;
	int highH = 131;

	int lowS = 70; 
	int highS = 255;

	int lowV = 124;
	int highV = 255;

	//Create trackbars in "Control" window
	createFilterTrackbar(lowH, highH, lowS, highS, lowV, highV);

	// Continuously capture pictures and filter them
	while(1){
		cap0>>image0;
		Point center = findBox(image0, lowH, highH, lowS, highS, lowV, highV);
		//delay 33ms
		waitKey(33);
		
		//saveVideo.write(image0);
		if (waitKey(10) == 27) //wait for 'esc' key press for 30ms. If 'esc' key is pressed, break loop
		{
			cout << "esc key is pressed by user" << endl;
            break;
		}
	}
	return 0;
}


