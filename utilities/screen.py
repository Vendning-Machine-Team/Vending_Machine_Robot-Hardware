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

from config import SCREEN_CONFIG # import screen configuration from config module


########## CREATE DEPENDENCIES ##########

##### create global variables #####

height = SCREEN_CONFIG['HEIGHT']
width = SCREEN_CONFIG['WIDTH']
fps = SCREEN_CONFIG['FPS']





################################################
############### SCREEN FUNCTIONS ###############
################################################


########## PYGAME INITIALIZATION ##########

def initialize_screen(): # function to initialize pygame screen

    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((width, height)) #default of 800x480

    image_folder = r"c:\Users\srsay\Downloads\Vending_Machine_Robot-Hardware\image_assets"

    images = {}
    for filename in os.listdir(image_folder):
        if filename.endswith(".png"):
            name = filename[:-4]  # remove .png
            img_path = os.path.join(image_folder, filename)
            img = pygame.image.load(img_path).convert_alpha()  # convert_alpha keeps transparency
            images[name] = img

    return screen, images

try:
    screen, images = initialize_screen() # initialize the screen

    button_names = [name for name in images.keys() if name.startswith('button_')]

    # Number mapping
    num_map = {'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'zero': '0'}

    current_input = ""
    font = pygame.font.SysFont(None, 48)

    def insert_number(num):
        global current_input
        current_input += num
        print(f"Current input: {current_input}")

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for name in button_names:
                    button_image = images[name]
                    if x < button_image.get_width() and y < button_image.get_height():
                        if button_image.get_at((x, y))[3] != 0:
                            num = num_map[name.split('_')[1]]
                            insert_number(num)
                            break

        screen.fill((255, 255, 255))  # fill the screen with white

        # Display screen_interface at the bottom first so buttons render on top
        if 'screen_interface' in images:
            interface_height = images['screen_interface'].get_height()
            screen.blit(images['screen_interface'], (0, height - interface_height))

        # Display buttons on top of the interface/background
        for name in button_names:
            screen.blit(images[name], (0, 0))

        # Display current input
        text = font.render(current_input, True, (0, 0, 0))
        screen.blit(text, (10, 10))

        pygame.display.flip()  # update the display



except Exception as e:
    print(f"THE SCREEN HAS AN ERROR!!!!!!!!!! \n{e}")