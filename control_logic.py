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

from behaviors.mecanum import *
from utilities.motors import initialize_motor_controllers, stop_all, run_back_motors

##### customer tracking functions #####

from behaviors.customer_finder import approach_largest_person, force_sale, find_customer
import behaviors.customer_finder as customer_finder
from behaviors.proximity import check_distance_from_home, return_to_home

##### sale functions #####

from behaviors.sale import handle_sale

##### screen functions #####

from utilities.screen import render_qr_frame

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

SALE_IN_PROGRESS = False # boolean that tracks if a sale is in progress always starts as False until proven otherwise
OUT_OF_RANGE = False  # boolean that tracks if robot is out of range of home coordinates always starts as False until proven otherwise

##### person detection variables #####

PERSON_DETECTED_STREAK = 0  # consecutive frames with person_detected == True
PERSON_ABSENT_STREAK = 0  # consecutive frames with person_detected == False
PERSON_STATE_MOVING = False  # whether motors are currently commanded to move
PERSON_LAST_STATE_CHANGE_TIME = 0.0  # used to enforce minimum move time
PERSON_LAST_DETECTED_TIME = 0.0  # tracks when a person was last positively detected
ROBOT_IN_FORCE_SALE = False  # True once approach_largest_person() has stopped the robot close to a person and force_sale() takes over

##### state machine loop #####

def _state_machine():  # central function that runs robot in real life

    ##### set/initialize variables #####

    global SALE_IN_PROGRESS, OUT_OF_RANGE # declare as global as these will be edited by function
    global PERSON_DETECTED_STREAK, PERSON_ABSENT_STREAK
    global PERSON_STATE_MOVING, PERSON_LAST_STATE_CHANGE_TIME, PERSON_LAST_DETECTED_TIME
    global ROBOT_IN_FORCE_SALE
    mjpeg_buffer = b''  # initialize buffer for MJPEG frames
    last_gps_check_time = 0.0 # throttle GPS check threads

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
            #TODO a certain amount of time until either they start a sale, time elapses, or they are out of range. We need to ensure
            #TODO that the robot is not too close to the customer and that they are not too far away, while also making
            #TODO sure that the person remains in frame.

            ##### transition from robot stop to approach customer #####

            # if the robot not currently moving and person has been detected for required num frames...
            if (not PERSON_STATE_MOVING) and (not ROBOT_IN_FORCE_SALE) and (
                PERSON_DETECTED_STREAK >= config.PERSON_DETECTION_CONFIG['DETECTED_FRAMES_TO_START']
            ):

                PERSON_STATE_MOVING = True # set person state to True
                PERSON_LAST_STATE_CHANGE_TIME = now # update last state change time

            ##### transition from robot move to stop #####

            # if the robot is currently moving and person has been absent for required num frames...
            elif PERSON_STATE_MOVING and (not ROBOT_IN_FORCE_SALE) and (
                PERSON_ABSENT_STREAK >= config.PERSON_DETECTION_CONFIG['ABSENT_FRAMES_TO_STOP']
            ):

                enough_move_time = ( # find time since last state change for required time
                    (now - PERSON_LAST_STATE_CHANGE_TIME) >= config.PERSON_DETECTION_CONFIG['MIN_MOVE_SECONDS']
                )

                absent_hold_elapsed = ( # find time since last person was detected for required time
                    (now - PERSON_LAST_DETECTED_TIME) >= config.PERSON_DETECTION_CONFIG['ABSENT_HOLD_SECONDS']
                )

                # if robot has been moving for required time and person has been absent for required time...
                if enough_move_time and absent_hold_elapsed:

                    PERSON_STATE_MOVING = False # set person state to False
                    PERSON_LAST_STATE_CHANGE_TIME = now # update last state change time

            ##### force sale — runs every frame once robot has stopped close to a person #####

            if ROBOT_IN_FORCE_SALE:

                force_sale(person_detected, target_cx, largest_box_area)

                # force_sale() resets _force_sale_start_time to 0.0 when MAX_ENGAGEMENT_SECONDS expires
                # that reset is the signal that this person timed out — spin to find the next customer
                if customer_finder._force_sale_start_time == 0.0:
                    logging.info("(control_logic.py): force_sale timed out — calling find_customer().\n")
                    ROBOT_IN_FORCE_SALE = False
                    PERSON_STATE_MOVING = False
                    find_customer()

            ##### continuous approach steering — runs every frame while moving toward a person #####

            elif PERSON_STATE_MOVING and person_detected:

                logging.info(
                    f"(control_logic.py): Robot is moving and person is visible — "
                    f"steering toward person "
                    f"(target_cx={target_cx}px, box_area={largest_box_area}px²).\n"
                )
                approach_largest_person(target_cx, largest_box_area)

                # once approach_largest_person() stops the robot close enough, hand off to force_sale
                if largest_box_area >= config.PERSON_APPROACH_CONFIG['STOP_AREA']:
                    logging.info("(control_logic.py): Person close enough — entering force_sale.\n")
                    ROBOT_IN_FORCE_SALE = True


            ########## HANDLING A SALE ##########

            #TODO this is logically pretty much done
            #TODO once sam does his part with the sale interface, we can make this chunk its own function and plop it somewhere else

            ##### code received from backend #####

            codes = None # initially no codes

            if CODES_FROM_BACKEND_QUEUE is not None and not CODES_FROM_BACKEND_QUEUE.empty():  # if codes were received...

                codes = CODES_FROM_BACKEND_QUEUE.get() # get one sale payload from queue
                logging.info(f"(control_logic.py): Codes received from backend: {codes}\n")
                SALE_IN_PROGRESS = handle_sale(codes, SALE_IN_PROGRESS)

            ##### render QR idle screen when not in a sale #####

            if not SALE_IN_PROGRESS:
                render_qr_frame()


            ########## FIND A NEW CUSTOMER ##########

            #TODO If a sale is not begun after a certain amount of time (i.e. the robot does not get a code from the backend after
            #TODO a certain amount of time), we need to skip to 'find a new customer'. If a sale has successfully completed, then we
            #TODO need to 'find a new customer'.


            ########## CHECK ROBOT'S RANGE FROM HOME COORDINATES ##########

            #TODO currently not threaded, will keep like this so person tracking does not resume until robot is back in range of home coordinates

            # step 1. every n amount of time (opening a new thread every time and then closing it after checking) check for lat and lon coordinates
            if (time.monotonic() - last_gps_check_time) >= config.GPS_CONFIG['CHECK_INTERVAL_SECONDS']:
                last_gps_check_time = time.monotonic()

                def _gps_check_worker():
                    global OUT_OF_RANGE
                    OUT_OF_RANGE = bool(check_distance_from_home())

                threading.Thread(target=_gps_check_worker, daemon=True).start()

            # step 2. if within acceptable range, do nothing
            if not OUT_OF_RANGE:
                logging.debug(f"(control_logic.py): Robot is within acceptable range of home coordinates.\n")


            # step 3. else outside acceptable range, turn around and move back to home coordinates (this needs to be in the same thread as moving
            # toward or away from the customer so the robot does not get confused; unless a sale is in progress, the robot MUST prioritize going home)
            elif OUT_OF_RANGE and (not SALE_IN_PROGRESS):
                logging.info(f"(control_logic.py): Robot is out of range of home coordinates and no sale is in progress. Turning around and moving back to home coordinates.\n")
                return_to_home()


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
