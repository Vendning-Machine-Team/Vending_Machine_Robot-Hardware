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

##### import config #####

import utilities.config as config

##### import necessary movement / utility functions #####

from behaviors.lid import open_close_cycle
from utilities.motors import stop_all
from utilities.internet import parse_customer_queue_command
from utilities.screen import run_code_screen, show_success_screen





##############################################
############### SALE FUNCTIONS ###############
##############################################


########## SALE ALGORITHM ##########

def handle_sale(codes, sale_in_progress=False): # function to handle a sale from one backend queue payload
    logging.info(f"(sale.py): handle_sale called. codes={'present' if codes else 'None'}\n")

    if codes is not None: # if codes are legit...

        # step 0. set sale in progress to True and stop all movement
        sale_in_progress = True # set sale in progress to True
        if not stop_all():
            logging.warning("(sale.py): stop_all() reported failure — continuing with sale anyway.\n")

        # step 1. separate email and code from code string with new internet function
        email, code = parse_customer_queue_command(codes)
        if code is None:
            logging.warning("(sale.py): Sale payload did not include a valid customer_queue code.\n")
            sale_in_progress = False
            return sale_in_progress

        # step 2. show code entry (handles retries and errors internally)
        logging.info(f"(sale.py): Prompting user to enter code...\n")
        entered_code = run_code_screen(
            email=email,
            code=code,
            max_attempts=config.SALE_CONFIG['MAX_CODE_ATTEMPTS']
        )

        # step 3. correct code — open lid
        if entered_code:
            logging.info(f"(sale.py): Correct code entered. Lid will open and customer can grab purchase.\n")
            show_success_screen("Lid is opening!")
            open_close_cycle()
            sale_in_progress = False

        # step 4. wrong code / max attempts exceeded
        else:
            logging.info(f"(sale.py): Sale ended without correct code. Sale will not be completed.\n")
            sale_in_progress = False

    return sale_in_progress
