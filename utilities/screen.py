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
import logging
import time
import pygame

# Add parent directory to path so we can import from utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

##### import necessary functions #####

from utilities.config import SCREEN_CONFIG


########## CREATE DEPENDENCIES ##########

##### create global variables #####

height = SCREEN_CONFIG['HEIGHT']
width = SCREEN_CONFIG['WIDTH']
fps = SCREEN_CONFIG['FPS']





################################################
############### SCREEN FUNCTIONS ###############
################################################


########## PYGAME INITIALIZATION ##########

def initialize_screen():
    """Initialize pygame screen and load images"""

    pygame.init()
    pygame.font.init()

    pygame.mouse.set_visible(True)

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Vending Machine")

    # Use relative path from this file's location to find image_assets
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    image_folder = os.path.join(project_root, "image_assets")

    images = {}
    if os.path.exists(image_folder):
        for filename in os.listdir(image_folder):
            if filename.endswith(".png"):
                name = filename[:-4]
                img_path = os.path.join(image_folder, filename)
                img = pygame.image.load(img_path).convert_alpha()
                images[name] = img

    return screen, images


########## CODE ENTRY SCREEN ##########

def run_code_screen(email=None):
    """
    Display code entry screen with numpad.
    Shows the email the code was sent to.
    Returns the entered code or None if cancelled.
    """
    try:
        screen, images = initialize_screen()

        current_input = ""

        font = pygame.font.SysFont(None, 48)
        title_font = pygame.font.SysFont(None, 42)
        message_font = pygame.font.SysFont(None, 32)
        clock = pygame.time.Clock()

        # Number mapping for button images
        num_map = {
            'one': '1', 'two': '2', 'three': '3',
            'four': '4', 'five': '5', 'six': '6',
            'seven': '7', 'eight': '8', 'nine': '9',
            'zero': '0'
        }

        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return None

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos

                    # Check numpad buttons (image-based)
                    button_names = [name for name in images.keys() if name.startswith('button_')]
                    for name in button_names:
                        button_image = images[name]
                        if (0 <= mouse_x < button_image.get_width() and
                            0 <= mouse_y < button_image.get_height()):
                            pixel_alpha = button_image.get_at((mouse_x, mouse_y))[3]
                            if pixel_alpha != 0:
                                num = num_map[name.split('_')[1]]
                                current_input += num
                                print(f"Code input: {current_input}")
                                break

                    # Check submit/clear buttons
                    submit_rect = pygame.Rect(width // 2 + 20, height - 70, 150, 35)
                    clear_rect = pygame.Rect(width // 2 - 170, height - 70, 150, 35)

                    if submit_rect.collidepoint(mouse_x, mouse_y) and current_input:
                        logging.info(f"(screen.py): Code entered: {current_input}")
                        pygame.quit()
                        return current_input
                    elif clear_rect.collidepoint(mouse_x, mouse_y):
                        current_input = ""

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        current_input = current_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if current_input:
                            logging.info(f"(screen.py): Code entered: {current_input}")
                            pygame.quit()
                            return current_input
                    elif event.key == pygame.K_ESCAPE:
                        current_input = ""
                    elif event.unicode.isdigit():
                        current_input += event.unicode

            # Draw screen
            screen.fill((255, 255, 255))

            ##### LAYER 1: Background interface #####
            if 'screen_interface' in images:
                screen.blit(images['screen_interface'], (0, 0))
            else:
                # Fallback: draw blue header and footer
                pygame.draw.rect(screen, (0, 120, 255), (0, 0, width, 50))
                pygame.draw.rect(screen, (0, 120, 255), (0, height - 40, width, 40))

            ##### LAYER 2: Numpad buttons (overlay images at 0,0) #####
            button_names = [name for name in images.keys() if name.startswith('button_')]
            for name in button_names:
                screen.blit(images[name], (0, 0))

            ##### LAYER 3: Text elements (drawn on top of buttons) #####

            # Title in blue header area (y = 25, centered)
            title = title_font.render("Enter Verification Code", True, (255, 255, 255))
            title_rect = title.get_rect(center=(width // 2, 25))
            screen.blit(title, title_rect)

            # Email info below header (y = 60, above the input box)
            if email:
                email_text = message_font.render(f"{email}, please enter your code:", True, (0, 0, 0))
                email_rect = email_text.get_rect(center=(width // 2, 60))
                screen.blit(email_text, email_rect)

            # Code display inside the input box (y = 125, centered in the box area)
            code_display = font.render(current_input if current_input else "_ _ _ _ _ _", True, (0, 0, 0))
            code_rect = code_display.get_rect(center=(width // 2, 125))
            screen.blit(code_display, code_rect)

            ##### LAYER 4: Submit/Clear buttons (above blue footer) #####
            submit_rect = pygame.Rect(width // 2 + 20, height - 70, 150, 35)
            clear_rect = pygame.Rect(width // 2 - 170, height - 70, 150, 35)

            pygame.draw.rect(screen, (0, 150, 0), submit_rect)
            pygame.draw.rect(screen, (200, 50, 50), clear_rect)

            submit_text = message_font.render("SUBMIT", True, (255, 255, 255))
            clear_text = message_font.render("CLEAR", True, (255, 255, 255))

            screen.blit(submit_text, submit_text.get_rect(center=submit_rect.center))
            screen.blit(clear_text, clear_text.get_rect(center=clear_rect.center))

            pygame.display.flip()
            clock.tick(fps)

        pygame.quit()
        return None

    except Exception as e:
        logging.error(f"(screen.py): Code screen error: {e}")
        print(f"Code screen error: {e}")
        return None


########## MESSAGE SCREENS ##########

def show_success_screen(message="Lid is opening!"):
    """Display success message"""
    _show_message("SUCCESS!", message, color=(0, 150, 0), duration=3)


def show_error_screen(message="Please try again", attempts_left=0):
    """Display error message"""
    if attempts_left > 0:
        message = f"{message} ({attempts_left} attempts left)"
    _show_message("INCORRECT CODE", message, color=(200, 50, 50), duration=2)


def _show_message(title, message, color=(0, 150, 0), duration=3):
    """Display a message screen for a specified duration."""
    try:
        screen, images = initialize_screen()

        title_font = pygame.font.SysFont(None, 56)
        message_font = pygame.font.SysFont(None, 36)
        clock = pygame.time.Clock()

        start_time = time.time()

        while time.time() - start_time < duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pygame.quit()
                    return

            screen.fill((255, 255, 255))

            if 'screen_interface' in images:
                screen.blit(images['screen_interface'], (0, 0))
            else:
                pygame.draw.rect(screen, (0, 120, 255), (0, 0, width, 60))
                pygame.draw.rect(screen, (0, 120, 255), (0, height - 40, width, 40))

            title_text = title_font.render(title, True, color)
            title_rect = title_text.get_rect(center=(width // 2, height // 2 - 30))
            screen.blit(title_text, title_rect)

            msg_text = message_font.render(message, True, (50, 50, 50))
            msg_rect = msg_text.get_rect(center=(width // 2, height // 2 + 30))
            screen.blit(msg_text, msg_rect)

            pygame.display.flip()
            clock.tick(fps)

        pygame.quit()

    except Exception as e:
        logging.error(f"(screen.py): Message screen error: {e}")


########## ENTRY POINT ##########

if __name__ == "__main__":
    print("Testing code entry screen...")
    code = run_code_screen(email="test@example.com")
    if code:
        print(f"Entered code: {code}")
    else:
        print("Cancelled")
