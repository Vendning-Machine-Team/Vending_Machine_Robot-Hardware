##################################################################################
# Copyright (c) 2026 Vending Machine Robot                                       #
#                                                                                #
# Licensed under the Creative Commons Attribution-NonCommercial 4.0              #
# International (CC BY-NC 4.0). Personal and educational use is permitted.       #
# Commercial use by companies or for-profit entities is prohibited.              #
##################################################################################





############################################################
############### IMPORT / CREATE DEPENDENCIES ###############
############################################################


########## MANDATORY DEPENDENCIES ##########

##### mandatory libraries #####

import threading
import queue
import time
import os
import atexit
import socket
import logging
from collections import deque
import numpy as np
import cv2

##### mandatory dependencies #####

from utilities.log import initialize_logging
import utilities.config as config
import utilities.internet as internet  # dynamically import internet utilities to be constantly updated

##### (pre)initialize all utilities #####

LOGGER = initialize_logging()
CAMERA_PROCESS = None
CHANNEL_DATA = {}
SOCK = None
CODES_FROM_BACKEND_QUEUE = None
ROBOT_ID = None
JOINT_MAP = {}
DETECTION_MODEL = None
DETECTION_INPUT_LAYER = None
DETECTION_OUTPUT_LAYER = None


##### movement functions #####

from movement.mecanum import *
from utilities.motors import initialize_motor_controllers, stop_all, run_back_motors
from movement.customer_interaction import approach_largest_person

#atexit.register(stop_all)

##### import GPS functions #####

from utilities.gps import *


########## PREPARE ROBOT ##########

##### prepare real robot #####

def set_robot_dependencies():  # function to initialize real robot dependencies

    ##### import necessary functions #####

    from utilities.camera import initialize_camera  # import to start camera logic
    import utilities.internet as internet  # dynamically import internet utilities to be constantly updated

    ##### initialize global variables #####

    global CAMERA_PROCESS, SOCK, CODES_FROM_BACKEND_QUEUE, ROBOT_ID, JOINT_MAP, GPS
    global DETECTION_MODEL, DETECTION_INPUT_LAYER, DETECTION_OUTPUT_LAYER

    ##### initialize camera process #####

    CAMERA_PROCESS = initialize_camera()  # create camera process
    if CAMERA_PROCESS is None:
        logging.error("(control_logic.py): Failed to initialize CAMERA_PROCESS for robot!\n")

    ##### initialize socket and codes queue #####

    SOCK = internet.initialize_backend_socket()  # initialize EC2 socket connection
    CODES_FROM_BACKEND_QUEUE = internet.initialize_command_queue(SOCK)  # initialize codes queue for socket communication
    if SOCK is None:
        logging.error("(control_logic.py): Failed to initialize SOCK for robot!\n")
    if CODES_FROM_BACKEND_QUEUE is None:
        logging.error("(control_logic.py): Failed to initialize CODES_FROM_BACKEND_QUEUE for robot!\n")

    ##### initialize SSDLite person detection model #####

    from utilities import inference
    model_path = config.INFERENCE_CONFIG.get('CNN_PATH') or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'model', 'ssdlite_mobilenet_v2.xml'
    )
    if os.path.isfile(model_path):
        DETECTION_MODEL, DETECTION_INPUT_LAYER, DETECTION_OUTPUT_LAYER = inference.load_and_compile_model(model_path)
        if DETECTION_MODEL is None:
            logging.warning("(control_logic.py): SSDLite model failed to load; person detection disabled.\n")
    else:
        logging.warning(f"(control_logic.py): SSDLite model not found at {model_path}; person detection disabled.\n")

    ##### initialize motors #####

    initialize_motor_controllers()

    ##### initialize GPS #####

    GPS = initialize_gps()  # initialize GPS connection

    if GPS is None:
        logging.warning("(control_logic.py): Failed to initialize GPS for robot!\n")
    else:
        logging.info("(control_logic.py): Successfully initialized GPS for robot.\n")


########## PREPARE ROBOT ##########

##### prepare robot with correct dependencies #####

set_robot_dependencies()

##### post-initialization dependencies #####

from utilities.camera import decode_real_frame
from utilities import inference





#########################################
############### RUN ROBOT ###############
#########################################


########## STATE MACHINE LOOPS ##########

##### set global variables #####

MOVEMENT_COMPLETE = True  # boolean that tracks if the robot is done moving, independent of it being neutral or not
SALE_IN_PROGRESS = False  # set global neutral standing boolean

##### person detection variables #####

PERSON_DETECTED_STREAK = 0  # consecutive frames with person_detected == True
PERSON_ABSENT_STREAK = 0  # consecutive frames with person_detected == False
PERSON_STATE_MOVING = False  # whether motors are currently commanded to move
PERSON_LAST_STATE_CHANGE_TIME = 0.0  # used to enforce minimum move time
PERSON_LAST_DETECTED_TIME = 0.0  # tracks when a person was last positively detected


##### state machine loop #####

def _state_machine():  # central function that runs robot in real life

    ##### set/initialize variables #####

    global MOVEMENT_COMPLETE, SALE_IN_PROGRESS # declare as global as these will be edited by function
    global PERSON_DETECTED_STREAK, PERSON_ABSENT_STREAK
    global PERSON_STATE_MOVING, PERSON_LAST_STATE_CHANGE_TIME, PERSON_LAST_DETECTED_TIME
    mjpeg_buffer = b''  # initialize buffer for MJPEG frames

    ##### run robotic logic #####

    SALE_IN_PROGRESS = True  # set is_neutral to True

    ##### stream video, run inference, and control the robot #####

    try:  # try to run main robotic process

        while True:  # central loop to entire process, commenting out of importance

            now = time.time() # get current time for timing calculations


            ########## RUN CAMERA AND INFERENCE ##########

            ##### decode camera frame #####

            # run camera and decode frame (no video stream to backend)
            mjpeg_buffer, _, inference_frame = decode_real_frame(
                CAMERA_PROCESS,
                mjpeg_buffer
            )

            ##### run person detection #####

            person_detected, target_cx, largest_box_area = inference.run_person_detection(
                DETECTION_MODEL, DETECTION_INPUT_LAYER, DETECTION_OUTPUT_LAYER,
                inference_frame, run_inference=True
            )

            ##### show inference frame #####

            if inference_frame is not None:
                cv2.imshow("SSDLite detection", inference_frame)
                cv2.waitKey(1)

            ##### log inference results #####

            logging.debug(
                f"(control_logic.py): Inference unpacked — "
                f"person_detected={person_detected}, "
                f"target_cx={target_cx}px, "
                f"largest_box_area={largest_box_area}px².\n"
            )

            ##### person detected #####

            if person_detected: # if a person is detected...

                PERSON_DETECTED_STREAK += 1 # increment detected streak
                PERSON_ABSENT_STREAK = 0 # reset absent streak
                PERSON_LAST_DETECTED_TIME = now # update last detected time

            else: # if no person is detected...

                PERSON_ABSENT_STREAK += 1 # increment absent streak
                PERSON_DETECTED_STREAK = 0 # reset detected streak


            ########## APPROACHING A CUSTOMER ##########

            #TODO We need to make this be a 'calm' approach: if person detected, roll up to them
            #TODO and eventually stop infront of them to get their attention. The robot will essentially harrass a
            #TODO customer until they start a sale by following them around at a distance and holding that distance for
            #TODO a certain amount of time until either they start a sale or time elapses. We need to ensure
            #TODO that the robot is not too close to the customer and that they are not too far away, while also making
            #TODO sure that the person remains in frame.

            ##### transition from robot stop to approach customer #####

            # if the robot not currently moving and person has been detected for required num frames...
            if (not PERSON_STATE_MOVING) and (
                PERSON_DETECTED_STREAK >= config.PERSON_DETECTION_CONFIG['DETECTED_FRAMES_TO_START']
            ):

                #Threading.thread(target=forward, args=(10), daemon=True).start()
                forward(10) # TODO should I thread this? if so need a variable to track movement completion

                PERSON_STATE_MOVING = True # set person state to True
                PERSON_LAST_STATE_CHANGE_TIME = now # update last state change time

            ##### transition from robot move to stop #####

            # if the robot is currently moving and person has been absent for required num frames...
            elif PERSON_STATE_MOVING and (
                PERSON_ABSENT_STREAK >= config.PERSON_DETECTION_CONFIG['ABSENT_FRAMES_TO_STOP']
            ):

                enough_move_time = ( # find time since last state change for required time
                    (now - PERSON_LAST_STATE_CHANGE_TIME) >= config.PERSON_DETECTION_CONFIG['MIN_MOVE_SECONDS']
                )

                absent_hold_elapsed = ( # find time since last person was detected for required time
                    (now - PERSON_LAST_DETECTED_TIME) >= config.PERSON_DETECTION_CONFIG['ABSENT_HOLD_SECONDS']
                )

                ##### person moves out of frame #####

                # if robot has been moving for required time and person has been absent for required time...
                if enough_move_time and absent_hold_elapsed:

                    #Threading.thread(target=stop_all, daemon=True).start()
                    stop_all() # TODO should I thread this? if so need a variable to track movement completion

                    PERSON_STATE_MOVING = False # set person state to False
                    PERSON_LAST_STATE_CHANGE_TIME = now # update last state change time


            ########## HANDLING A SALE ##########

            #TODO After rolling up to the customer, we need to handle the sale. If after we roll up to them,
            #TODO they are still in the frame, and they dont start a sale, we need to skip to 'find a new customer'.
            #TODO If they start a sale, we need to handle the sale. It is okay to have a sale take place in this
            #TODO same thread, as the roobt inference hanging while waiting for a sale to end is actually a good thing.
            #TODO We don't want the robot to do a 180° and wander off while a sale is in progress.
            #TODO This is also where we cann screen.py functions to display the sale interface.

            codes = None  # initially no codes

            if CODES_FROM_BACKEND_QUEUE is not None and not CODES_FROM_BACKEND_QUEUE.empty():  # if codes queue is not empty...
                codes = CODES_FROM_BACKEND_QUEUE.get()  # get codes from queue
                if codes is not None:
                    if MOVEMENT_COMPLETE:  # if movement is complete, run codes
                        logging.info(f"(control_logic.py): Received codes '{codes}' from queue (WILL RUN).\n")
                    else:
                        logging.info(f"(control_logic.py): Received codes '{codes}' from queue (BLOCKED).\n")

            if codes and MOVEMENT_COMPLETE:  # if codes present and movement complete...
                # logging.debug(f"(control_logic.py): Running codes: {codes}...\n")
                threading.Thread(target=_handle_command, args=(codes), daemon=True).start()

            elif not codes and MOVEMENT_COMPLETE and not SALE_IN_PROGRESS:  # if no codes and move complete and not neutral...
                logging.debug(f"(control_logic.py): No codes received.\n")


            ########## FIND A NEW CUSTOMER ##########

            #TODO If a sale is not begun after a certain amount of time (i.e. the robot does not get a code from the backend after
            #TODO a certain amount of time), we need to skip to 'find a new customer'. If a sale has successfully completed, then we
            #TODO need to 'find a new customer'.


            ########## OCCAISONALLY CHECK FOR LAT AND LON COORDINATES ##########

            #TODO while the robot is following a customer, there is a chance that the robot will
            #TODO wander too far away from the library entrance. We need to check for this and if the robot
            #TODO is too far away from the library entrance, we need to give up the chase and turn around back to the
            #TODO library entrance. To do this, we need to occaisonally check for lat and lon, using those to determine
            #TODO our distance as well as cardinal directions. We need the cardinal directions to determine how we should turn
            #TODO in order to get back to the library entrance. We also need to ignore this if a sale is in progress (i.e. if the
            #TODO robot is slightly out of range but someone is buying something, only turn back to the library entrance if the sale is complete).










            #TODO code below is queue logic I made ages ago plus Tri's code; it's important to learn this code and to then build off of it later.

            # continuous approach steering — runs every frame while the robot is actively
            # moving AND a person is currently visible in the camera frame
            # the debounce state machine above decides WHEN to start or stop moving
            # this block decides WHERE to steer (left, right, forward, or stop) each frame
            # approach_largest_person() uses target_cx and largest_box_area from inference
            # to issue the correct motor command for this frame via mecanum.py
            if PERSON_STATE_MOVING and person_detected:
                logging.info(
                    f"(control_logic.py): Robot is moving and person is visible — "
                    f"steering toward person "
                    f"(target_cx={target_cx}px, box_area={largest_box_area}px²).\n"
                )
                approach_largest_person(target_cx, largest_box_area)


    ########## SHUT DOWN ROBOT ##########

    ##### handle keyboard interrupt #####

    except KeyboardInterrupt:  # if user ends program...
        logging.info("(control_logic.py): KeyboardInterrupt received, exiting.\n")
        stop_all()

    ##### handle unexpected exception #####

    except Exception as e:  # if something breaks and only God knows what it is...
        logging.error(f"(control_logic.py): Unexpected exception in main loop: {e}\n")
        stop_all() # stop all motors
        exit(1)

    ##### stop all motors and close all windows #####

    finally:
        stop_all()
        cv2.destroyAllWindows()


########## MISCELLANEOUS CONTROL FUNCTIONS ##########

def restart_process():  # start background thread to restart robot_dog.service every 30 minutes by checking elapsed time
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed >= 1800:  # 30 minutes = 1800 seconds
            os.system('sudo systemctl restart robot_dog.service')
            start_time = time.time()  # reset timer after restart
        time.sleep(1)  # check every second


########## RUN ROBOTIC PROCESS ##########

restart_thread = threading.Thread(target=restart_process, daemon=True)
restart_thread.start()
# voltage_thread = threading.Thread(target=voltage_monitor, daemon=True)
# voltage_thread.start()
_state_machine()  # run robot process
