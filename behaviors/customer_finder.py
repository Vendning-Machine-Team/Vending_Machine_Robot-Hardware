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

import utilities.config as config # imports utilities/config.py; binds to `config` — all PERSON_APPROACH_CONFIG and FORCE_SALE_CONFIG values live there

##### import necessary movement functions #####

from behaviors.mecanum import * # wildcard-imports arc_left(), arc_right(), forward(), drive() from behaviors/mecanum.py into scope
from utilities.motors import stop_all # imports stop_all() from utilities/motors.py — writes PWM duty 0 to every GPIO motor pin via pigpio




###################################################
############### MODULE-LEVEL STATE ################
###################################################


_last_known_offset = 0 # MODULE-LEVEL INT — stores the signed horizontal pixel distance between the person and frame center from the last frame the person was visible
                        # computed as: target_cx - frame_center_x each frame person_detected=True
                        # negative value = person was last seen LEFT of frame center → force_sale() will rotate_left() to re-acquire
                        # positive value = person was last seen RIGHT of frame center → force_sale() will rotate_right() to re-acquire
                        # zero = person was last seen exactly centered
                        # FROZEN when person_detected=False (State 3) — never updated during blind rotation scan
                        # read by State 1 sub-states to decide sighted re-centering direction
                        # read by State 3 to decide blind rotation scan direction

_force_sale_start_time = 0.0 # MODULE-LEVEL FLOAT — time.monotonic() timestamp recorded exactly once on the first frame force_sale() is called for a given person
                               # 0.0 = sentinel value meaning no active engagement; timer has not started or was just reset after timeout
                               # non-zero = engagement clock is live; total elapsed = time.monotonic() - _force_sale_start_time
                               # set via: if _force_sale_start_time == 0.0: _force_sale_start_time = time.monotonic()
                               # intentionally NEVER reset during State 2 (re-approach) or State 3 (blind rotation) — clock counts total time with this person across ALL states
                               # only reset to 0.0 when timeout fires so the NEXT person gets a completely fresh MAX_ENGAGEMENT_SECONDS window
                               # time.monotonic() used instead of time.time() because monotonic is immune to system clock adjustments (NTP, DST, manual changes)




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
    """
    Called after force_sale() times out on a person (MAX_ENGAGEMENT_SECONDS expired)
    or whenever the robot needs to find a new customer.

    Step 1 — rotate the robot 180° in place using timed rotation.
             rotate_left() is called for SPIN_DURATION seconds at SPIN_INTENSITY
             to achieve approximately 180°. Both values must be tuned on real
             hardware since there is no IMU or encoder feedback — the robot
             cannot verify the actual angle turned.

    Step 2 — hand off to the approach pipeline to find and close in on the next person.
             # TODO: we can either call approach_largest_person() directly in here
             #       or handle the handoff in the driver class — decision TBD pending driver class implementation
    """

    # step 1 — spin 180° in place using timed rotation
    rotate_left(config.FIND_CUSTOMER_CONFIG['SPIN_INTENSITY']) # calls rotate_left() from behaviors/mecanum.py; sets all 4 wheels clockwise to spin the robot body left in place at SPIN_INTENSITY PWM
    time.sleep(config.FIND_CUSTOMER_CONFIG['SPIN_DURATION'])   # holds the spin for SPIN_DURATION seconds; this is the only mechanism for angle control — no IMU available; tune SPIN_DURATION in config until ~180° is achieved on real hardware
    stop_all()                                                  # writes PWM duty 0 to all four GPIO motor pins via pigpio daemon — halts the spin after SPIN_DURATION seconds have elapsed

    # step 2 —
    # TODO: we can either call approach_largest_person() directly in here
    #       or handle the handoff in the driver class — decision TBD pending driver class implementation

def force_sale(person_detected, target_cx, largest_box_area):
    # PARAM: person_detected   — bool; True if the inference model detected at least one person in the current frame
    # PARAM: target_cx         — horizontal pixel center of the largest detected person bounding box (only valid when person_detected=True)
    # PARAM: largest_box_area  — area of the largest detected person bounding box in px² (only valid when person_detected=True)
    """
    Called every frame once approach_largest_person() has already stopped the robot
    close to a person (largest_box_area >= STOP_AREA was reached). Maintains proximity
    to the person and re-acquires them if they exit the camera frame.

    Three states drive the per-frame logic:

      State 1 — HOLD (person visible and still close):
        largest_box_area >= STOP_AREA and person_detected=True
        → stop_all(); hold position; sale interaction goes here.

      State 2 — RE-APPROACH (person visible but backed away):
        person_detected=True but largest_box_area < STOP_AREA
        → delegate to approach_largest_person() to re-close the distance.

      State 3 — ROTATE SCAN (person has exited the frame):
        person_detected=False
        → rotate in the direction the person was last seen using _last_known_offset.
           rotate_left() if they were last left of center, rotate_right() if right.

    Module-level variable used:
      _last_known_offset (int): updated every frame a person is visible;
                                 read in State 3 to choose rotation direction.

    Motor functions called (all imported at module top):
      - stop_all()                      : utilities/motors.py  — zeros all GPIO motor PWM
      - approach_largest_person()       : this module          — re-closes gap to person
      - rotate_left(intensity)          : behaviors/mecanum.py — spins robot left in place
      - rotate_right(intensity)         : behaviors/mecanum.py — spins robot right in place
    """

    global _last_known_offset    # required by Python to write to the module-level _last_known_offset variable; without this line Python would create a new local variable instead of updating the shared one
    global _force_sale_start_time # required by Python to write to the module-level _force_sale_start_time variable; same reason — needed for any assignment to a module-level variable inside a function

    # ----- ENGAGEMENT TIMER -----
    if _force_sale_start_time == 0.0: # checks if this is the very first frame force_sale() has been called for this person; 0.0 is the sentinel value meaning the clock has not started yet
        _force_sale_start_time = time.monotonic() # starts the engagement clock by recording the current monotonic time in seconds; time.monotonic() counts upward from an arbitrary point and never jumps backward — immune to NTP or manual system clock changes

    elapsed = time.monotonic() - _force_sale_start_time # computes total seconds since the engagement clock started; this value grows every frame regardless of which state is active — it counts through HOLD, RE-APPROACH, and ROTATE SCAN combined

    if elapsed >= config.FORCE_SALE_CONFIG['MAX_ENGAGEMENT_SECONDS']: # reads MAX_ENGAGEMENT_SECONDS (300s = 5 min) from FORCE_SALE_CONFIG; if total engagement time has reached or exceeded the limit → give up on this person
        _force_sale_start_time = 0.0 # resets the engagement clock back to sentinel value 0.0 so the very next person force_sale() is called for will get a completely fresh MAX_ENGAGEMENT_SECONDS window
        stop_all() # writes PWM duty 0 to all four GPIO motor pins via pigpio daemon — halts all wheel motion before the caller transitions the robot to find_customer()
        logging.debug( # logs the timeout event with the exact elapsed time so you can verify in the log file how long the robot spent with this person before giving up
            f"(customer_finder.py): FORCE_SALE TIMEOUT — gave up on person after {elapsed:.1f}s "
            f"(MAX_ENGAGEMENT_SECONDS={config.FORCE_SALE_CONFIG['MAX_ENGAGEMENT_SECONDS']}s). Moving on.\n"
        )
        return # exits force_sale() immediately and returns control to the caller (_state_machine in control_logic.py); the caller is responsible for transitioning to find_customer() after this return
    # ----- END ENGAGEMENT TIMER -----

    frame_center_x = config.PERSON_APPROACH_CONFIG['FRAME_WIDTH'] // 2 # reads FRAME_WIDTH (e.g. 1152px) from PERSON_APPROACH_CONFIG and integer-divides by 2 → the horizontal midpoint pixel of the camera frame (e.g. 576px); used as the reference point all offsets are measured against

    if person_detected: # OpenVINO inference returned person_detected=True this frame → person is visible in the camera; enter the visible-person branch to update offset and decide which state to run

        _last_known_offset = target_cx - frame_center_x # subtracts frame_center_x from target_cx to get the signed pixel distance of the person from frame center; negative = person is left of center, positive = person is right of center, zero = perfectly centered; written to module-level so State 3 can read it if person exits on the next frame

        if largest_box_area >= config.PERSON_APPROACH_CONFIG['STOP_AREA']: # reads STOP_AREA from PERSON_APPROACH_CONFIG; box area AT OR ABOVE threshold means person is close enough — robot should stop driving and hold; enter STATE 1 sighted re-centering sub-states

            # STATE 1 — person is visible and close; check offset to decide: rotate to re-center or hold still
            if _last_known_offset < -config.FORCE_SALE_CONFIG['HOLD_DEADBAND']: # reads HOLD_DEADBAND (150px) from FORCE_SALE_CONFIG; _last_known_offset is MORE negative than −HOLD_DEADBAND → person has drifted LEFT of center beyond the tolerance zone while still visible and close; this is a SIGHTED rotation — direction is known because person is still in frame
                rotate_left(config.FORCE_SALE_CONFIG['ROTATE_INTENSITY']) # calls rotate_left() from behaviors/mecanum.py; sets all 4 wheels clockwise to spin the robot body left in place at ROTATE_INTENSITY (~20% PWM); nudges robot heading left to re-center the person; next frame re-evaluates offset — stops when offset falls back within ±HOLD_DEADBAND
                logging.debug( # logs STATE 1A sighted re-center left: the exact offset that triggered the rotation, the HOLD_DEADBAND threshold it exceeded, and the ROTATE_INTENSITY applied
                    f"(customer_finder.py): FORCE_SALE HOLD ROTATE LEFT — person drifting left, re-centering. "
                    f"offset={_last_known_offset:+d}px < -HOLD_DEADBAND={-config.FORCE_SALE_CONFIG['HOLD_DEADBAND']}px, "
                    f"intensity={config.FORCE_SALE_CONFIG['ROTATE_INTENSITY']}.\n"
                )

            elif _last_known_offset > config.FORCE_SALE_CONFIG['HOLD_DEADBAND']: # reads HOLD_DEADBAND (150px) from FORCE_SALE_CONFIG; _last_known_offset is MORE positive than +HOLD_DEADBAND → person has drifted RIGHT of center beyond the tolerance zone while still visible and close; SIGHTED rotation — direction is known
                rotate_right(config.FORCE_SALE_CONFIG['ROTATE_INTENSITY']) # calls rotate_right() from behaviors/mecanum.py; sets all 4 wheels counterclockwise to spin the robot body right in place at ROTATE_INTENSITY (~20% PWM); nudges robot heading right to re-center the person; stops automatically next frame when offset falls within ±HOLD_DEADBAND
                logging.debug( # logs STATE 1B sighted re-center right: the exact offset that triggered the rotation, the HOLD_DEADBAND threshold it exceeded, and the ROTATE_INTENSITY applied
                    f"(customer_finder.py): FORCE_SALE HOLD ROTATE RIGHT — person drifting right, re-centering. "
                    f"offset={_last_known_offset:+d}px > +HOLD_DEADBAND={config.FORCE_SALE_CONFIG['HOLD_DEADBAND']}px, "
                    f"intensity={config.FORCE_SALE_CONFIG['ROTATE_INTENSITY']}.\n"
                )

            else: # _last_known_offset is within ±HOLD_DEADBAND → person is centered enough relative to the frame; no steering correction needed; robot holds its current position
                stop_all() # writes PWM duty 0 to all four GPIO motor pins via pigpio daemon — holds the robot completely still; this is the slot where sale interaction (screen display, audio prompt, etc.) will be added later
                logging.debug( # logs STATE 1C hold decision: confirms person is in frame and close, logs the current box_area vs STOP_AREA threshold, and the signed offset vs HOLD_DEADBAND window
                    f"(customer_finder.py): FORCE_SALE HOLD — person in frame, close, and centered. "
                    f"box_area={largest_box_area}px² >= STOP_AREA={config.PERSON_APPROACH_CONFIG['STOP_AREA']}px², "
                    f"offset={_last_known_offset:+d}px within ±HOLD_DEADBAND={config.FORCE_SALE_CONFIG['HOLD_DEADBAND']}px.\n"
                )

        else: # largest_box_area is below STOP_AREA but person_detected=True → person is still visible but has backed away from the robot; bounding box shrank because distance increased; need to re-close the gap

            # STATE 2 — person is visible but backed away; delegate entirely to approach_largest_person() to re-chase
            approach_largest_person(target_cx, largest_box_area) # passes the current frame's target_cx and largest_box_area to approach_largest_person(); that function handles all steering decisions (arc_left, arc_right, forward, slowdown, stop_all) to re-close the distance; when box_area hits STOP_AREA again the next frame falls back into STATE 1
            logging.debug( # logs STATE 2 re-approach decision: current box_area and the STOP_AREA threshold that was not met, confirming the delegation to approach_largest_person()
                f"(customer_finder.py): FORCE_SALE RE-APPROACH — person backed away, delegating to approach_largest_person. "
                f"box_area={largest_box_area}px² < STOP_AREA={config.PERSON_APPROACH_CONFIG['STOP_AREA']}px².\n"
            )

    else: # person_detected=False → OpenVINO found no person in this frame; person has fully exited the camera frame; _last_known_offset is NOT updated here — it stays frozen at the last recorded position; robot must spin blindly to re-acquire

        # STATE 3 — person is gone from frame; use frozen _last_known_offset to choose blind rotation direction
        if _last_known_offset <= 0: # frozen _last_known_offset is negative or zero → person was last seen LEFT of center or exactly centered; rotate left to scan in the direction they were last heading

            rotate_left(config.FORCE_SALE_CONFIG['ROTATE_INTENSITY']) # calls rotate_left() from behaviors/mecanum.py; sets all 4 wheels clockwise to spin the robot body left in place at ROTATE_INTENSITY (~20% PWM); continues spinning every frame until person_detected=True again on a future frame
            logging.debug( # logs STATE 3A: human-readable out-of-frame message + the frozen last_known_offset that chose left and the ROTATE_INTENSITY being applied
                f"(customer_finder.py): FORCE_SALE — person out of frame, turning LEFT to re-acquire. "
                f"last_known_offset={_last_known_offset:+d}px <= 0, "
                f"intensity={config.FORCE_SALE_CONFIG['ROTATE_INTENSITY']}.\n"
            )

        else: # frozen _last_known_offset is positive → person was last seen RIGHT of center; rotate right to scan in the direction they were last heading

            rotate_right(config.FORCE_SALE_CONFIG['ROTATE_INTENSITY']) # calls rotate_right() from behaviors/mecanum.py; sets all 4 wheels counterclockwise to spin the robot body right in place at ROTATE_INTENSITY (~20% PWM); continues spinning every frame until person_detected=True again on a future frame
            logging.debug( # logs STATE 3B: human-readable out-of-frame message + the frozen last_known_offset that chose right and the ROTATE_INTENSITY being applied
                f"(customer_finder.py): FORCE_SALE — person out of frame, turning RIGHT to re-acquire. "
                f"last_known_offset={_last_known_offset:+d}px > 0, "
                f"intensity={config.FORCE_SALE_CONFIG['ROTATE_INTENSITY']}.\n"
            )
