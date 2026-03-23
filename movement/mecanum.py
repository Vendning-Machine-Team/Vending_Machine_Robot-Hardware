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

##### import motor functions #####

import math

from utilities.motors import move_motor





###################################################
############### MECANUM DRIVE LOGIC ###############
###################################################


########## MASTER VECTOR DIRECTION FUNCTION ##########

def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _apply_wheel_value(motor_name, wheel_value, max_intensity):
    # wheel_value should be in -1.0 to 1.0 after normalization
    v = _clamp(float(wheel_value), -1.0, 1.0)
    max_intensity = _clamp(int(max_intensity), 0, 10)

    scaled_intensity = int(round(abs(v) * max_intensity))
    if scaled_intensity <= 0:
        move_motor(motor_name, 'stop', 0)
        return

    # + value means use the same wheel spin direction as forward()
    # - value means reverse that wheel
    if motor_name in ('FL', 'BL'):
        direction = 'counterclockwise' if v > 0 else 'clockwise'
    else:
        direction = 'clockwise' if v > 0 else 'counterclockwise'

    move_motor(motor_name, direction, scaled_intensity)


def set_wheel_speeds(fl, fr, bl, br, max_intensity=10):
    """
    set wheel values directly.
    expected input per wheel: -1.0 to 1.0
    positive = same direction used for forward()
    """
    values = [float(fl), float(fr), float(bl), float(br)]

    # normalize if any wheel magnitude is above 1.0
    max_mag = max(abs(v) for v in values)
    if max_mag > 1.0:
        values = [v / max_mag for v in values]

    _apply_wheel_value('FL', values[0], max_intensity)
    _apply_wheel_value('FR', values[1], max_intensity)
    _apply_wheel_value('BL', values[2], max_intensity)
    _apply_wheel_value('BR', values[3], max_intensity)


def drive(x, y, r, intensity=10):
    """
    mecanum vector drive.
    x: left/right strafe (-1 left, +1 right)
    y: forward/back (-1 back, +1 forward)
    r: rotation (-1 left, +1 right)
    intensity: 0-10 overall scale
    """
    x = _clamp(float(x), -1.0, 1.0)
    y = _clamp(float(y), -1.0, 1.0)
    r = _clamp(float(r), -1.0, 1.0)

    # standard mecanum wheel mix
    fl = y - x - r
    fr = y + x + r
    bl = y + x - r
    br = y - x + r

    set_wheel_speeds(fl, fr, bl, br, intensity)


def drive_polar(angle_deg, magnitude, rotation=0.0, intensity=10):
    """
    drive by angle instead of x/y.
    0 deg = forward, 90 deg = right, 180 deg = backward, 270 deg = left
    """
    angle_rad = math.radians(float(angle_deg))
    magnitude = _clamp(float(magnitude), 0.0, 1.0)
    rotation = _clamp(float(rotation), -1.0, 1.0)

    x = math.sin(angle_rad) * magnitude
    y = math.cos(angle_rad) * magnitude

    drive(x, y, rotation, intensity)


def stop():
    move_motor('FL', 'stop', 0)
    move_motor('FR', 'stop', 0)
    move_motor('BL', 'stop', 0)
    move_motor('BR', 'stop', 0)


########## FORWARD LOGIC ##########

def forward(intensity):
    # forward:
    # fl counterclockwise, fr clockwise, bl counterclockwise, br clockwise
    move_motor('FL', 'counterclockwise', intensity)
    move_motor('FR', 'clockwise', intensity)
    move_motor('BL', 'counterclockwise', intensity)
    move_motor('BR', 'clockwise', intensity)


########## BACKWARD LOGIC ##########

def backward(intensity):
    # backward is forward reversed
    move_motor('FL', 'clockwise', intensity)
    move_motor('FR', 'counterclockwise', intensity)
    move_motor('BL', 'clockwise', intensity)
    move_motor('BR', 'counterclockwise', intensity)


########## SHIFT LEFT LOGIC ##########

def shift_left(intensity):
    # strafe left
    move_motor('FL', 'clockwise', intensity)
    move_motor('FR', 'clockwise', intensity)
    move_motor('BL', 'counterclockwise', intensity)
    move_motor('BR', 'counterclockwise', intensity)


########## SHIFT RIGHT LOGIC ##########

def shift_right(intensity):
    # strafe right is strafe left reversed
    move_motor('FL', 'counterclockwise', intensity)
    move_motor('FR', 'counterclockwise', intensity)
    move_motor('BL', 'clockwise', intensity)
    move_motor('BR', 'clockwise', intensity)


########## ROTATE LEFT LOGIC ##########

def rotate_left(intensity):
    # rotate left in place
    move_motor('FL', 'clockwise', intensity)
    move_motor('FR', 'clockwise', intensity)
    move_motor('BL', 'clockwise', intensity)
    move_motor('BR', 'clockwise', intensity)


########## ROTATE RIGHT LOGIC ##########

def rotate_right(intensity):
    # rotate right in place
    move_motor('FL', 'counterclockwise', intensity)
    move_motor('FR', 'counterclockwise', intensity)
    move_motor('BL', 'counterclockwise', intensity)
    move_motor('BR', 'counterclockwise', intensity)


########## DIAGONAL LOGIC ##########

def diagonal_front_left(intensity):
    # front-left diagonal
    move_motor('FL', 'stop', 0)
    move_motor('FR', 'clockwise', intensity)
    move_motor('BL', 'counterclockwise', intensity)
    move_motor('BR', 'stop', 0)


def diagonal_front_right(intensity):
    # front-right diagonal
    move_motor('FL', 'counterclockwise', intensity)
    move_motor('FR', 'stop', 0)
    move_motor('BL', 'stop', 0)
    move_motor('BR', 'clockwise', intensity)


def diagonal_back_left(intensity):
    # back-left diagonal
    move_motor('FL', 'clockwise', intensity)
    move_motor('FR', 'stop', 0)
    move_motor('BL', 'stop', 0)
    move_motor('BR', 'counterclockwise', intensity)


def diagonal_back_right(intensity):
    # back-right diagonal
    move_motor('FL', 'stop', 0)
    move_motor('FR', 'counterclockwise', intensity)
    move_motor('BL', 'clockwise', intensity)
    move_motor('BR', 'stop', 0)


########## ARC LOGIC ##########

def arc_left(forward_strength=1.0, turn_strength=0.4, intensity=10):
    # move forward while curving left
    drive(0.0, forward_strength, -abs(turn_strength), intensity)


def arc_right(forward_strength=1.0, turn_strength=0.4, intensity=10):
    # move forward while curving right
    drive(0.0, forward_strength, abs(turn_strength), intensity)
