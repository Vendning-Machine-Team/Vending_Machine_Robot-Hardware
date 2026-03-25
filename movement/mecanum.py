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

import math

##### import motor functions #####

from utilities.motors import move_motor





###################################################
############### MECANUM DRIVE LOGIC ###############
###################################################


########## MASTER DRIVE FUNCTION ##########

##### master drive function #####

# function used to drive the robot in a given direction and intensity
# x: left/right strafe (-1 left, +1 right), y: forward/back (-1 back, +1 forward)
# r: rotation (-1 left, +1 right), intensity: 0-10 overall scale
def drive(x, y, r, intensity):

    x = _clamp(float(x), -1.0, 1.0)
    y = _clamp(float(y), -1.0, 1.0)
    r = _clamp(float(r), -1.0, 1.0)

    # standard mecanum wheel mix
    fl = y - x - r
    fr = y + x + r
    bl = y + x - r
    br = y - x + r

    set_wheel_speeds(fl, fr, bl, br, intensity)


##### drive by angle #####

# drive with an angle and magnitude, 0 deg = forward, 90 deg = right, 180 deg = backward, 270 deg = left
def drive_polar(angle_deg, magnitude, rotation=0.0, intensity=10):

    angle_rad = math.radians(float(angle_deg))
    magnitude = _clamp(float(magnitude), 0.0, 1.0)
    rotation = _clamp(float(rotation), -1.0, 1.0)

    x = math.sin(angle_rad) * magnitude
    y = math.cos(angle_rad) * magnitude

    drive(x, y, rotation, intensity)


########## CARDINAL DIRECTIONS LOGIC ##########

##### forward #####

def forward(intensity): # fl counterclockwise, fr clockwise, bl counterclockwise, br clockwise

    move_motor('FL', 'counterclockwise', intensity)
    move_motor('FR', 'clockwise', intensity)
    move_motor('BL', 'counterclockwise', intensity)
    move_motor('BR', 'clockwise', intensity)

##### backward #####

def backward(intensity): # backward is forward reversed

    move_motor('FL', 'clockwise', intensity)
    move_motor('FR', 'counterclockwise', intensity)
    move_motor('BL', 'clockwise', intensity)
    move_motor('BR', 'counterclockwise', intensity)

##### strafe left #####

def strafe_left(intensity): # strafe left

    move_motor('FL', 'clockwise', intensity)
    move_motor('FR', 'clockwise', intensity)
    move_motor('BL', 'counterclockwise', intensity)
    move_motor('BR', 'counterclockwise', intensity)

##### strafe right #####

def strafe_right(intensity): # strafe right

    move_motor('FL', 'counterclockwise', intensity)
    move_motor('FR', 'counterclockwise', intensity)
    move_motor('BL', 'clockwise', intensity)
    move_motor('BR', 'clockwise', intensity)


########## ROTATION LOGIC ##########

##### rotate left #####

def rotate_left(intensity): # rotate left in place

    move_motor('FL', 'clockwise', intensity)
    move_motor('FR', 'clockwise', intensity)
    move_motor('BL', 'clockwise', intensity)
    move_motor('BR', 'clockwise', intensity)


##### rotate right #####

def rotate_right(intensity): # rotate right in place

    move_motor('FL', 'counterclockwise', intensity)
    move_motor('FR', 'counterclockwise', intensity)
    move_motor('BL', 'counterclockwise', intensity)
    move_motor('BR', 'counterclockwise', intensity)


########## DIAGONAL LOGIC ##########

##### diagonal front left #####

def diagonal_front_left(intensity): # front-left diagonal

    move_motor('FL', 'stop', 0)
    move_motor('FR', 'clockwise', intensity)
    move_motor('BL', 'counterclockwise', intensity)
    move_motor('BR', 'stop', 0)

##### diagonal front right #####

def diagonal_front_right(intensity): # front-right diagonal

    move_motor('FL', 'counterclockwise', intensity)
    move_motor('FR', 'stop', 0)
    move_motor('BL', 'stop', 0)
    move_motor('BR', 'clockwise', intensity)

##### diagonal back left #####

def diagonal_back_left(intensity): # back-left diagonal

    move_motor('FL', 'clockwise', intensity)
    move_motor('FR', 'stop', 0)
    move_motor('BL', 'stop', 0)
    move_motor('BR', 'counterclockwise', intensity)

##### diagonal back right #####

def diagonal_back_right(intensity): # back-right diagonal

    move_motor('FL', 'stop', 0)
    move_motor('FR', 'counterclockwise', intensity)
    move_motor('BL', 'clockwise', intensity)
    move_motor('BR', 'stop', 0)


########## ARC MOVEMENT LOGIC ##########

##### arc left #####

def arc_left(forward_strength=1.0, turn_strength=0.4, intensity=10): # function used to move forward while curving left

    drive(0.0, forward_strength, -abs(turn_strength), intensity)

##### arc right #####

def arc_right(forward_strength=1.0, turn_strength=0.4, intensity=10): # function used to move forward while curving right

    drive(0.0, forward_strength, abs(turn_strength), intensity)


########## HELPER FUNCTIONS ##########

##### clamp vector values #####

def _clamp(value, minimum, maximum): # function used to make sure direction vectors are within -1.0 to 1.0

    return max(minimum, min(maximum, value))

##### apply wheel values #####

def _apply_wheel_value(motor_name, wheel_value, max_intensity): # function used to apply the wheel value to the motor

    v = _clamp(float(wheel_value), -1.0, 1.0) # make sure wheel value is within -1.0 to 1.0
    max_intensity = _clamp(int(max_intensity), 0, 10) # make sure max intensity is within 0 to 10
    scaled_intensity = int(round(abs(v) * max_intensity))

    if scaled_intensity <= 0:
        move_motor(motor_name, 'stop', 0)
        return

    # + value means use the same wheel spin direction as forward(), - value means reverse that wheel
    if motor_name in ('FL', 'BL'):
        direction = 'counterclockwise' if v > 0 else 'clockwise'
    else:
        direction = 'clockwise' if v > 0 else 'counterclockwise'

    move_motor(motor_name, direction, scaled_intensity)

##### set wheel speeds #####

def set_wheel_speeds(fl, fr, bl, br, max_intensity=10): # function used to set the speed of each wheel, positive = foward direction

    values = [float(fl), float(fr), float(bl), float(br)]
    max_mag = max(abs(v) for v in values) # normalize if any wheel magnitude is above 1.0

    if max_mag > 1.0:
        values = [v / max_mag for v in values]

    _apply_wheel_value('FL', values[0], max_intensity)
    _apply_wheel_value('FR', values[1], max_intensity)
    _apply_wheel_value('BL', values[2], max_intensity)
    _apply_wheel_value('BR', values[3], max_intensity)