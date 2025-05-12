#Import the Open-CV extra functionalities
import cv2
import os
import time 
from picamera2 import Picamera2
from gpiozero import AngularServo
from flask import Flask, Response

servo =AngularServo(12, initial_angle=0, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)

app = Flask(__name__)

# find user
users  = []
users.append(os.getlogin())


#This is to pull the information about what each object is called
classNames = []
classFile = "/home/" + users[0] + "/Desktop/Object_Detection_Files/coco.names"
with open(classFile,"rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

#This is to pull the information about what each object should look like
configPath = "/home/"+ users[0] + "/Desktop/Object_Detection_Files/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "/home/"+ users[0] + "/Desktop/Object_Detection_Files/frozen_inference_graph.pb"

#This is some set up values to get good results
net = cv2.dnn_DetectionModel(weightsPath,configPath)
net.setInputSize(320,320)
net.setInputScale(1.0/ 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

#This is to set up what the drawn box size/colour is and the font/size/colour of the name tag and confidence label   
def getObjects(flag,img, thres, nms, draw=True, objects=[]):
    classIds, confs, bbox = net.detect(img,confThreshold=thres,nmsThreshold=nms)
#Below has been commented out, if you want to print each sighting of an object to the console you can uncomment below     
#print(classIds,bbox)
    if len(objects) == 0: objects = classNames
    objectInfo =[]
    if len(classIds) != 0:
        for classId, confidence,box in zip(classIds.flatten(),confs.flatten(),bbox):
            className = classNames[classId - 1]
            if className in objects: 
                objectInfo.append([box,className])
                if (draw):
                    cv2.rectangle(img,box,color=(0,255,0),thickness=2)
                    cv2.putText(img,classNames[classId-1].upper(),(box[0]+10,box[1]+30),
                    cv2.FONT_HERSHEY_COMPLEX,1,(0,255,0),2)
                    cv2.putText(img,str(round(confidence*100,2)),(box[0]+200,box[1]+30),
                    cv2.FONT_HERSHEY_COMPLEX,1,(0,255,0),2)
                    
                    servo.angle = 90
                    time.sleep = 5
                    flag = 0
                    
                    
    
    return img,objectInfo,flag

def generate_frames():
    while True:
        frame = picam2.capture_array()
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
Actual_Time = time.strftime("%I:%M:%S")
servo.angle = 0
print(Actual_Time)
# GET AN IMAGE from Pi camera
img = picam2.capture_array("main")
img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
#Below provides a huge amount of controll. the 0.45 number is the threshold number, the 0.2 number is the nms number)
if ((Actual_Time > Set_Alarm) and flag == 1):
    result, objectInfo, flag = getObjects(flag,img,0.45,0.2,objects=['dog'])
#print(objectInfo)
cv2.imshow("Output",img)
    
            



#Below determines the size of the live feed window that will be displayed on the Raspberry Pi OS
if __name__ == "__main__":
    # start Pi camera
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
    picam2.start()
    Set_Alarm = input("H:M:S:")
    flag = 1
    app.run(host='0.0.0.0', port=5000)
   