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

import sys
import os
import logging  # import logging for debugging
import time  # import time for sleep functions
import pygame  # import pygame for screen display and input handling

# Add parent directory to path so we can import from utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

    # For Raspberry Pi framebuffer display (touchscreen)
    # Set these before pygame.init()
    if os.path.exists('/dev/fb0'):
        os.environ['SDL_VIDEODRIVER'] = 'fbcon'
        os.environ['SDL_FBDEV'] = '/dev/fb0'

    pygame.init()
    pygame.font.init()

    # Hide mouse cursor for touchscreen
    pygame.mouse.set_visible(True)  # Set to False on Pi touchscreen

    screen = pygame.display.set_mode((width, height)) #default of 800x480

    # Use relative path from this file's location to find image_assets
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    image_folder = os.path.join(project_root, "image_assets")

    images = {}
    for filename in os.listdir(image_folder):
        if filename.endswith(".png"):
            name = filename[:-4]  # remove .png
            img_path = os.path.join(image_folder, filename)
            img = pygame.image.load(img_path).convert_alpha()  # convert_alpha keeps transparency
            images[name] = img

    return screen, images


########## MAIN SCREEN LOOP ##########

def run_payment_screen():
    """
    Run the payment code entry screen.
    Returns the entered code when complete, or None if cancelled.
    """
    try:
        screen, images = initialize_screen()

        button_names = [name for name in images.keys() if name.startswith('button_')]

        # Number mapping
        num_map = {
            'one': '1', 'two': '2', 'three': '3',
            'four': '4', 'five': '5', 'six': '6',
            'seven': '7', 'eight': '8', 'nine': '9',
            'zero': '0'
        }

        current_input = ""
        font = pygame.font.SysFont(None, 64)
        clock = pygame.time.Clock()

        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return None

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos

                    # Check each button for click (buttons are full-screen overlays at 0,0)
                    for name in button_names:
                        button_image = images[name]

                        # Check if click position has non-transparent pixel in this button image
                        if (0 <= mouse_x < button_image.get_width() and
                            0 <= mouse_y < button_image.get_height()):

                            pixel_alpha = button_image.get_at((mouse_x, mouse_y))[3]
                            if pixel_alpha != 0:  # Non-transparent = button was clicked
                                num = num_map[name.split('_')[1]]
                                current_input += num
                                logging.info(f"(screen.py): Button pressed: {num}, Current input: {current_input}")
                                print(f"Button pressed: {num}, Current input: {current_input}")
                                break

                elif event.type == pygame.KEYDOWN:
                    # Allow keyboard input for testing
                    if event.key == pygame.K_BACKSPACE:
                        current_input = current_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        logging.info(f"(screen.py): Code entered: {current_input}")
                        return current_input
                    elif event.unicode.isdigit():
                        current_input += event.unicode

            # Draw screen
            screen.fill((255, 255, 255))  # white background

            # Display screen_interface as background first
            if 'screen_interface' in images:
                screen.blit(images['screen_interface'], (0, 0))

            # Display all button overlays at (0,0) - they are pre-positioned in the images
            for name in button_names:
                screen.blit(images[name], (0, 0))

            # Display current input in the text box area (centered in the interface box)
            text = font.render(current_input, True, (0, 0, 0))
            text_rect = text.get_rect(center=(width // 2, 135))  # Positioned in the input box
            screen.blit(text, text_rect)

            pygame.display.flip()
            clock.tick(fps)

        pygame.quit()
        return current_input

    except Exception as e:
        logging.error(f"(screen.py): Screen error: {e}")
        print(f"THE SCREEN HAS AN ERROR!!!!!!!!!! \n{e}")
        return None


########## ENTRY POINT ##########

if __name__ == "__main__":
    code = run_payment_screen()
    if code:
        print(f"Entered code: {code}")
    else:
        print("No code entered")