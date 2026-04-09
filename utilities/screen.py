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
import socket
import json

# Add parent directory to path so we can import from utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

##### import necessary functions #####

from utilities.config import SCREEN_CONFIG, INTERNET_CONFIG


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


########## KEYBOARD LAYOUT ##########

KEYBOARD_ROWS = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
    ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', '@'],
    ['z', 'x', 'c', 'v', 'b', 'n', 'm', '.', '_', '-'],
    ['SPACE', 'BACKSPACE', 'SUBMIT']
]

def draw_keyboard(screen, font, start_y):
    """Draw on-screen keyboard and return button rects"""
    button_rects = {}
    key_width = 60
    key_height = 50
    padding = 5

    for row_idx, row in enumerate(KEYBOARD_ROWS):
        # Calculate row width to center it
        if row_idx == 4:  # Special row with larger keys
            row_width = 3 * 120 + 2 * padding
        else:
            row_width = len(row) * (key_width + padding) - padding

        start_x = (width - row_width) // 2
        y = start_y + row_idx * (key_height + padding)

        for key_idx, key in enumerate(row):
            if row_idx == 4:  # Special keys row
                if key == 'SPACE':
                    key_w = 120
                    x = start_x
                elif key == 'BACKSPACE':
                    key_w = 120
                    x = start_x + 125
                else:  # SUBMIT
                    key_w = 120
                    x = start_x + 250
            else:
                key_w = key_width
                x = start_x + key_idx * (key_width + padding)

            rect = pygame.Rect(x, y, key_w, key_height)
            button_rects[key] = rect

            # Draw key background
            pygame.draw.rect(screen, (200, 200, 200), rect)
            pygame.draw.rect(screen, (100, 100, 100), rect, 2)

            # Draw key label
            if key == 'SPACE':
                label = 'SPACE'
            elif key == 'BACKSPACE':
                label = '<--'
            elif key == 'SUBMIT':
                label = 'OK'
            else:
                label = key.upper()

            text = font.render(label, True, (0, 0, 0))
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

    return button_rects


########## NUMPAD LAYOUT ##########

def draw_numpad(screen, font, images, start_y):
    """Draw numpad using button images or fallback rectangles"""
    button_rects = {}

    # Check if we have button images (they're full-screen overlays)
    button_names = [name for name in images.keys() if name.startswith('button_')]

    if button_names:
        # Use the pre-positioned button images
        for name in button_names:
            screen.blit(images[name], (0, 0))

        # Create click detection rects based on image pixel positions
        # Return images dict for pixel-based detection
        return {'use_images': True, 'images': images, 'button_names': button_names}

    else:
        # Fallback: draw simple numpad
        key_width = 80
        key_height = 60
        padding = 10

        numpad = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['CLEAR', '0', 'SUBMIT']
        ]

        grid_width = 3 * key_width + 2 * padding
        start_x = (width - grid_width) // 2

        for row_idx, row in enumerate(numpad):
            y = start_y + row_idx * (key_height + padding)
            for key_idx, key in enumerate(row):
                x = start_x + key_idx * (key_width + padding)
                rect = pygame.Rect(x, y, key_width, key_height)
                button_rects[key] = rect

                # Draw key
                color = (0, 150, 0) if key == 'SUBMIT' else (200, 50, 50) if key == 'CLEAR' else (200, 200, 200)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (100, 100, 100), rect, 2)

                text = font.render(key if len(key) <= 2 else key[:3], True, (0, 0, 0))
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)

        return button_rects


########## EMAIL ENTRY SCREEN ##########

def run_email_screen():
    """
    Display email entry screen with on-screen keyboard.
    Returns the entered email address or None if cancelled.
    """
    try:
        screen, images = initialize_screen()

        current_input = ""
        font = pygame.font.SysFont(None, 36)
        title_font = pygame.font.SysFont(None, 48)
        clock = pygame.time.Clock()

        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return None

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos

                    # Check keyboard buttons
                    for key, rect in button_rects.items():
                        if rect.collidepoint(mouse_x, mouse_y):
                            if key == 'SPACE':
                                current_input += ' '
                            elif key == 'BACKSPACE':
                                current_input = current_input[:-1]
                            elif key == 'SUBMIT':
                                if '@' in current_input and '.' in current_input:
                                    logging.info(f"(screen.py): Email entered: {current_input}")
                                    return current_input
                                else:
                                    # Flash error - invalid email
                                    pass
                            else:
                                current_input += key
                            break

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        current_input = current_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if '@' in current_input and '.' in current_input:
                            return current_input
                    elif event.unicode and event.unicode.isprintable():
                        current_input += event.unicode

            # Draw screen
            screen.fill((255, 255, 255))

            # Draw background interface if available
            if 'screen_interface' in images:
                screen.blit(images['screen_interface'], (0, 0))
            else:
                # Draw blue header/footer
                pygame.draw.rect(screen, (0, 120, 255), (0, 0, width, 60))
                pygame.draw.rect(screen, (0, 120, 255), (0, height - 40, width, 40))

            # Draw title in blue header area
            title = title_font.render("Enter Your Email", True, (255, 255, 255))
            title_rect = title.get_rect(center=(width // 2, 30))
            screen.blit(title, title_rect)

            # Draw input box
            input_box = pygame.Rect(50, 70, width - 100, 50)
            pygame.draw.rect(screen, (255, 255, 255), input_box)
            pygame.draw.rect(screen, (0, 0, 0), input_box, 2)

            # Draw current input
            input_text = font.render(current_input, True, (0, 0, 0))
            screen.blit(input_text, (input_box.x + 10, input_box.y + 10))

            # Draw blinking cursor
            if int(time.time() * 2) % 2:
                cursor_x = input_box.x + 10 + input_text.get_width()
                pygame.draw.line(screen, (0, 0, 0), (cursor_x, input_box.y + 10), (cursor_x, input_box.y + 40), 2)

            # Draw keyboard
            button_rects = draw_keyboard(screen, font, 140)

            pygame.display.flip()
            clock.tick(fps)

        pygame.quit()
        return None

    except Exception as e:
        logging.error(f"(screen.py): Email screen error: {e}")
        print(f"Email screen error: {e}")
        return None


########## CODE ENTRY SCREEN ##########

def run_code_screen(email=None, max_attempts=3):
    """
    Display code entry screen with numpad.
    Returns the entered code or None if cancelled/max attempts reached.
    """
    try:
        screen, images = initialize_screen()

        current_input = ""
        attempts = 0
        message = ""
        message_color = (0, 0, 0)

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

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        current_input = current_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if current_input:
                            logging.info(f"(screen.py): Code entered: {current_input}")
                            return current_input
                    elif event.key == pygame.K_ESCAPE:
                        current_input = ""
                    elif event.unicode.isdigit():
                        current_input += event.unicode

            # Draw screen
            screen.fill((255, 255, 255))

            # Draw background interface
            if 'screen_interface' in images:
                screen.blit(images['screen_interface'], (0, 0))
            else:
                pygame.draw.rect(screen, (0, 120, 255), (0, 0, width, 60))
                pygame.draw.rect(screen, (0, 120, 255), (0, height - 40, width, 40))

            # Draw title
            title = title_font.render("Enter Verification Code", True, (255, 255, 255))
            title_rect = title.get_rect(center=(width // 2, 30))
            screen.blit(title, title_rect)

            # Draw email info if provided
            if email:
                email_text = message_font.render(f"Code sent to: {email}", True, (50, 50, 50))
                email_rect = email_text.get_rect(center=(width // 2, 70))
                screen.blit(email_text, email_rect)

            # Draw code input display (in the input box area)
            code_display = font.render(current_input if current_input else "_ _ _ _ _ _", True, (0, 0, 0))
            code_rect = code_display.get_rect(center=(width // 2, 115))
            screen.blit(code_display, code_rect)

            # Draw numpad buttons (overlay images)
            button_names = [name for name in images.keys() if name.startswith('button_')]
            for name in button_names:
                screen.blit(images[name], (0, 0))

            # Draw message if any
            if message:
                msg_text = message_font.render(message, True, message_color)
                msg_rect = msg_text.get_rect(center=(width // 2, height - 60))
                screen.blit(msg_text, msg_rect)

            # Draw submit/clear buttons at bottom
            submit_rect = pygame.Rect(width // 2 + 20, height - 80, 150, 40)
            clear_rect = pygame.Rect(width // 2 - 170, height - 80, 150, 40)

            pygame.draw.rect(screen, (0, 150, 0), submit_rect)
            pygame.draw.rect(screen, (200, 50, 50), clear_rect)

            submit_text = message_font.render("SUBMIT", True, (255, 255, 255))
            clear_text = message_font.render("CLEAR", True, (255, 255, 255))

            screen.blit(submit_text, submit_text.get_rect(center=submit_rect.center))
            screen.blit(clear_text, clear_text.get_rect(center=clear_rect.center))

            # Check for submit/clear clicks
            if pygame.mouse.get_pressed()[0]:
                mouse_pos = pygame.mouse.get_pos()
                if submit_rect.collidepoint(mouse_pos) and current_input:
                    pygame.time.wait(200)  # Debounce
                    return current_input
                elif clear_rect.collidepoint(mouse_pos):
                    current_input = ""
                    pygame.time.wait(200)

            pygame.display.flip()
            clock.tick(fps)

        pygame.quit()
        return None

    except Exception as e:
        logging.error(f"(screen.py): Code screen error: {e}")
        print(f"Code screen error: {e}")
        return None


########## MESSAGE SCREENS ##########

def show_message_screen(title, message, color=(0, 150, 0), duration=3):
    """
    Display a message screen for a specified duration.
    color: (0, 150, 0) for success green, (200, 50, 50) for error red
    """
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
                    # Tap to dismiss early
                    pygame.quit()
                    return

            # Draw screen
            screen.fill((255, 255, 255))

            # Draw background
            if 'screen_interface' in images:
                screen.blit(images['screen_interface'], (0, 0))
            else:
                pygame.draw.rect(screen, (0, 120, 255), (0, 0, width, 60))
                pygame.draw.rect(screen, (0, 120, 255), (0, height - 40, width, 40))

            # Draw title
            title_text = title_font.render(title, True, color)
            title_rect = title_text.get_rect(center=(width // 2, height // 2 - 30))
            screen.blit(title_text, title_rect)

            # Draw message
            msg_text = message_font.render(message, True, (50, 50, 50))
            msg_rect = msg_text.get_rect(center=(width // 2, height // 2 + 30))
            screen.blit(msg_text, msg_rect)

            pygame.display.flip()
            clock.tick(fps)

        pygame.quit()

    except Exception as e:
        logging.error(f"(screen.py): Message screen error: {e}")


def show_success_screen(message="Lid is opening!"):
    """Display success message"""
    show_message_screen("SUCCESS!", message, color=(0, 150, 0), duration=3)


def show_error_screen(message="Please try again", attempts_left=0):
    """Display error message"""
    if attempts_left > 0:
        message = f"{message} ({attempts_left} attempts left)"
    show_message_screen("INCORRECT CODE", message, color=(200, 50, 50), duration=2)


########## BACKEND INTEGRATION ##########

def request_verification_code(email):
    """
    Send email to backend to request a verification code.
    Returns True if successful, False otherwise.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((INTERNET_CONFIG['BACKEND_PUBLIC_IP'], INTERNET_CONFIG['BACKEND_PORT']))

        # Create request payload
        payload = json.dumps({
            'type': 'request_code',
            'email': email
        })

        # Send length-prefixed message
        payload_bytes = payload.encode('utf-8')
        sock.sendall(len(payload_bytes).to_bytes(4, 'big'))
        sock.sendall(payload_bytes)

        sock.close()
        logging.info(f"(screen.py): Verification code requested for {email}")
        return True

    except Exception as e:
        logging.error(f"(screen.py): Failed to request verification code: {e}")
        return False


########## FULL SALE FLOW ##########

def run_sale_interface():
    """
    Run the complete sale interface flow:
    1. Get email from user
    2. Request verification code from backend
    3. Get code from user
    4. Return the entered code for verification

    Returns: (email, entered_code) tuple, or (None, None) if cancelled
    """
    # Step 1: Get email
    email = run_email_screen()
    if not email:
        return None, None

    # Step 2: Request code from backend
    show_message_screen("Sending Code...", f"Sending to {email}", color=(0, 120, 255), duration=1)
    success = request_verification_code(email)

    if not success:
        show_error_screen("Failed to send code. Check connection.")
        return None, None

    show_message_screen("Code Sent!", "Check your email", color=(0, 150, 0), duration=2)

    # Step 3: Get verification code
    code = run_code_screen(email=email)
    if not code:
        return email, None

    return email, code


########## ENTRY POINT ##########

if __name__ == "__main__":
    print("Starting sale interface test...")
    email, code = run_sale_interface()

    if email and code:
        print(f"Email: {email}")
        print(f"Code: {code}")
    else:
        print("Sale cancelled or failed")
