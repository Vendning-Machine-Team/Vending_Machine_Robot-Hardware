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

from utilities.motors import move_motor





###################################################
############### MECANUM DRIVE LOGIC ###############
###################################################


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
