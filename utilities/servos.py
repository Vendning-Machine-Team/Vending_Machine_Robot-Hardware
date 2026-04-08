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

##### import necessary functions #####

from utilities.maestro import initialize_maestro # import maestro initialization functions


########## CREATE DEPENDENCIES ##########

##### create maestro object #####

MAESTRO = initialize_maestro() # create maestro object





#############################################################
############### FUNDAMENTAL MOVEMENT FUNCTION ###############
#############################################################


########## MOVE A SINGLE SERVO ##########

def set_target(channel, target, speed, acceleration): # function to set target position of a singular servo

    ##### move a servo to a desired position using its number and said position #####

    logging.debug(f"(servos.py): Attempting to move servo {channel} to target {target} with speed {speed} and acceleration {acceleration}...\n")

    try: # attempt to move desired servo

        target = int(round(target * 4)) # convert target from microseconds to quarter-microseconds
        speed = max(0, min(16383, speed)) # ensure speed is within valid range
        acceleration = max(0, min(255, acceleration)) # ensure acceleration is within valid range
        speed_command = bytearray([0x87, channel, speed & 0x7F, (speed >> 7) & 0x7F]) # create speed command
        MAESTRO.write(speed_command) # send speed command to maestro

        # create acceleration command
        accel_command = bytearray([0x89, channel, acceleration & 0x7F, (acceleration >> 7) & 0x7F])
        MAESTRO.write(accel_command) # send acceleration command to maestro
        command = bytearray([0x84, channel, target & 0x7F, (target >> 7) & 0x7F]) # create target position command
        MAESTRO.write(command) # send target position command to maestro

    except:
        logging.error("(servos.py): Failed to move servo.\n") # print failure statement





#############################################################
############### FUNDAMENTAL MOVEMENT FUNCTION ###############
#############################################################


########## SERVO 0 (left lid hinge) TEST ###########

def test_servo_0_center():
    """Move servo 0 (left lid hinge) to center position (1500 μs / 90°)"""
    print("\n[Servo 0] Moving to CENTER (1500 μs / 90°)")
    set_target(channel=0, target=1500, speed=200, acceleration=250)
    print("Servo 0 should now be at center position")

def test_servo_0_plus_90():
    """Move servo 0 (left lid hinge) +90° from center (2000 μs / 180°)"""
    print("\n[Servo 0] Moving +90° from center (2000 μs / 180°)")
    set_target(channel=0, target=2000, speed=200, acceleration=250)
    print("Servo 0 should now be rotated +90° from center")

def test_servo_0_minus_90():
    """Move servo 0 (left lid hinge) -90° from center (1000 μs / 0°)"""
    print("\n[Servo 0] Moving -90° from center (1000 μs / 0°)")
    set_target(channel=0, target=1000, speed=200, acceleration=250)
    print("Servo 0 should now be rotated -90° from center")

def test_servo_0_full_range():
    """Sweep servo 0 through full 180° range"""
    print("\n[Servo 0] Full range test: 1000 → 1500 → 2000 → 1500")
    print("Moving to 1000 μs (0°)...")
    set_target(channel=0, target=1000, speed=200, acceleration=250)
    time.sleep(2)

    print("Moving to 1500 μs (90°)...")
    set_target(channel=0, target=1500, speed=200, acceleration=250)
    time.sleep(2)

    print("Moving to 2000 μs (180°)...")
    set_target(channel=0, target=2000, speed=200, acceleration=250)
    time.sleep(2)

    print("Returning to center (1500 μs)...")
    set_target(channel=0, target=1500, speed=200, acceleration=250)
    print("Full range test complete")


########## SERVO 2 (lid lock) TEST ###########

def test_servo_2_center():
    """Move servo 2 (lid lock) to center position (1500 μs / 90°)"""
    print("\n[Servo 2] Moving to CENTER (1500 μs / 90°)")
    set_target(channel=2, target=1500, speed=200, acceleration=250)
    print("Servo 2 should now be at center position")

def test_servo_2_plus_90():
    """Move servo 2 (lid lock) +90° from center (2000 μs / 180°)"""
    print("\n[Servo 2] Moving +90° from center (2000 μs / 180°)")
    set_target(channel=2, target=2000, speed=200, acceleration=250)
    print("Servo 2 should now be rotated +90° from center")

def test_servo_2_minus_90():
    """Move servo 2 (lid lock) -90° from center (1000 μs / 0°)"""
    print("\n[Servo 2] Moving -90° from center (1000 μs / 0°)")
    set_target(channel=2, target=1000, speed=200, acceleration=250)
    print("Servo 2 should now be rotated -90° from center")

def test_servo_2_full_range():
    """Sweep servo 2 through full 180° range"""
    print("\n[Servo 2] Full range test: 1000 → 1500 → 2000 → 1500")
    print("Moving to 1000 μs (0°)...")
    set_target(channel=2, target=1000, speed=200, acceleration=250)
    time.sleep(2)

    print("Moving to 1500 μs (90°)...")
    set_target(channel=2, target=1500, speed=200, acceleration=250)
    time.sleep(2)

    print("Moving to 2000 μs (180°)...")
    set_target(channel=2, target=2000, speed=200, acceleration=250)
    time.sleep(2)

    print("Returning to center (1500 μs)...")
    set_target(channel=2, target=1500, speed=200, acceleration=250)
    print("Full range test complete")


########## CUSTOM POSITION TEST ###########

def test_servo_custom(channel, position): # move any servo to a custom pos

    print(f"\n[Servo {channel}] Moving to custom position: {position} μs")
    set_target(channel=channel, target=position, speed=200, acceleration=250)
    print(f"Servo {channel} moved to {position} μs")
