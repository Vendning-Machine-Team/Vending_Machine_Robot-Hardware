# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the hardware integration and edge AI codebase for an autonomous vending machine robot. The robot uses a Raspberry Pi with mecanum wheels for omnidirectional movement, a camera for computer vision, and runs person detection inference locally using OpenVINO on an Intel Myriad VPU.

## Key Architecture Components

### Main Control Loop (`control_logic.py`)

The central state machine that orchestrates all robot behavior:

- **Initialization** (`set_real_robot_dependencies`): Sets up camera process, backend socket connection, command queue, person detection model (SSDLite MobileNetV2), and motor controllers
- **Physical Loop** (`_physical_loop`): Main control loop that continuously reads camera frames, runs person detection inference, processes commands from backend queue, and controls motor behavior
- **Person Detection State Machine**: Uses debouncing logic to prevent motor chattering:
  - Requires `PERSON_DETECTED_FRAMES_TO_START` consecutive detections before moving
  - Requires `PERSON_ABSENT_FRAMES_TO_STOP` consecutive non-detections before stopping
  - Enforces minimum move time (`PERSON_MIN_MOVE_SECONDS`) and hold time (`PERSON_ABSENT_HOLD_SECONDS`)
- **Command Handling** (`_handle_command`, `_execute_commands`): Processes keyboard commands from backend (WASD for movement, arrow keys for rotation/tilt), with support for diagonal movement and command chaining via `+`
- **State Variables**: `IS_COMPLETE` blocks new commands during movement, `IS_NEUTRAL` tracks idle state, `PERSON_STATE_MOVING` tracks motor activation

### Motor Control System

**DC Motor Controllers** (`utilities/motors.py`):
- Uses pigpio library for hardware PWM control
- Two dual-channel motor controllers (LEFT_DCMC and RIGHT_DCMC) control four mecanum wheels (FL, FR, BL, BR)
- Motor configuration in `utilities/config.py` (MOTOR_CONFIG) defines GPIO pin mappings and orientation flags
- `initialize_motor_controllers()`: Sets up pigpio connection, configures GPIO pins, builds motor name index
- `move_motor(motor_name, direction, intensity)`: High-level API accepting motor name ('FL', 'FR', 'BL', 'BR'), direction ('clockwise', 'counterclockwise', 'stop'), and intensity (1-10)
- Orientation flag in config maps logical directions to electrical forward/reverse for each motor
- `stop_all()`: Emergency stop registered with atexit

**Mecanum Drive Logic** (`movement/mecanum.py`):
- `drive(x, y, r, intensity)`: Master drive function with x (strafe), y (forward/back), r (rotation), intensity (0-10)
- `drive_polar(angle_deg, magnitude, rotation, intensity)`: Alternative angle-based interface
- Cardinal directions: `forward()`, `backward()`, `strafe_left()`, `strafe_right()`
- Rotation: `rotate_left()`, `rotate_right()`
- Diagonals: `diagonal_front_left()`, `diagonal_front_right()`, `diagonal_back_left()`, `diagonal_back_right()`
- Arc movements: `arc_left()`, `arc_right()`
- `set_wheel_speeds(fl, fr, bl, br, max_intensity)`: Normalizes wheel values and applies to all four motors

**Servo Control** (`utilities/servos.py`, `utilities/maestro.py`):
- Maestro servo controller via serial (`/dev/serial0` at 9600 baud)
- `set_target(channel, target, speed, acceleration)`: Sends Pololu protocol commands to Maestro
- `map_angle_to_servo_position(angle, joint_data)`: Maps angles to PWM microsecond values using FULL_BACK_ANGLE/FULL_FRONT_ANGLE ranges

### Computer Vision Pipeline

**Camera** (`utilities/camera.py`):
- Uses rpicam-vid subprocess to capture MJPEG stream from Raspberry Pi camera
- `initialize_camera()`: Kills existing rpicam processes, starts new rpicam-vid process with specified resolution/framerate
- `decode_real_frame()`: Parses MJPEG stream by finding JPEG markers (`\xff\xd8` start, `\xff\xd9` end), decodes with OpenCV
- Returns both streamed frame (for backend transmission) and inference frame (for local processing)
- Supports RL preprocessing mode (crop, grayscale, resize) when `config.RL_NOT_CNN = True`

**Inference** (`utilities/inference.py`):
- **Person Detection**: `run_person_detection()` uses SSDLite MobileNetV2 compiled for Myriad VPU
  - Input: 256x256 RGB image
  - Draws bounding boxes and confidence scores on frame
  - Returns boolean `person_detected` flag when confidence > 0.5
- **Model Loading**: `load_and_compile_model()` uses OpenVINO Core API to compile `.xml` models for specified device (default: MYRIAD)
- **Gait Adjustment RL** (stub): `run_gait_adjustment_blind()` designed for imageless RL-based gait control using historical position/orientation state

### Backend Communication

**Internet** (`utilities/internet.py`):
- `initialize_backend_socket()`: Connects TCP socket to backend EC2 instance (IP/port from `INTERNET_CONFIG`)
- `listen_for_commands()`: Background thread that receives length-prefixed command strings from backend and enqueues them
- `stream_to_backend()`: Sends length-prefixed MJPEG frames to backend for web streaming
- Uses thread lock (`_send_lock`) to prevent concurrent socket writes

### Configuration

**Config** (`utilities/config.py`):
- `CONTROL_MODE`: 'web' (backend commands) or 'radio' (unused)
- `LOOP_RATE_HZ`: Target loop rate (30 Hz, deprecated/legacy)
- `LOG_CONFIG`: Log file path and level
- `CAMERA_CONFIG`: Resolution, frame rate, FOV, crop settings
- `INFERENCE_CONFIG`: TPU device name ('MYRIAD'), CNN model path
- `MOTOR_CONFIG`: Detailed GPIO pin mappings, PWM frequency, motor-to-controller-channel mappings, orientation flags
- `INTERNET_CONFIG`: Backend IP, port, API URL

## Important Wiring Details

**DC Motors** (from MOTOR_CONFIG comments in `utilities/config.py`):
- **LEFT_DCMC**: GPIO 17/27 (channel A → FL), GPIO 22/23 (channel B → BL)
- **RIGHT_DCMC**: GPIO 5/6 (channel A → BR), GPIO 20/21 (channel B → FR)
- Each controller has two channels (A, B) with two direction pins (IN1, IN2) per channel
- Orientation flag (1 or -1) determines whether clockwise motion is forward or reverse for that wheel

**Maestro Servo Controller**: Connected to `/dev/serial0` at 9600 baud (channels 0-11)

**Camera**: Raspberry Pi Camera Module v2 via rpicam-vid

**Intel Myriad VPU**: Used for OpenVINO inference acceleration

## Running the Robot

**Prerequisites:**
- pigpio daemon must be running: `sudo pigpiod`
- OpenVINO environment must be sourced (paths in `vending_machine.service.d`)

**Starting the robot:**
```bash
# Run directly with virtual environment
/home/matthewthomasbeck/.virtualenvs/openvino/bin/python control_logic.py

# Or via systemd service (production)
sudo systemctl start vending_machine.service
sudo systemctl status vending_machine.service
```

**Service configuration:**
- Service file: `vending_machine.service.d`
- Pre-start cleanup: Kills existing `control_logic.py`, rpicam processes, and releases `/dev/serial0`
- Environment: OpenVINO virtual environment with PYTHONPATH and LD_LIBRARY_PATH for OpenVINO libs

**Logs:**
- Log file: `/home/matthewthomasbeck/Projects/Vending_Machine_Robot-Hardware/vending_machine.log`
- Initialized in `utilities/log.py`, level configured in `utilities/config.py`

## Command Interface

**Control mode:** Set `CONTROL_MODE = 'web'` in config

**Commands from backend** (received via socket as strings):
- `'w'`: Forward
- `'s'`: Backward
- `'a'`: Strafe left
- `'d'`: Strafe right
- `'arrowleft'`: Rotate left
- `'arrowright'`: Rotate right
- `'arrowup'`: Tilt up
- `'arrowdown'`: Tilt down
- `'w+a'`, `'w+d'`, `'s+a'`, `'s+d'`: Diagonal movements
- `'n'`: Return to neutral/stop
- `'i'`: Toggle imageless gait mode

Commands are processed by `_execute_commands()` which converts them to motor actions via mecanum drive functions.

## Development Notes

**Motor orientation tuning:**
- If a wheel spins the wrong direction, flip its ORIENTATION flag in MOTOR_CONFIG (1 ↔ -1)
- Recent commits adjusted rear motor orientations to match engineer's plans

**Person detection behavior:**
- Adjust debouncing constants at top of `control_logic.py` to tune responsiveness vs. stability
- Currently: 1 frame to start, 24 frames to stop, 0.6s minimum move time, 0.5s hold after detection

**Backend communication:**
- Backend EC2 IP configured in `INTERNET_CONFIG['BACKEND_PUBLIC_IP']`
- Recent commits updated IP endpoint for socket connection and switched to code queue from backend

**Common gotchas:**
- Always run `sudo pigpiod` before starting robot control
- Ensure no other processes hold `/dev/serial0` (maestro serial port)
- Camera can only have one rpicam-vid instance running; initialization kills existing processes
- Motor chattering was resolved by tuning person detection debouncing parameters

**Testing motor groups:**
- `run_front_motors(intensity)`: Test FL and FR motors only
- `run_back_motors(intensity)`: Test BL and BR motors only
- Useful for wiring/orientation verification

## License

Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0). Personal and educational use permitted; commercial use prohibited.
