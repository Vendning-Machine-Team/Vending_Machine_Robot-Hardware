import sys
import os
import time

# Add parent directory to path so we can import from utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.servos import set_target
from utilities.config import LID_CONFIG, LID_LOCK_CONFIG


def resolve_hinge_target(side, state):
    """Match production lid target resolution for consistent testing."""
    direction_key = f"{side}_HINGE_DIRECTION"
    if direction_key not in LID_CONFIG:
        explicit_key = f"{state}_POSITION_{side}"
        if explicit_key in LID_CONFIG:
            return LID_CONFIG[explicit_key]

    min_pos = LID_CONFIG.get('MIN_POSITION', 1000)
    max_pos = LID_CONFIG.get('MAX_POSITION', 2000)
    if state == 'OPEN':
        base_target = LID_CONFIG.get('BASE_OPEN_POSITION', LID_CONFIG.get('OPEN_POSITION_LEFT', max_pos))
    else:
        base_target = LID_CONFIG.get('BASE_CLOSED_POSITION', LID_CONFIG.get('CLOSED_POSITION_LEFT', min_pos))

    direction = LID_CONFIG.get(direction_key, 1)
    if direction >= 0:
        return base_target

    return (min_pos + max_pos) - base_target


#############################################################
############### FUNDAMENTAL MOVEMENT FUNCTION ###############
#############################################################


########## SERVO 0 (left lid hinge) TEST ###########

def test_servo_0_closed():
    """Move servo 0 (left lid hinge) to CLOSED position"""
    pos = resolve_hinge_target('LEFT', 'CLOSED')
    print(f"\n[Servo 0] Moving to CLOSED ({pos} μs)")
    set_target(channel=LID_CONFIG['LEFT_HINGE_CHANNEL'], target=pos,
               speed=LID_CONFIG['SPEED'], acceleration=LID_CONFIG['ACCELERATION'])

def test_servo_0_open():
    """Move servo 0 (left lid hinge) to OPEN position"""
    pos = resolve_hinge_target('LEFT', 'OPEN')
    print(f"\n[Servo 0] Moving to OPEN ({pos} μs)")
    set_target(channel=LID_CONFIG['LEFT_HINGE_CHANNEL'], target=pos,
               speed=LID_CONFIG['SPEED'], acceleration=LID_CONFIG['ACCELERATION'])

def test_servo_0_full_range():
    """Sweep servo 0 between closed and open"""
    closed = resolve_hinge_target('LEFT', 'CLOSED')
    opened = resolve_hinge_target('LEFT', 'OPEN')
    print(f"\n[Servo 0] Full range test: CLOSED ({closed}) → OPEN ({opened}) → CLOSED ({closed})")

    print(f"Moving to CLOSED ({closed} μs)...")
    set_target(channel=LID_CONFIG['LEFT_HINGE_CHANNEL'], target=closed,
               speed=LID_CONFIG['SPEED'], acceleration=LID_CONFIG['ACCELERATION'])
    time.sleep(2)

    print(f"Moving to OPEN ({opened} μs)...")
    set_target(channel=LID_CONFIG['LEFT_HINGE_CHANNEL'], target=opened,
               speed=LID_CONFIG['SPEED'], acceleration=LID_CONFIG['ACCELERATION'])
    time.sleep(2)

    print(f"Returning to CLOSED ({closed} μs)...")
    set_target(channel=LID_CONFIG['LEFT_HINGE_CHANNEL'], target=closed,
               speed=LID_CONFIG['SPEED'], acceleration=LID_CONFIG['ACCELERATION'])
    print("Full range test complete")


########## SERVO 1 (right lid hinge) TEST ###########

def test_servo_1_closed():
    """Move servo 1 (right lid hinge) to CLOSED position"""
    pos = resolve_hinge_target('RIGHT', 'CLOSED')
    print(f"\n[Servo 1] Moving to CLOSED ({pos} μs)")
    set_target(channel=LID_CONFIG['RIGHT_HINGE_CHANNEL'], target=pos,
               speed=LID_CONFIG['SPEED'], acceleration=LID_CONFIG['ACCELERATION'])

def test_servo_1_open():
    """Move servo 1 (right lid hinge) to OPEN position"""
    pos = resolve_hinge_target('RIGHT', 'OPEN')
    print(f"\n[Servo 1] Moving to OPEN ({pos} μs)")
    set_target(channel=LID_CONFIG['RIGHT_HINGE_CHANNEL'], target=pos,
               speed=LID_CONFIG['SPEED'], acceleration=LID_CONFIG['ACCELERATION'])

def test_servo_1_full_range():
    """Sweep servo 1 between closed and open"""
    closed = resolve_hinge_target('RIGHT', 'CLOSED')
    opened = resolve_hinge_target('RIGHT', 'OPEN')
    print(f"\n[Servo 1] Full range test: CLOSED ({closed}) → OPEN ({opened}) → CLOSED ({closed})")

    print(f"Moving to CLOSED ({closed} μs)...")
    set_target(channel=LID_CONFIG['RIGHT_HINGE_CHANNEL'], target=closed,
               speed=LID_CONFIG['SPEED'], acceleration=LID_CONFIG['ACCELERATION'])
    time.sleep(2)

    print(f"Moving to OPEN ({opened} μs)...")
    set_target(channel=LID_CONFIG['RIGHT_HINGE_CHANNEL'], target=opened,
               speed=LID_CONFIG['SPEED'], acceleration=LID_CONFIG['ACCELERATION'])
    time.sleep(2)

    print(f"Returning to CLOSED ({closed} μs)...")
    set_target(channel=LID_CONFIG['RIGHT_HINGE_CHANNEL'], target=closed,
               speed=LID_CONFIG['SPEED'], acceleration=LID_CONFIG['ACCELERATION'])
    print("Full range test complete")


########## SERVO 2 (lid lock) TEST ###########

def test_servo_2_locked():
    """Move servo 2 (lid lock) to LOCKED position"""
    pos = LID_LOCK_CONFIG['LOCKED_POSITION']
    print(f"\n[Servo 2] Moving to LOCKED ({pos} μs)")
    set_target(channel=LID_LOCK_CONFIG['LOCK_CHANNEL'], target=pos,
               speed=LID_LOCK_CONFIG['SPEED'], acceleration=LID_LOCK_CONFIG['ACCELERATION'])

def test_servo_2_unlocked():
    """Move servo 2 (lid lock) to UNLOCKED position"""
    pos = LID_LOCK_CONFIG['UNLOCKED_POSITION']
    print(f"\n[Servo 2] Moving to UNLOCKED ({pos} μs)")
    set_target(channel=LID_LOCK_CONFIG['LOCK_CHANNEL'], target=pos,
               speed=LID_LOCK_CONFIG['SPEED'], acceleration=LID_LOCK_CONFIG['ACCELERATION'])

def test_servo_2_full_range():
    """Sweep servo 2 between locked and unlocked"""
    locked = LID_LOCK_CONFIG['LOCKED_POSITION']
    unlocked = LID_LOCK_CONFIG['UNLOCKED_POSITION']
    print(f"\n[Servo 2] Full range test: LOCKED ({locked}) → UNLOCKED ({unlocked}) → LOCKED ({locked})")

    print(f"Moving to LOCKED ({locked} μs)...")
    set_target(channel=LID_LOCK_CONFIG['LOCK_CHANNEL'], target=locked,
               speed=LID_LOCK_CONFIG['SPEED'], acceleration=LID_LOCK_CONFIG['ACCELERATION'])
    time.sleep(2)

    print(f"Moving to UNLOCKED ({unlocked} μs)...")
    set_target(channel=LID_LOCK_CONFIG['LOCK_CHANNEL'], target=unlocked,
               speed=LID_LOCK_CONFIG['SPEED'], acceleration=LID_LOCK_CONFIG['ACCELERATION'])
    time.sleep(2)

    print(f"Returning to LOCKED ({locked} μs)...")
    set_target(channel=LID_LOCK_CONFIG['LOCK_CHANNEL'], target=locked,
               speed=LID_LOCK_CONFIG['SPEED'], acceleration=LID_LOCK_CONFIG['ACCELERATION'])
    print("Full range test complete")


########## CUSTOM POSITION TEST ###########

def test_servo_custom(channel, position):
    """Move any servo to a custom pos"""
    print(f"\n[Servo {channel}] Moving to custom position: {position} μs")
    set_target(channel=channel, target=position, speed=200, acceleration=250)
    print(f"Servo {channel} moved to {position} μs")


########## MAIN MENU ###########

def show_menu():
    left_closed = resolve_hinge_target('LEFT', 'CLOSED')
    left_open = resolve_hinge_target('LEFT', 'OPEN')
    right_closed = resolve_hinge_target('RIGHT', 'CLOSED')
    right_open = resolve_hinge_target('RIGHT', 'OPEN')

    print("\n" + "="*60)
    print("SERVO CALIBRATION MENU")
    print("="*60)
    print(f"\nServo 0 (Left Lid Hinge) "
          f"[CLOSED={left_closed}, OPEN={left_open}]:")
    print("  1. Closed position")
    print("  2. Open position")
    print("  3. Full range sweep")
    print(f"\nServo 1 (Right Lid Hinge) "
          f"[CLOSED={right_closed}, OPEN={right_open}]:")
    print("  4. Closed position")
    print("  5. Open position")
    print("  6. Full range sweep")
    print(f"\nServo 2 (Lid Lock) "
          f"[LOCKED={LID_LOCK_CONFIG['LOCKED_POSITION']}, UNLOCKED={LID_LOCK_CONFIG['UNLOCKED_POSITION']}]:")
    print("  7. Locked position")
    print("  8. Unlocked position")
    print("  A. Full range sweep")
    print("\nCustom:")
    print("  9. Custom position")
    print("  0. Exit")
    print("="*60)


def main():
    print("\nServo Calibration Tool")
    print("Use this to test and calibrate servo positions\n")

    while True:
        show_menu()
        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            test_servo_0_closed()
        elif choice == "2":
            test_servo_0_open()
        elif choice == "3":
            test_servo_0_full_range()
        elif choice == "4":
            test_servo_1_closed()
        elif choice == "5":
            test_servo_1_open()
        elif choice == "6":
            test_servo_1_full_range()
        elif choice == "7":
            test_servo_2_locked()
        elif choice == "8":
            test_servo_2_unlocked()
        elif choice.lower() == "a":
            test_servo_2_full_range()
        elif choice == "9":
            try:
                channel = int(input("Enter servo channel (0-11): "))
                position = int(input("Enter position in microseconds (1000-2000): "))
                test_servo_custom(channel, position)
            except ValueError:
                print("Invalid input. Please enter numbers only.")
        elif choice == "0":
            print("\nExiting calibration tool...")
            break
        else:
            print("\nInvalid choice. Please try again.")

        time.sleep(0.5)


if __name__ == "__main__":
    main()
