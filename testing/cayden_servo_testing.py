import sys
import os
import time

# Add parent directory to path so we can import from utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.servos import set_target


#############################################################
############### FUNDAMENTAL MOVEMENT FUNCTION ###############
#############################################################


########## SERVO 0 (left lid hinge) TEST ###########

def test_servo_0_center():
    """Move servo 0 (left lid hinge) to center position (1500 μs / 90°)"""
    print("\n[Servo 0] Moving to CENTER (1500 μs / 90°)")
    set_target(channel=0, target=1500, speed=200, acceleration=250)
    print("Servo 0 should now be at center position")

def test_servo_0_plus_90():
    """Move servo 0 (left lid hinge) +90° from center (2000 μs / 180°)"""
    print("\n[Servo 0] Moving +90° from center (2000 μs / 180°)")
    set_target(channel=0, target=2000, speed=200, acceleration=250)
    print("Servo 0 should now be rotated +90° from center")

def test_servo_0_minus_90():
    """Move servo 0 (left lid hinge) -90° from center (1000 μs / 0°)"""
    print("\n[Servo 0] Moving -90° from center (1000 μs / 0°)")
    set_target(channel=0, target=1000, speed=200, acceleration=250)
    print("Servo 0 should now be rotated -90° from center")

def test_servo_0_full_range():
    """Sweep servo 0 through full 180° range"""
    print("\n[Servo 0] Full range test: 1000 → 1500 → 2000 → 1500")
    print("Moving to 1000 μs (0°)...")
    set_target(channel=0, target=1000, speed=200, acceleration=250)
    time.sleep(2)

    print("Moving to 1500 μs (90°)...")
    set_target(channel=0, target=1500, speed=200, acceleration=250)
    time.sleep(2)

    print("Moving to 2000 μs (180°)...")
    set_target(channel=0, target=2000, speed=200, acceleration=250)
    time.sleep(2)

    print("Returning to center (1500 μs)...")
    set_target(channel=0, target=1500, speed=200, acceleration=250)
    print("Full range test complete")


########## SERVO 2 (lid lock) TEST ###########

def test_servo_2_center():
    """Move servo 2 (lid lock) to center position (1500 μs / 90°)"""
    print("\n[Servo 2] Moving to CENTER (1500 μs / 90°)")
    set_target(channel=2, target=1500, speed=200, acceleration=250)
    print("Servo 2 should now be at center position")

def test_servo_2_plus_90():
    """Move servo 2 (lid lock) +90° from center (2000 μs / 180°)"""
    print("\n[Servo 2] Moving +90° from center (2000 μs / 180°)")
    set_target(channel=2, target=2000, speed=200, acceleration=250)
    print("Servo 2 should now be rotated +90° from center")

def test_servo_2_minus_90():
    """Move servo 2 (lid lock) -90° from center (1000 μs / 0°)"""
    print("\n[Servo 2] Moving -90° from center (1000 μs / 0°)")
    set_target(channel=2, target=1000, speed=200, acceleration=250)
    print("Servo 2 should now be rotated -90° from center")

def test_servo_2_full_range():
    """Sweep servo 2 through full 180° range"""
    print("\n[Servo 2] Full range test: 1000 → 1500 → 2000 → 1500")
    print("Moving to 1000 μs (0°)...")
    set_target(channel=2, target=1000, speed=200, acceleration=250)
    time.sleep(2)

    print("Moving to 1500 μs (90°)...")
    set_target(channel=2, target=1500, speed=200, acceleration=250)
    time.sleep(2)

    print("Moving to 2000 μs (180°)...")
    set_target(channel=2, target=2000, speed=200, acceleration=250)
    time.sleep(2)

    print("Returning to center (1500 μs)...")
    set_target(channel=2, target=1500, speed=200, acceleration=250)
    print("Full range test complete")


########## CUSTOM POSITION TEST ###########

def test_servo_custom(channel, position): # move any servo to a custom pos

    print(f"\n[Servo {channel}] Moving to custom position: {position} μs")
    set_target(channel=channel, target=position, speed=200, acceleration=250)
    print(f"Servo {channel} moved to {position} μs")


########## MAIN MENU ###########

def show_menu():
    print("\n" + "="*60)
    print("SERVO CALIBRATION MENU")
    print("="*60)
    print("\nServo 0 (Left Lid Hinge):")
    print("  1. Center position (1500 us)")
    print("  2. +90 from center (2000 us)")
    print("  3. -90 from center (1000 us)")
    print("  4. Full range sweep")
    print("\nServo 2 (Lid Lock):")
    print("  5. Center position (1500 us)")
    print("  6. +90 from center (2000 us)")
    print("  7. -90 from center (1000 us)")
    print("  8. Full range sweep")
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
            test_servo_0_center()
        elif choice == "2":
            test_servo_0_plus_90()
        elif choice == "3":
            test_servo_0_minus_90()
        elif choice == "4":
            test_servo_0_full_range()
        elif choice == "5":
            test_servo_2_center()
        elif choice == "6":
            test_servo_2_plus_90()
        elif choice == "7":
            test_servo_2_minus_90()
        elif choice == "8":
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
