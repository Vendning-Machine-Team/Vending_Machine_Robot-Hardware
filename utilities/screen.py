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

import logging  # import logging for debugging
import time  # import time for sleep functions
import pygame  # import pygame for screen display and input handling
import os  # import os for file operations

##### import necessary functions #####

from utilities.config import SCREEN_CONFIG # import screen configuration from config module


########## CREATE DEPENDENCIES ##########

##### create global variables #####

height = SCREEN_CONFIG.HEIGHT
width = SCREEN_CONFIG.WIDTH
fps = SCREEN_CONFIG.FPS





################################################
############### SCREEN FUNCTIONS ###############
################################################


########## PYGAME INITIALIZATION ##########

def initialize_screen(): # function to initialize pygame screen

    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((width, height)) #default of 800x480

    image_folder = "/home/matthewthomasbeck/Projects/Vending_Machine_Robot-Hardware/ImageAssets"
    #image_folder = r"C:\Users\srsay\Downloads\Vending_Machine_Robot-Hardware\ImageAssets"

    images = []
    for filename in sorted(os.listdir(image_folder)):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            img_path = os.path.join(image_folder, filename)
            img = pygame.image.load(img_path).convert_alpha()  # convert_alpha keeps transparency
            images.append(img_path)
