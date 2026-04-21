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
import time # import time for sale timeout logic

##### import config #####

import utilities.config as config

##### import necessary movement / utility functions #####

from behaviors.lid import open_close_cycle
from utilities.motors import stop_all
from utilities.internet import parse_customer_queue_command
from utilities.screen import run_code_screen, show_success_screen, show_error_screen





##############################################
############### SALE FUNCTIONS ###############
##############################################


########## SALE ALGORITHM ##########

def handle_sale(codes, sale_in_progress=False): # function to handle a sale from one backend queue payload

    failed_attempts = 0 # initialize failed attempts to 0

    if codes is not None: # if codes are legit...

        # step 0. set sale in progress to True and stop all movement
        sale_in_progress = True # set sale in progress to True
        stopped_successfully = stop_all()

        if not stopped_successfully: # if the movement was not stopped successfully...
            logging.error(f"(control_logic.py): Failed to stop all movement. Sale will not be completed.\n")
            sale_in_progress = False
            return sale_in_progress

        # step 1. separate email and code from code string with new internet function
        email, code = parse_customer_queue_command(codes)
        if code is None:
            logging.warning("(control_logic.py): Sale payload did not include a valid customer_queue code.\n")
            sale_in_progress = False
            return sale_in_progress

        # step 2. display sale interface and ask user to enter code
        entered_code = None
        sale_start_time = time.monotonic() # start timeout timer once sale begins

        # step 3. compare entered code with backend code
        while failed_attempts < config.SALE_CONFIG['MAX_CODE_ATTEMPTS']: # while the user has not tried 3 times and failed...

            if (time.monotonic() - sale_start_time) >= config.SALE_CONFIG['SALE_TIMEOUT_SECONDS']:
                logging.warning(
                    f"(control_logic.py): Sale timed out after {config.SALE_CONFIG['SALE_TIMEOUT_SECONDS']}s "
                    f"(email='{email}'). Canceling sale.\n"
                )
                sale_in_progress = False
                break

            logging.info(f"(control_logic.py): Checking code entered by user...\n")

            # if no user input yet, prompt for code entry
            if entered_code is None:

                logging.info(f"(control_logic.py): Prompting user to enter code...\n")
                entered_code = run_code_screen(email=email)
                
                # if user cancelled or timeout occurred during input
                if entered_code is None:
                    logging.info(f"(control_logic.py): User did not enter code. Waiting for retry or timeout.\n")
                    time.sleep(0.1)
                    continue

            if entered_code == code: # if the entered code is correct...

                logging.info(f"(control_logic.py): Correct code entered. Lid will open and customer can grab purchase.\n")

                # step 3.0 display success message
                show_success_screen("Lid is opening!")

                # step 3.1 call lid.py open_close_cycle() to open the lid and let
                open_close_cycle() # open the lid and let the customer grab their purchase (unfortunately uses honor system atm)

                # step 3.2 set SALE_IN_PROGRESS to False
                sale_in_progress = False

                # step 3.3 break out of while loop
                break

            else: # if the entered code is incorrect...

                logging.info(f"(control_logic.py): Incorrect code entered. {config.SALE_CONFIG['MAX_CODE_ATTEMPTS'] - failed_attempts} attempts remaining.\n")

                # step 3.0 display error message with remaining attempts
                show_error_screen("Please try again", config.SALE_CONFIG['MAX_CODE_ATTEMPTS'] - failed_attempts - 1)

                failed_attempts += 1
                entered_code = None # reset so UI can prompt again

        # step 4. if user has tried MAX_CODE_ATTEMPTS times and failed, display error message and set SALE_IN_PROGRESS to False
        if failed_attempts >= config.SALE_CONFIG['MAX_CODE_ATTEMPTS']:
            logging.info(f"(control_logic.py): Incorrect code entered {config.SALE_CONFIG['MAX_CODE_ATTEMPTS']} times. Sale will not be completed.\n")

            # step 6.0 display error message
            show_error_screen("Too many attempts. Sale cancelled.")

            sale_in_progress = False

    return sale_in_progress
