# USAGE
# python ncs_realtime_objectdetection.py --graph graphs/mobilenetgraph --display 1
# python ncs_realtime_objectdetection.py --graph graphs/mobilenetgraph --confidence 0.5 --display 1
from time import sleep
import time
import RPi.GPIO as GPIO

# Note : this script/repo doesn't work on Nvidia jetson platforms out of the box.

# import the necessary packages
from mvnc import mvncapi as mvnc
from imutils.video import VideoStream
from imutils.video import FPS
import argparse
import numpy as np
import time
import cv2
#Mot1 = 22    # Motor  forward
#Mot2 = 18    # Motor back

Act1 = 13    # Lift

Act2 = 15    # Lower

Act3 = 11    # Enable


Hyd1 = 33    # Clip

Hyd2 = 35    # Unclip

Hyd3 = 31    # Enable

#GPIO.setup(Mot1,GPIO.OUT)

#GPIO.setup(Mot2,GPIO.OUT)


CLASSES = ["background", "dog"]

COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

# frame dimensions should be sqaure
PREPROCESS_DIMS = (300, 300)
DISPLAY_DIMS = (900, 900)

# calculate the multiplier needed to scale the bounding boxes
DISP_MULTIPLIER = DISPLAY_DIMS[0] // PREPROCESS_DIMS[0]
def Cembre_forward(Mot1, Mot2):    
    GPIO.output(Mot1,GPIO.HIGH)
    GPIO.output(Mot2,GPIO.LOW)

def Cembre_backward(Mot1, Mot2):    
    GPIO.output(Mot1,GPIO.LOW)
    GPIO.output(Mot2,GPIO.HIGH)

def Cembre_lift(Act1, Act2, Act3):    
    GPIO.output(Act1,GPIO.HIGH)
    GPIO.output(Act2,GPIO.LOW)
    GPIO.output(Act3,GPIO.HIGH)

def Cembre_lower(Act1, Act2, Act3):    
    GPIO.output(Act1,GPIO.LOW)
    GPIO.output(Act2,GPIO.HIGH)
    GPIO.output(Act3,GPIO.HIGH)

def Cembre_stop(Act1, Act2, Hyd3, Mot1, Mot2):
    GPIO.output(Act1,GPIO.LOW)
    GPIO.output(Act2,GPIO.LOW)
    GPIO.output(Hyd3,GPIO.LOW)
    GPIO.output(Mot1,GPIO.LOW)
    GPIO.output(Mot2,GPIO.LOW)
    
def Cembre_clip(Hyd1, Hyd2, Hyd3):    
    GPIO.output(Hyd1,GPIO.HIGH)
    GPIO.output(Hyd2,GPIO.LOW)
    GPIO.output(Hyd3,GPIO.HIGH)

def Cembre_unclip(Hyd1, Hyd2, Hyd3):    
    GPIO.output(Hyd1,GPIO.LOW)
    GPIO.output(Hyd2,GPIO.HIGH)
    GPIO.output(Hyd3,GPIO.HIGH)

def Cembre_stop(Hyd3):

    GPIO.output(Hyd3,GPIO.LOW)

def preprocess_image(input_image):
    # preprocess the image
    #print("process image")
    preprocessed = cv2.resize(input_image, PREPROCESS_DIMS)
    preprocessed = preprocessed - 127.5
    preprocessed = preprocessed * 0.007843
    preprocessed = preprocessed.astype(np.float16)

    # return the image to the calling function
    return preprocessed

def predict(image, graph):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(18,GPIO.OUT)
    GPIO.setup(22,GPIO.OUT)

    GPIO.output(18,GPIO.LOW)
    GPIO.output(22,GPIO.HIGH)
    GPIO.setup(Act1,GPIO.OUT)
    GPIO.setup(Act2,GPIO.OUT)
    GPIO.setup(Act3,GPIO.OUT)
    GPIO.setup(Hyd1,GPIO.OUT)
    GPIO.setup(Hyd2,GPIO.OUT)
    GPIO.setup(Hyd3,GPIO.OUT)
    # preprocess the image
    #image = preprocess_image(image)

    # send the image to the NCS and run a forward pass to grab the
    # network predictions
    #print("going to process image")
    image = preprocess_image(image)
    #print("start queue inference")
    #graph.queue_inference_with_fifo_elem (input_fifo, output_fifo, image, image)
    #print("success queue inference")
    graph.LoadTensor(image, None)
    #print("load graph")
    (output, _) = graph.GetResult()
    #print("outpout")
    #(output, _) = output_fifo.read_elem()
    #print("success read_element")
    # grab the number of valid object predictions from the output,
    # then initialize the list of predictions
    num_valid_boxes = output[0]
     
    #print ('output', num_valid_boxes)
    predictions = []
    #print("num_valid_boxes",num_valid_boxes)
    # loop over results

    # loop over results
    for box_index in range(int(num_valid_boxes)):
        # calculate the base index into our array so we can extract
        # bounding box information
        base_index = 7 + box_index * 7
        pre_class = int(output[base_index + 1])
        #confi = output[base_index +2]
        #if confi >= 95:
        if output[base_index +2] >= 0.996: 
            #print ("pred class", output[base_index + 1])
            print ("Confidence 1111", output[base_index +2])
            sleep(0.91)
            GPIO.output(18,GPIO.LOW)
            GPIO.output(22,GPIO.LOW)
            Cembre_lower(Act1, Act2, Act3)
            
            sleep(20)
            Cembre_unclip(Hyd1, Hyd2, Hyd3)
            sleep(2.7)
            sleep(5)
            Cembre_stop(Hyd3)
            Cembre_clip(Hyd1, Hyd2, Hyd3)
            #Cembre_unclip(Hyd1, Hyd2, Hyd3)
            sleep(2.7)
            Cembre_stop(Hyd3)
            Cembre_lift(Act1, Act2, Act3)
            sleep(20)
            GPIO.output(18,GPIO.LOW)
            GPIO.output(22,GPIO.HIGH)
            sleep(3)
            

        # boxes with non-finite (inf, nan, etc) numbers must be ignored
        if (not np.isfinite(output[base_index]) or
            not np.isfinite(output[base_index + 1]) or
            not np.isfinite(output[base_index + 2]) or
            not np.isfinite(output[base_index + 3]) or
            not np.isfinite(output[base_index + 4]) or
            not np.isfinite(output[base_index + 5]) or
            not np.isfinite(output[base_index + 6])):
            continue

        # extract the image width and height and clip the boxes to the
        # image size in case network returns boxes outside of the image
        # boundaries
        (h, w) = image.shape[:2]
        
        x1 = max(0, int(output[base_index + 3] * w))
        y1 = max(0, int(output[base_index + 4] * h))
        x2 = min(w, int(output[base_index + 5] * w))
        y2 = min(h, int(output[base_index + 6] * h))

        # grab the prediction class label, confidence (i.e., probability),
        # and bounding box (x, y)-coordinates
        #print("pred class",output[base_index + 1])
        pred_class = int(output[base_index + 1])
        pred_conf = output[base_index + 2]
        pred_boxpts = ((x1, y1), (x2, y2))

        # create prediciton tuple and append the prediction to the
        # predictions list
        prediction = (pred_class, pred_conf, pred_boxpts)
        #print (pred_class, pred_conf)
        predictions.append(prediction)
        GPIO.cleanup()


    # return the list of predictions to the calling function
    return predictions

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-g", "--graph", default="mobilenetgraph",
#ap.add_argument("-g", "--graph", default="graphs/mobilenetgraph",
help="path to input graph file")
ap.add_argument("-c", "--confidence", default=.5,
help="confidence threshold")
ap.add_argument("-d", "--display", type=int, default=1,
help="switch to display image on screen")
args = vars(ap.parse_args())

# grab a list of all NCS devices plugged in to USB
#print("[INFO] finding NCS devices...")
devices = mvnc.EnumerateDevices()

# if no devices found, exit the script
if len(devices) == 0:
    print("[INFO] No devices found. Please plug in a NCS")
    quit()

# use the first device since this is a simple test script
# (you'll want to modify this is using multiple NCS devices)
#print("[INFO] found {} devices. device0 will be used. "
#    "opening device0...".format(len(devices)))
device = mvnc.Device(devices[0])
device.OpenDevice()

# open the CNN graph file
#print("[INFO] loading the graph file into RPi memory...")
with open(args["graph"], mode="rb") as f:
    graph_in_memory = f.read()

# load the graph into the NCS
#print("[INFO] allocating the graph on the NCS...")
graph = device.AllocateGraph(graph_in_memory)
# open a pointer to the video stream thread and allow the buffer to
# start to fill, then start the FPS counter
#print("[INFO] starting the video stream and FPS counter...")
vs = VideoStream(usePiCamera=True).start()
time.sleep(1)
fps = FPS().start()
#print("[INFO] creating fifo ")
#input_fifo, output_fifo = graph.allocate_with_fifos(device, graph_in_memory)
#print("[INFO] fifo created")
# loop over frames from the video file stream
while True:
    try:
        # grab the frame from the threaded video stream
        # make a copy of the frame and resize it for display/video purposes
        frame = vs.read() 
        
        #print("[INFO] start predict", frame.shape)
        image_for_result = frame.copy()
        image_for_result = cv2.resize(image_for_result, DISPLAY_DIMS)

        # use the NCS to acquire predictions 
        #print("[INFO] start predict")

        predictions = predict(frame, graph)
        #print("[INFO] success predict")
        # loop over our predictions
        for (i, pred) in enumerate(predictions):
            # extract prediction data for readability
            (pred_class, pred_conf, pred_boxpts) = pred
            #print (pred_class, pred_conf, pred_boxpts)


            if args["display"] > 0:
                # build a label consisting of the predicted class and
                # associated probability
                label = "{}: {:.2f}%".format(CLASSES[pred_class],
                    pred_conf * 100)
                fps.stop()
                cv2.putText(image_for_result, "FPS = {:.2f}".format(fps.fps()), (100,100), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 0), 2)
                # extract information from the prediction boxpoints
                (ptA, ptB) = (pred_boxpts[0], pred_boxpts[1])
                ptA = (ptA[0] * DISP_MULTIPLIER, ptA[1] * DISP_MULTIPLIER)
                ptB = (ptB[0] * DISP_MULTIPLIER, ptB[1] * DISP_MULTIPLIER)
                (startX, startY) = (ptA[0], ptA[1])
                y = startY - 15 if startY - 15 > 15 else startY + 15

                # display the rectangle and label text
                cv2.rectangle(image_for_result, ptA, ptB,
                    COLORS[pred_class], 2)
                cv2.putText(image_for_result, label, (startX, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, COLORS[pred_class], 3)

        # check if we should display the frame on the screen
        # with prediction data (you can achieve faster FPS if you
        # do not output to the screen)
        #if args["display"] > 0:
        #    # display the frame to the screen
        #    cv2.imshow("Output", image_for_result)
        #    key = cv2.waitKey(1) & 0xFF

            # if the `q` key was pressed, break from the loop
        #    if key == ord("q"):
        #        break

        # update the FPS counter
        fps.update()
    
    # if "ctrl+c" is pressed in the terminal, break from the loop
    except KeyboardInterrupt:
        break

    # if there's a problem reading a frame, break gracefully
    except AttributeError:
        break

# stop the FPS counter timer
fps.stop()

# if "ctrl+c" is pressed in the terminal, break from the loop
# destroy all windows if we are displaying them
if args["display"] > 0:
    cv2.destroyAllWindows()

# stop the video stream
#vs.stop()

# clean up the graph and device
graph.DeallocateGraph()
device.CloseDevice()

# display FPS information
print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
