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

import time # import time for servo movement
import logging # import logging for debugging

##### import config #####

import utilities.config as config # imports utilities/config.py; binds to `config` — all PERSON_APPROACH_CONFIG values (FRAME_WIDTH, STOP_AREA, etc.) live there

##### import necessary movement functions #####

from behaviors.mecanum import * # wildcard-imports arc_left(), arc_right(), forward(), drive() from behaviors/mecanum.py into scope
from utilities.motors import stop_all # imports stop_all() from utilities/motors.py — writes PWM duty 0 to every GPIO motor pin via pigpio




###################################################
############### APPROACH A CUSTOMER ###############
###################################################


########## PERSON APPROACH FUNCTION ##########

##### steer robot toward the largest detected person in the camera frame #####

def approach_largest_person(target_cx,        # PARAM: horizontal pixel center of the largest detected person bounding box
                             largest_box_area): # PARAM: bounding box area in px²; used as camera-based distance proxy (bigger = closer)
    """
    Issues a single motor command each frame to steer the robot toward
    the largest detected person visible in the camera frame.

    This function is called every frame while PERSON_STATE_MOVING is True
    and a person is currently visible. The existing debounce state machine in
    _physical_loop() controls WHEN the robot starts and stops moving — this
    function controls WHERE the robot steers while it is already moving.

    Two values derived from the OpenVINO bounding box drive this logic:
      - largest_box_area (px²): used as a camera-based distance proxy.
                                 bigger box = person is closer to the robot.
      - target_cx (px):         horizontal pixel center of the largest box.
                                 compared against the frame center to decide
                                 whether to steer left, right, or go straight.

    Motor functions used (all already imported from mecanum.py / motors.py):
      - arc_left()  : curves forward-left using mecanum wheel mixing via drive()
      - arc_right() : curves forward-right using mecanum wheel mixing via drive()
      - forward()   : drives all four wheels straight forward
      - stop_all()  : zeros PWM duty on all GPIO motor pins via pigpio
    """

    # find the horizontal center of the camera frame in pixels
    # everything left of this point has a negative offset, right has a positive offset
    frame_center_x = config.PERSON_APPROACH_CONFIG['FRAME_WIDTH'] // 2 # reads FRAME_WIDTH from config, integer-divides by 2 → midpoint pixel of camera frame (e.g. 640 → 320)

    # compute how far left or right the detected person is from the frame center
    # negative offset = person is left of center  then robot needs to arc left
    # positive offset = person is right of center then robot needs to arc right
    # near-zero offset = person is centered       then robot drives straight forward
    offset = target_cx - frame_center_x # subtracts frame_center_x from target_cx → signed horizontal error in px; negative=left of center, positive=right of center

    logging.debug( # logs: function entry, box_area in px², target_cx, frame_center, signed offset (:+d forces sign prefix); \n adds blank line for log readability
        f"(control_logic.py): approach_largest_person called — "
        f"box_area={largest_box_area}px², "
        f"target_cx={target_cx}px, "
        f"frame_center={frame_center_x}px, "
        f"offset={offset:+d}px.\n"
    )

    if largest_box_area >= config.PERSON_APPROACH_CONFIG['STOP_AREA']: # reads STOP_AREA from config; box area AT OR ABOVE threshold → person is close enough, enter hard-stop branch

        # the person's bounding box has exceeded the hard stop threshold —
        # they are close enough to the robot, halt all four motors immediately
        # stop_all() writes duty cycle 0 to every GPIO motor pin via pigpio
        stop_all() # writes PWM duty 0 to all four GPIO motor pins via pigpio daemon — immediately halts all wheel motion
        logging.debug( # logs STOP decision: current box_area and the STOP_AREA threshold value that triggered it
            f"(control_logic.py): STOP — person is close enough. "
            f"box_area={largest_box_area}px² >= APPROACH_STOP_AREA={config.PERSON_APPROACH_CONFIG['STOP_AREA']}px². "
            f"All motors stopped.\n"
        )

    elif largest_box_area >= config.PERSON_APPROACH_CONFIG['SLOWDOWN_AREA']: # reads SLOWDOWN_AREA from config; box area below STOP_AREA but AT OR ABOVE SLOWDOWN_AREA → reduce speed, keep steering

        # the person's box has entered the slowdown zone but not yet hit the hard stop —
        # reduce intensity to APPROACH_SLOW_INTENSITY so the robot bleeds off speed
        # and has minimal momentum when stop_all() fires on the next threshold crossing
        # steering logic (left/right/forward) still applies at the reduced intensity
        if offset < -config.PERSON_APPROACH_CONFIG['DEADBAND']: # reads DEADBAND from config; offset more negative than −DEADBAND → person is LEFT of center beyond tolerance zone
            arc_left(forward_strength=1.0, turn_strength=0.4, intensity=config.PERSON_APPROACH_CONFIG['SLOW_INTENSITY']) # calls drive(x=0, y=1.0, r=-0.4) in mecanum.py; SLOW_INTENSITY scales PWM down; curves forward-left at reduced speed
        elif offset > config.PERSON_APPROACH_CONFIG['DEADBAND']: # reads DEADBAND from config; offset more positive than +DEADBAND → person is RIGHT of center beyond tolerance zone
            arc_right(forward_strength=1.0, turn_strength=0.4, intensity=config.PERSON_APPROACH_CONFIG['SLOW_INTENSITY']) # calls drive(x=0, y=1.0, r=+0.4) in mecanum.py; SLOW_INTENSITY scales PWM down; curves forward-right at reduced speed
        else: # offset within ±DEADBAND → person is centered; drive straight at reduced speed
            forward(config.PERSON_APPROACH_CONFIG['SLOW_INTENSITY']) # FL/BL counterclockwise, FR/BR clockwise via move_motor(); SLOW_INTENSITY is the reduced speed scalar
        logging.debug( # logs SLOWDOWN decision: current box_area, SLOWDOWN_AREA threshold, SLOW_INTENSITY applied, and signed offset
            f"(control_logic.py): SLOWDOWN — entering stop zone. "
            f"box_area={largest_box_area}px² >= APPROACH_SLOWDOWN_AREA={config.PERSON_APPROACH_CONFIG['SLOWDOWN_AREA']}px². "
            f"Reduced intensity to {config.PERSON_APPROACH_CONFIG['SLOW_INTENSITY']}, offset={offset:+d}px.\n"
        )

    elif offset < -config.PERSON_APPROACH_CONFIG['DEADBAND']: # box area below both thresholds (far from robot); person is LEFT of center beyond deadband → arc left at full INTENSITY

        # person is to the LEFT of center beyond the deadband —
        # arc_left() calls drive(x=0, y=forward_strength, r=-turn_strength)
        # which mixes the four mecanum wheels to curve the robot forward-left
        # this steers the robot's heading toward the person without stopping forward motion
        arc_left(forward_strength=1.0, turn_strength=0.4, intensity=config.PERSON_APPROACH_CONFIG['INTENSITY']) # drive(x=0, y=1.0, r=-0.4); full INTENSITY; steers robot heading left toward person
        logging.debug( # logs ARC LEFT decision: signed pixel offset, deadband threshold, and current full INTENSITY
            f"(control_logic.py): ARC LEFT — person is left of center. "
            f"offset={offset:+d}px, deadband={config.PERSON_APPROACH_CONFIG['DEADBAND']}px, "
            f"intensity={config.PERSON_APPROACH_CONFIG['INTENSITY']}.\n"
        )

    elif offset > config.PERSON_APPROACH_CONFIG['DEADBAND']: # box area below both thresholds; offset NOT left of center; person is RIGHT of center beyond deadband → arc right at full INTENSITY

        # person is to the RIGHT of center beyond the deadband —
        # arc_right() calls drive(x=0, y=forward_strength, r=+turn_strength)
        # which mixes the four mecanum wheels to curve the robot forward-right
        arc_right(forward_strength=1.0, turn_strength=0.4, intensity=config.PERSON_APPROACH_CONFIG['INTENSITY']) # drive(x=0, y=1.0, r=+0.4); full INTENSITY; steers robot heading right toward person
        logging.debug( # logs ARC RIGHT decision: signed pixel offset, deadband threshold, and current full INTENSITY
            f"(control_logic.py): ARC RIGHT — person is right of center. "
            f"offset={offset:+d}px, deadband={config.PERSON_APPROACH_CONFIG['DEADBAND']}px, "
            f"intensity={config.PERSON_APPROACH_CONFIG['INTENSITY']}.\n"
        )

    else: # offset within ±DEADBAND and box area below both thresholds → person is centered; drive straight at full INTENSITY

        # person is within the deadband of the frame center —
        # drive all four wheels straight forward at approach intensity
        # forward() sets FL/BL counterclockwise and FR/BR clockwise via move_motor()
        forward(config.PERSON_APPROACH_CONFIG['INTENSITY']) # FL/BL counterclockwise, FR/BR clockwise via move_motor(); full INTENSITY speed scalar; no steering correction needed
        logging.debug( # logs FORWARD decision: signed pixel offset, deadband window, and current full INTENSITY
            f"(control_logic.py): FORWARD — person is centered. "
            f"offset={offset:+d}px within deadband={config.PERSON_APPROACH_CONFIG['DEADBAND']}px, "
            f"intensity={config.PERSON_APPROACH_CONFIG['INTENSITY']}.\n"
        )




###################################################
############### FIND A NEW CUSTOMER ###############
###################################################



#TODO Henry works here
########## FIND CUSTOMER FUNCTION ##########

def find_customer():

    # step 1. rotate some random angle (180 degrees ± 90 degrees)
    

    # step 2. move in some direction until person is detected


    # step 3. lock onto person (basically the function above)

    pass

def force_sale():

    # step 1. rotate towards the same person (if they dont run away)


    # step 2. move in some direction until person is detected


    # step 3. lock onto person (basically the function above)

    pass
