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

    image_folder = "/home/matthewthomasbeck/Projects/Vending_Machine_Robot-Hardware/ImageAssets"
    #image_folder = r"C:\Users\srsay\Downloads\Vending_Machine_Robot-Hardware\ImageAssets"

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

    # Define button positions (assuming buttons are 80x80)
    button_size = 80
    margin = 10
    start_x = 50
    start_y = 50
    positions = {
        'button_one': (start_x, start_y),
        'button_two': (start_x + button_size + margin, start_y),
        'button_three': (start_x + 2*(button_size + margin), start_y),
        'button_four': (start_x, start_y + button_size + margin),
        'button_five': (start_x + button_size + margin, start_y + button_size + margin),
        'button_six': (start_x + 2*(button_size + margin), start_y + button_size + margin),
        'button_seven': (start_x, start_y + 2*(button_size + margin)),
        'button_eight': (start_x + button_size + margin, start_y + 2*(button_size + margin)),
        'button_nine': (start_x + 2*(button_size + margin), start_y + 2*(button_size + margin)),
        'button_zero': (start_x + button_size + margin, start_y + 3*(button_size + margin)),
    }

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
                for name, pos in positions.items():
                    rect = pygame.Rect(pos[0], pos[1], button_size, button_size)
                    if rect.collidepoint(x, y):
                        num = num_map[name.split('_')[1]]
                        insert_number(num)

        screen.fill((255, 255, 255))  # fill the screen with white

        # Display buttons
        for name, pos in positions.items():
            screen.blit(images[name], pos)

        # Display screen_interface at the bottom
        interface_height = images['screen_interface'].get_height()
        screen.blit(images['screen_interface'], (0, height - interface_height))

        # Display current input
        text = font.render(current_input, True, (0, 0, 0))
        screen.blit(text, (10, 10))

        pygame.display.flip()  # update the display



except Exception as e:
    print(f"THE SCREEN HAS AN ERROR!!!!!!!!!! \n{e}")