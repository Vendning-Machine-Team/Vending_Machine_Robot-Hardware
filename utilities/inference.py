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

##### import config #####

import utilities.config as config

##### import necessary libraries #####

import numpy as np # import NumPy for array manipulation
import logging # import logging for logging messages

##### get physical robot dependencies #####

from openvino import Core  # import OpenVINO runtime
import cv2 # import OpenCV for image processing

########## CREATE DEPENDENCIES ##########

##### all commands #####

# used to encode commands as a fixed-length vector
ALL_COMMANDS = ['a', 'd', 's', 'w', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright']





###################################################
############### INFERENCE FUNCTIONS ###############
###################################################


########## LOAD AND COMPILE MODEL ##########

def load_and_compile_model( # function to load and compile an OpenVINO model
        model_path, # path to the model file
        device_name=config.INFERENCE_CONFIG['TPU_NAME'] # device name for inference (e.g., "CPU", "GPU", "MYRIAD")
):

    ##### clean up OpenCV windows from last run #####

    try: # try to destroy any lingering OpenCV windows from previous runs
        cv2.destroyAllWindows()
        logging.info("(inference.py): Closed lingering OpenCV windows.\n")

    except Exception as e:
        logging.warning(f"(inference.py): Failed to destroy OpenCV windows: {e}\n")

    ##### compile model #####

    logging.debug("(inference.py): Loading and compiling model...\n")

    try: # try to load and compile the model

        ie = Core() # check for devices
        #model_bin_path = model_path.replace(".xml", ".bin") # get binary path from XML path (incase needed)
        model = ie.read_model(model=model_path) # read model from XML file
        compiled_model = ie.compile_model(model, device_name=device_name) # compile model for specified device
        input_layer = compiled_model.input(0) # get input layer of compiled model
        output_layer = compiled_model.output(0) # get output layer of compiled model
        logging.info(f"(inference.py): Model loaded and compiled on {device_name}.\n")
        logging.debug(f"(inference.py): Model input shape: {input_layer.shape}\n")

        try: # try to test model with dummy input

            test_with_dummy_input(compiled_model, input_layer, output_layer) # test model with dummy input
        except Exception as e: # if dummy input test fails...
            logging.warning(f"(inference.py): Dummy input test failed: {e}\n")
            return None, None, None

        return compiled_model, input_layer, output_layer

    except Exception as e:
        logging.error(f"(inference.py): Failed to load/compile model: {e}\n")
        return None, None, None


########## LOAD AND COMPILE ONNX MODEL ##########

def load_and_compile_onnx_model( # function to load and compile model
        model_path, # path to the ONNX model file
        device_name=config.INFERENCE_CONFIG['TPU_NAME'] # device name for inference (e.g., "CPU", "GPU", "MYRIAD")
):
    
    logging.debug(f"(inference.py): Loading and compiling ONNX model: {model_path}\n")

    try: # try to load and compile the ONNX model

        ie = Core() # import runtime
        model = ie.read_model(model=model_path) # load the model
        compiled_model = ie.compile_model(model, device_name=device_name) # compile the model for the specified device
        input_layer = compiled_model.input(0) # get input and output layers
        output_layer = compiled_model.output(0) # get input and output layers
        
        logging.info(f"(inference.py): ONNX model loaded and compiled on {device_name}.\n")

        try: # attempt to run with dummy input
            test_with_dummy_input(compiled_model, input_layer, output_layer)
            logging.info(f"(inference.py): ONNX model dummy input test passed.\n")

        except Exception as e: # if dummy input test fails...
            logging.warning(f"(inference.py): ONNX model dummy input test failed: {e}\n")
        
        return compiled_model, input_layer, output_layer # return compiled model and layers (some models may still work)

    except Exception as e: # if loading/compiling fails...
        logging.error(f"(inference.py): Failed to load/compile ONNX model: {e}\n")
        return None, None, None


########## TEST MODEL ##########

def test_with_dummy_input(compiled_model, input_layer, output_layer): # function to test the model with a dummy input

    ##### check if model/layers are properly initialized #####

    logging.debug("(inference.py): Testing model with dummy input...\n")

    # if model/layers not properly initialized...
    if compiled_model is None or input_layer is None or output_layer is None:
        logging.error("(inference.py): Model is not properly initialized.\n")
        return

    ##### run dummy input through the model #####

    try: # try to run a dummy input through the model

        dummy_input_shape = input_layer.shape # get the shape of the input layer
        dummy_input = np.ones(dummy_input_shape, dtype=np.float32) # create a dummy input with ones
        _ = compiled_model([dummy_input])[output_layer] # run the model but don't use output
        logging.info("(inference.py): Dummy input test passed.\n")

    except Exception as e:
        logging.error(f"(inference.py): Dummy input test failed: {e}\n")


########## RUN PERSON DETECTION CNN MODEL AND SHOW FRAME ##########

def run_person_detection(compiled_model, input_layer, output_layer, frame, run_inference):

    if frame is None:
        logging.debug("(inference.py): Frame is None.\n")
        return False, 0, 0  # return no detection and zero box data — caller must unpack all three values

    try:
        if not run_inference:

            logging.debug("(inference.py): Not running inference, passing...\n")
            #cv2.imshow("video (standard)", frame)
            #cv2.waitKey(1)
            return False, 0, 0  # inference is disabled — return no detection and zero box data

        person_detected = False

        if compiled_model is not None and input_layer is not None and output_layer is not None:

            logging.debug("(inference.py): Running inference...\n")
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            input_blob = cv2.resize(frame_rgb, (256, 256)).transpose(2, 0, 1)
            input_blob = np.expand_dims(input_blob, axis=0).astype(np.float32)
            results = compiled_model([input_blob])[output_layer]

            # initialize largest-box tracking variables before scanning all detections
            # these will be updated as we loop through every detected person this frame
            # the largest box corresponds to the closest / most prominent person in view
            largest_box_area = 0  # running maximum bounding box area (px²) seen this frame
            target_cx = 0         # horizontal pixel center of the largest box found so far

            logging.debug("(inference.py): Scanning all detections for largest person box...\n")

            for detection in results[0][0]:
                confidence = detection[2]
                if confidence > 0.5:
                    person_detected = True
                    xmin, ymin, xmax, ymax = map(
                        int, detection[3:7] * [
                            frame.shape[1], frame.shape[0],
                            frame.shape[1], frame.shape[0]
                        ]
                    )

                    # compute the area of this detection's bounding box in pixels squared
                    # area is used as a camera-based distance proxy in control_logic.py —
                    # the larger the box, the closer the person is to the robot
                    box_area = (xmax - xmin) * (ymax - ymin)

                    # if this detection is the largest box seen so far this frame,
                    # update the target values — the robot will approach this person
                    # and ignore all smaller (farther) detections
                    if box_area > largest_box_area:
                        largest_box_area = box_area
                        target_cx = (xmin + xmax) // 2  # horizontal pixel center of this box
                        logging.debug(
                            f"(inference.py): New largest box — "
                            f"area={box_area}px², center_x={target_cx}px, "
                            f"confidence={confidence:.2f}, "
                            f"bbox=({xmin},{ymin},{xmax},{ymax}).\n"
                        )

                    label = f"ID {int(detection[1])}: {confidence:.2f}"
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        label,
                        (xmin, ymin - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2
                    )

            logging.debug("(inference.py): Inference complete.\n")
            logging.debug(
                f"(inference.py): Frame result — "
                f"person_detected={person_detected}, "
                f"largest_box_area={largest_box_area}px², "
                f"target_cx={target_cx}px.\n"
            )
            #cv2.imshow("video (inference)", frame)
            #cv2.waitKey(1)

        else:
            logging.warning("(inference.py): Inference requested but model is not loaded.\n")

        # return all three values so control_logic.py can make both the stop decision
        # (from largest_box_area) and the steering decision (from target_cx)
        return person_detected, target_cx, largest_box_area

    except Exception as e:
        logging.error(f"(inference.py): Inference error: {e}\n")
        return False, 0, 0  # on any exception return safe defaults — caller always unpacks three values