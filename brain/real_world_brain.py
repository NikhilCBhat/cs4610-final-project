import sys
sys.path.append('/home/sloshymarcos111/.local/lib/python2.7/site-packages')
import cv2
from cv2 import aruco
import numpy as np
from mBot import *

#     Note: The OpenCV code is based off of the OpenCV tutorials
#     that are linked in the README

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_50)
parameters = aruco.DetectorParameters_create()

target_ids = [5, 4, 3, 2, 1, 0]  # aruco marker ID list  

def get_center(corner):
    return np.mean(corner[0], axis=0)


def get_distance(p1, p2):
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]

    return np.sqrt(dx ** 2 + dy ** 2)


def get_size(corner):
    corner = corner[0]
    return max(get_distance(corner[0], corner[2]), get_distance(corner[1], corner[3]))


def detect_markers(frame):
    corners, ids, _ = aruco.detectMarkers(image=frame, dictionary=aruco_dict, parameters=parameters)

    frame = aruco.drawDetectedMarkers(frame, corners, ids)
    cv2.imshow('frame', frame)

    if not corners:
        return None

    else:
        return {
            id[0]: [get_center(corner), get_size(corner)] for id, corner in zip(ids, corners)
        }


# def detected_target_id(target):

turning_flag = False
straight_flag = False

# 0 = turning
# 1 = go straight
bot_state = 0

if __name__ == "__main__":

    bot = mBot()
    bot.startWithSerial("/dev/ttyUSB0")  # connection to mBot Ranger via serial

    vid = cv2.VideoCapture('https://192.168.1.54:8080/video')  # replace with IP camera url with '/video' attached
    width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
    while (True):
        if len(target_ids) is 0:
            print("END")
            bot.doMove(0, 0)
            bot.doRGBLedOnBoard(1, 0, 255, 0)
            break

        ret, frame = vid.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # converts image to grayscale
        id_to_marker_info = detect_markers(gray)

        if not id_to_marker_info:
            bot.doMove(-100, 100)
            continue

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        target = target_ids[-1]

        # If we have hit the marker pop and change into turning mode
        if target in id_to_marker_info:
            diagonal = id_to_marker_info[target][1]

            if diagonal > 275:
                print ("\n======================")
                print ("POP HERE" + str(target_ids.pop()))
                print ("\n======================")
                turning_flag = True

		# if the target id has not been detected, then turn to find
        if target not in id_to_marker_info:
            bot.doMove(-100, 100)
            print("TURNING TO FIND MARKER")
            continue

		# get aruco center horizontal coordinate
        id_x = id_to_marker_info[target][0][0]

		# get aruco center to center of frame distance
        markerPixelDist = id_x - (width / 2)

		# if aruco center is within threshold, continue straight	
        if bot_state == 1:
            bot.doMove(100, 100)

        if -20 < markerPixelDist and markerPixelDist < 20:
            bot_state = 1
            bot.doMove(100, 100)
            print("GOING FORWARDS")
            continue
		
		# if aruco center is to left of center frame, turn left
        if markerPixelDist < -80:
            bot_state = 0
            bot.doMove(100, -100)
            print("TURNING LEFT TO CENTER")
            continue

		# if aruco center is to right of center frame, turn right
        if markerPixelDist > 80:
            bot_state = 0
            bot.doMove(-100, 100)
            print("TURNING RIGHT TO CENTER")
            continue

    vid.release()
    print ("EXIT PROGRAM")
    quit()

