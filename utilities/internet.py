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


########## IMPORT DEPENDENCIES ##########

##### import necessary libraries #####

import os  # import os for file operations
import json  # import json for parsing backend customer_queue payloads
import socket  # import socket for Unix socket communication
import logging  # import logging for debugging
import threading  # import threading for concurrent operations
from queue import Queue  # import Queue for codes queue management

##### import config #####

from utilities.config import INTERNET_CONFIG  # import logging configuration from config module


########## CREATE DEPENDENCIES ##########

##### create global variables #####

SOCK = None  # global socket variable for backend connection, initialized to None
_send_lock = threading.Lock()  # lock for sending data to backend, initialized to a new threading lock





##############################################################
############### INTERNET CONNECTIVITY FUNCTION ###############
##############################################################

########## CONNECT TO BACKEND ##########

def initialize_backend_socket(): # function to connect to backend via socket

    ##### initialize global socket #####

    global SOCK
    logging.debug("(internet.py): Initializing backend socket...\n")
    if not SOCK: # if sock is not already initialized...
        SOCK = socket.socket() # create a new socket object

        try:
            SOCK.connect((INTERNET_CONFIG['BACKEND_PUBLIC_IP'], INTERNET_CONFIG['BACKEND_PORT']))
            logging.info("(internet.py): Connected to website backend.\n")
            return SOCK

        except Exception as e:
            logging.error(f"(internet.py): Failed to connect to website backend: {e}\n")
            SOCK = None
            return None


########## PARSE CUSTOMER QUEUE PAYLOAD FROM BACKEND ##########

def parse_customer_queue_command(command):  # extract email and purchase code from one queue entry

    ##### match wire format from Frontend paymentCode.js + Backend /api/robot-command #####

    # frontend POSTs command = JSON.stringify({ type: "customer_queue", email, code }).
    # backend sends that same UTF-8 string length-prefixed over TCP; listen_for_commands()
    # decodes bytes and puts the string on the queue unchanged.

    if command is None:
        return None, None

    if isinstance(command, (bytes, bytearray)):
        try:
            command = command.decode("utf-8")
        except Exception:
            return None, None

    if not isinstance(command, str):
        return None, None

    text = command.strip()
    if not text.startswith("{"):
        return None, None

    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None, None

    if not isinstance(obj, dict) or obj.get("type") != "customer_queue":
        return None, None

    raw_email = obj.get("email")
    raw_code = obj.get("code")

    if raw_code is None:
        return None, None

    email = "" if raw_email is None else str(raw_email).strip()
    code = str(raw_code).strip()

    if not code or not code.isdigit():
        return None, None

    return email, code


########## STREAM FRAME DATA TO BACKEND ##########

def stream_to_backend(socket_param, frame_data): # function to send frame data to backend

    ##### send frame data to backend #####

    global SOCK
    if frame_data is not None and socket_param is not None: # if there is frame data and a socket connection...
        #logging.debug("(internet.py): Streaming frame data to website backend...\n")

        try: # attempt to send frame data to backend
            with _send_lock:
                frame_length = len(frame_data) # send frame length (4 bytes)
                socket_param.sendall(frame_length.to_bytes(4, 'big'))
                socket_param.sendall(frame_data) # send frame data
                #logging.debug(
                    #f"(internet.py); Frame data sent to website backend successfully of size: {frame_length} bytes\n"
                #)

        except Exception as e: # if unable to send data...
            logging.error(f"(internet.py): Error sending data to website backend: {e}\n")

            try: # attempt to reconnect
                socket_param.close()
                SOCK = None
                SOCK = initialize_backend_socket()
            except Exception as reconnect_error:
                logging.error(f"(internet.py): Failed to reconnect: {reconnect_error}\n")

    else: # if no frame data or no socket connection...
        if frame_data is None:
            logging.debug("(internet.py): No frame data to send.\n")
            pass
        if socket_param is None:
            logging.warning("(internet.py): No socket connection to EC2.\n")


########## INITIALIZE COMMAND QUEUE ##########

def initialize_command_queue(local_sock): # function to create a codes queue for receiving commands from backend

    logging.debug("(internet.py): Initializing codes queue...\n") # log initialization of codes queue

    if local_sock is None:
        logging.error("(internet.py): No website backend socket—codes queue not started.\n")
        return None

    try:
        command_queue = Queue() # create a new codes queue
        threading.Thread(target=listen_for_commands, args=(local_sock, command_queue), daemon=True).start()
        logging.info("(internet.py): Command queue initialized successfully.\n")
        return command_queue # return the codes queue for further processing

    except Exception as e:
        logging.error(f"(internet.py): Failed to initialize codes queue: {e}\n")
        return None


########## RECEIVE COMMANDS FROM BACKEND ##########

def listen_for_commands(local_sock, command_queue):

    logging.debug("(internet.py): Listening for commands from website backend...\n")

    while True:
        try:
            length_bytes = local_sock.recv(4)
            #logging.debug(f"(internet.py): Received length_bytes: {length_bytes}\n")
            if not length_bytes:
                logging.warning("(internet.py): Socket closed or no data received for length. Exiting thread.\n")
                break
            length = int.from_bytes(length_bytes, 'big')
            command_bytes = b''
            while len(command_bytes) < length:
                chunk = local_sock.recv(length - len(command_bytes))
                if not chunk:
                    logging.warning("(internet.py): Socket closed while reading codes. Exiting thread.\n")
                    break
                command_bytes += chunk
            if len(command_bytes) < length:
                break
            command = command_bytes.decode()
            command_queue.put(command)
            logging.debug(f"(internet.py): Received codes: {command}\n")
        except Exception as e:
            logging.error(f"(internet.py): Error receiving codes from website backend: {e}\n")
            break
        finally:
            logging.warning("(internet.py): Encountering thread issues (thread exiting)!\n")
            try:
                # TODO this is a really shitty way to solve this problem, I need to see if the thread issue is caused by
                # TODO some kind of camera overflow, an unstable internet connection, or something else
                pass
                #os.system("sudo systemctl restart robot_dog.service")
            except Exception as e:
                pass
                #logging.error(f"(internet.py): Failed to restart robot_dog service: {e}\n")
            pass
