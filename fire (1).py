import time
import sys
import ibmiotf.application
import ibmiotf.device
import random
import cv2
import numpy as np
import datetime
import ibm_boto3
from ibm_botocore.client import Config, ClientError

#video_file = "video_1.mp4"
video = cv2.VideoCapture(0)

# Constants for IBM COS values
COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud" # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
COS_API_KEY_ID = "Gs6ghV8IKMnc7EihhpZkzSCA8mhdSmTtOPdeD9UFLtci" # eg "W00YiRnLW4a3fTjMB-odB-2ySfTrFBIQQWanc--P3byk"
COS_AUTH_ENDPOINT = "https://iam.cloud.ibm.com/identity/token"
COS_RESOURCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/e007d39ad52b49169bf1cfa7093898ac:f94c35e9-f988-4d3a-971a-5bd7e91b649e::" # eg "crn:v1:bluemix:public:cloud-object-storage:global:a/3bf0d9003abfb5d29761c3e97696b71c:d6f04d83-6c4f-4a62-a165-696756d63903::"


# Create resource
cos = ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_RESOURCE_CRN,
    ibm_auth_endpoint=COS_AUTH_ENDPOINT,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)

#Provide your IBM Watson Device Credentials
organization = "qmudqf"
deviceType = "rasberrypidevice"
deviceId = "0987654321"
authMethod = "token"
authToken = "ssk_E6h+F6vk+MsUoJ"



# Initialize GPIO

def myCommandCallback(cmd):
        print("Command received: %s" % cmd.data)
        

try:
	deviceOptions = {"org": organization, "type": deviceType, "id": deviceId, "auth-method": authMethod, "auth-token": authToken}
	deviceCli = ibmiotf.device.Client(deviceOptions)
	#..............................................
	
except Exception as e:
	print("Caught exception connecting device: %s" % str(e))
	sys.exit()

# Connect and send a datapoint "hello" with value "world" into the cloud as an event of type "greeting" 10 times
deviceCli.connect()

def multi_part_upload(bucket_name, item_name, file_path):
    try:
        print("Starting file transfer for {0} to bucket: {1}\n".format(item_name, bucket_name))
        # set 5 MB chunks
        part_size = 1024 * 1024 * 5

        # set threadhold to 15 MB
        file_threshold = 1024 * 1024 * 15

        # set the transfer threshold and chunk size
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )

        # the upload_fileobj method will automatically execute a multi-part upload
        # in 5 MB chunks for all files over 15 MB
        with open(file_path, "rb") as file_data:
            cos.Object(bucket_name, item_name).upload_fileobj(
                Fileobj=file_data,
                Config=transfer_config
            )

        print("Transfer for {0} Complete!\n".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to complete multi-part upload: {0}".format(e))


while True:
    hum=random.randint(10,50)
    #print(hum)
    temp =random.randint(30,80)
    gas=random.randint(40,150)
    #Send Temperature & Humidity to IBM Watson
    data = { 'Temperature' : temp, 'Humidity': hum , 'Gas_threshold': gas}
    #print (data)
    def myOnPublishCallback():
        print ("Published Temperature = %s C" % temp, "Humidity = %s %%" % hum, "Gas_quantity = %s ug "%gas, "to IBM Watson")

    success = deviceCli.publishEvent("DHT11", "json", data, qos=0, on_publish=myOnPublishCallback)
    if not success:
        print("Not connected to IoTF")
    time.sleep(2)
        
    deviceCli.commandCallback = myCommandCallback

    (grabbed, frame) = video.read()
    if not grabbed:
        break
 
    blur = cv2.GaussianBlur(frame, (21, 21), 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
 
    lower = [18, 50, 50]
    upper = [35, 255, 255]
    lower = np.array(lower, dtype="uint8")
    upper = np.array(upper, dtype="uint8")
    mask = cv2.inRange(hsv, lower, upper)
    
 
 
    output = cv2.bitwise_and(frame, hsv, mask=mask)
    no_red = cv2.countNonZero(mask)
    cv2.imshow("output", output)
    #print("output:", frame)
    if ((int(no_red) > 20000)|(temp>=70)|(gas>=80)):
        print ('Fire detected')
        print ('Switch ON the Fan & Sprinkler')
    else:
        print ('Fire not detected')
    #capture the first frame
    check,frame=video.read()
    gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #drawing rectangle boundries for the detected fire
    cv2.imshow('Fire detection', frame)
    global picname
    picname=datetime.datetime.now().strftime("%y-%m-%d-%H-%M")
    cv2.imwrite(picname+".jpg",frame)
    multi_part_upload("jjoshuu1","mypic1.jpg",picname+".jpg")
        
    #print(int(no_red))
   #print("output:".format(mask))
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
 
cv2.destroyAllWindows()
video.release()

# Disconnect the device and application from the cloud
deviceCli.disconnect()


        
        



 



