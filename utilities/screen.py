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
import threading
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

_qr_stop_event = threading.Event()
_qr_thread = None


########## BUTTON RECTS AND MAPPING ##########

BUTTON_CONFIGS = {
    'button_zero': {'num': '0'},
    'button_one': {'num': '1'},
    'button_two': {'num': '2'},
    'button_three': {'num': '3'},
    'button_four': {'num': '4'},
    'button_five': {'num': '5'},
    'button_six': {'num': '6'},
    'button_seven': {'num': '7'},
    'button_eight': {'num': '8'},
    'button_nine': {'num': '9'},
    'BackSpaceKey': {'action': 'backspace'},
    'EnterKey': {'action': 'enter'},
}





################################################
############### SCREEN FUNCTIONS ###############
################################################


########## PYGAME INITIALIZATION ##########

def initialize_screen():
    """Initialize pygame screen and load images from screen_assets"""

    pygame.init()
    pygame.font.init()

    pygame.mouse.set_visible(True)

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Vending Machine")

    # Use relative path from this file's location to find screen_assets
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    image_folder = os.path.join(project_root, "screen_assets")

    images = {}
    button_rects = {}
    
    if os.path.exists(image_folder):
        for filename in os.listdir(image_folder):
            if filename.endswith(".png"):
                name = filename[:-4]
                img_path = os.path.join(image_folder, filename)
                img = pygame.image.load(img_path).convert_alpha()
                images[name] = img
                
                # Store rect for collision detection if it's a button or control
                if name in BUTTON_CONFIGS or name == 'screen_interface':
                    button_rects[name] = img.get_rect(topleft=(0, 0))
    else:
        logging.warning(f"(screen.py): screen_assets folder not found at {image_folder}")

    return screen, images, button_rects


########## TOUCHSCREEN CODE ENTRY ##########

def run_code_screen(email=None):
    """
    Display code entry screen with touchscreen numpad.
    All buttons are image-based from screen_assets.
    Returns the entered code or None if cancelled.
    """
    logging.info(f"(screen.py): Displaying code entry screen for '{email}'.\n")
    try:
        screen, images, button_rects = initialize_screen()

        current_input = ""
        font = pygame.font.SysFont(None, 48)
        title_font = pygame.font.SysFont(None, 42)
        message_font = pygame.font.SysFont(None, 32)
        clock = pygame.time.Clock()

        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return None

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    
                    # Check which button was touched
                    for button_name, config in BUTTON_CONFIGS.items():
                        if button_name in images:
                            button_img = images[button_name]
                            button_rect = button_img.get_rect(topleft=(0, 0))
                            
                            # Check if touch is within button bounds
                            if button_rect.collidepoint(mouse_pos):
                                # Check alpha channel to see if user touched transparent area
                                if 0 <= mouse_pos[0] < button_rect.width and 0 <= mouse_pos[1] < button_rect.height:
                                    try:
                                        pixel_alpha = button_img.get_at((mouse_pos[0], mouse_pos[1]))[3]
                                        if pixel_alpha > 0:  # Non-transparent pixel
                                            if 'num' in config:
                                                if len(current_input) < 4:
                                                    current_input += config['num']
                                                    logging.debug(f"(screen.py): Code input: {current_input}")
                                            elif config.get('action') == 'backspace':
                                                current_input = current_input[:-1]
                                                logging.debug(f"(screen.py): Backspace pressed. Code: {current_input}")
                                            elif config.get('action') == 'enter':
                                                if current_input:
                                                    logging.info(f"(screen.py): Code entered: {current_input}")
                                                    pygame.quit()
                                                    return current_input
                                    except IndexError:
                                        pass

            # Draw screen
            screen.fill((255, 255, 255))

            ##### LAYER 1: Background interface #####
            if 'screen_interface' in images:
                screen.blit(images['screen_interface'], (0, 0))

            ##### LAYER 2: All button overlays (drawn at their positioned locations) #####
            for button_name in BUTTON_CONFIGS.keys():
                if button_name in images:
                    screen.blit(images[button_name], (0, 0))

            ##### LAYER 3: Text elements (drawn on top of buttons) #####

            # Title text
            title = title_font.render("Enter Verification Code", True, (255, 255, 255))
            title_rect = title.get_rect(center=(width // 2, 25))
            screen.blit(title, title_rect)

            # Email info text
            if email:
                email_text = message_font.render(f"{email}, please enter your code:", True, (255, 255, 255))
                email_rect = email_text.get_rect(center=(width // 2, 45))
                screen.blit(email_text, email_rect)

            # Code display
            code_display = font.render(current_input, True, (0, 0, 0))
            code_rect = code_display.get_rect(center=(width // 2, 125))
            screen.blit(code_display, code_rect)

            pygame.display.flip()
            clock.tick(fps)

        pygame.quit()
        return None

    except Exception as e:
        logging.error(f"(screen.py): Code screen error: {e}")
        return None


########## MESSAGE SCREENS ##########

def show_success_screen(message="Lid is opening!"):
    """Display success message"""
    logging.info(f"(screen.py): Displaying success screen — '{message}'.\n")
    _show_message("SUCCESS!", message, color=(0, 150, 0), duration=3)


def show_error_screen(message="Please try again", attempts_left=0):
    """Display error message"""
    logging.info(f"(screen.py): Displaying error screen — '{message}' ({attempts_left} attempts left).\n")
    if attempts_left > 0:
        message = f"{message} ({attempts_left} attempts left)"
    _show_message("INCORRECT CODE", message, color=(200, 50, 50), duration=2)


def _show_message(title, message, color=(0, 150, 0), duration=3):
    """Display a message screen for a specified duration."""
    try:
        screen, images, _ = initialize_screen()

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


########## QR CODE SCREEN ##########

def show_qr_screen():
    """Display QR code idle screen until stop_qr_screen() is called."""
    logging.info("(screen.py): Displaying QR code screen.\n")
    try:
        screen, images, _ = initialize_screen()
        clock = pygame.time.Clock()

        while not _qr_stop_event.is_set():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            screen.fill((255, 255, 255))

            if 'qr' in images:
                qr_img = images['qr']
                qr_rect = qr_img.get_rect(center=(width // 2, height // 2))
                screen.blit(qr_img, qr_rect)
            else:
                logging.warning("(screen.py): qr.png not found in screen_assets.\n")

            pygame.display.flip()
            clock.tick(fps)

        pygame.quit()

    except Exception as e:
        logging.error(f"(screen.py): QR screen error: {e}\n")


def start_qr_screen():
    """Start the QR code screen in a background thread."""
    global _qr_thread
    _qr_stop_event.clear()
    _qr_thread = threading.Thread(target=show_qr_screen, daemon=True)
    _qr_thread.start()
    logging.info("(screen.py): QR screen thread started.\n")


def stop_qr_screen():
    """Signal QR screen to stop and wait for it to close."""
    global _qr_thread
    _qr_stop_event.set()
    if _qr_thread is not None:
        _qr_thread.join(timeout=1.0)
        _qr_thread = None
    logging.info("(screen.py): QR screen stopped.\n")


########## ENTRY POINT ##########

if __name__ == "__main__":
    print("Testing code entry screen...")
    code = run_code_screen(email="test@example.com")
    if code:
        print(f"Entered code: {code}")
    else:
        print("Cancelled")
