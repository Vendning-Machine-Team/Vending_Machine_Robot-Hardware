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


########## BUTTON LAYOUT ##########

def get_button_positions(button_width, button_height, start_x, start_y, padding):
    """
    Create a numpad-style grid layout for buttons.
    Returns dict mapping button names to (x, y) positions.
    """
    # Numpad layout:
    # 1 2 3
    # 4 5 6
    # 7 8 9
    #   0
    positions = {
        'button_one':   (start_x + 0 * (button_width + padding), start_y + 0 * (button_height + padding)),
        'button_two':   (start_x + 1 * (button_width + padding), start_y + 0 * (button_height + padding)),
        'button_three': (start_x + 2 * (button_width + padding), start_y + 0 * (button_height + padding)),
        'button_four':  (start_x + 0 * (button_width + padding), start_y + 1 * (button_height + padding)),
        'button_five':  (start_x + 1 * (button_width + padding), start_y + 1 * (button_height + padding)),
        'button_six':   (start_x + 2 * (button_width + padding), start_y + 1 * (button_height + padding)),
        'button_seven': (start_x + 0 * (button_width + padding), start_y + 2 * (button_height + padding)),
        'button_eight': (start_x + 1 * (button_width + padding), start_y + 2 * (button_height + padding)),
        'button_nine':  (start_x + 2 * (button_width + padding), start_y + 2 * (button_height + padding)),
        'button_zero':  (start_x + 1 * (button_width + padding), start_y + 3 * (button_height + padding)),
    }
    return positions


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

        # Get button dimensions from first button image
        sample_button = images.get('button_one')
        if sample_button:
            button_width = sample_button.get_width()
            button_height = sample_button.get_height()
        else:
            button_width = 80
            button_height = 80

        # Calculate button positions (centered numpad)
        padding = 10
        grid_width = 3 * button_width + 2 * padding
        start_x = (width - grid_width) // 2
        start_y = 120  # leave room for input display at top

        button_positions = get_button_positions(button_width, button_height, start_x, start_y, padding)

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

                    # Check each button for click
                    for name in button_names:
                        if name not in button_positions:
                            continue

                        btn_x, btn_y = button_positions[name]
                        button_image = images[name]
                        btn_width = button_image.get_width()
                        btn_height = button_image.get_height()

                        # Check if click is within button bounds
                        if (btn_x <= mouse_x <= btn_x + btn_width and
                            btn_y <= mouse_y <= btn_y + btn_height):

                            # Check pixel alpha for non-rectangular buttons
                            local_x = mouse_x - btn_x
                            local_y = mouse_y - btn_y
                            if button_image.get_at((int(local_x), int(local_y)))[3] != 0:
                                num = num_map[name.split('_')[1]]
                                current_input += num
                                logging.info(f"(screen.py): Button pressed: {num}, Current input: {current_input}")
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

            # Display screen_interface as background
            if 'screen_interface' in images:
                screen.blit(images['screen_interface'], (0, 0))

            # Display buttons at their positions
            for name in button_names:
                if name in button_positions:
                    screen.blit(images[name], button_positions[name])

            # Display current input at top center
            text = font.render(current_input, True, (0, 0, 0))
            text_rect = text.get_rect(center=(width // 2, 50))
            screen.blit(text, text_rect)

            # Display instruction text
            instruction_font = pygame.font.SysFont(None, 32)
            instruction = instruction_font.render("Enter your payment code:", True, (50, 50, 50))
            instruction_rect = instruction.get_rect(center=(width // 2, 90))
            screen.blit(instruction, instruction_rect)

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