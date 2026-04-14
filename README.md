![Robot In Motion]()

# [Vending Machine Robot](https://github.com/orgs/Vendning-Machine-Team/repositories) - AI / Robotic Behavior Team
### By [Matthew Beck](https://www.linkedin.com/in/matthewthomasbeck/), [Samuel Saylor](), [Cayden Hutcheson](https://www.linkedin.com/in/cayden-hutcheson110), and [Tri Nguyen](https://www.linkedin.com/in/tri-nguyen2/)

**Please consider:** if you like it, **star it!**

## Tech Stack
**Hardware**
- **RaspberryPi 4B** *(computer)*
- **NCS2** *(edge AI chip)*
- **PiCamera Module 3**
- **GPS**
- **Pololu Maestro** *(servo controler)*
- **Dual H-Bridge Motor Driver Module** *(motor controllers)*

**Software**
- **Language:** *Python*
- **Libraries:** *threading, queue, time, os, atexit, socket, logging, collections.deque, subprocess, signal, sys, json, math, random, numpy, opencv-python, openvino, pygame, smbus, RPi.GPIO, pigpio, pyserial*
- **Toolkits:** *OpenVino*

## Roles
**[Matthew Beck](https://github.com/matthewthomasbeck):**
- Software Architect *(architected codebase, set up robot's runtime environment, and oversaw the design and debugging of other engineer's code)*
- Hardware Integrater *(itegrated gps, maestro, camera, AI chip, and motor controllers into the computer's firmware and wrote integration code for other engineers to use)*
- Software Developer *(made AI model code interface, developed socket integration for backend communication, wrote purchase sequence algorithm, wrote robot return-to-home algorithm, and wrote mecanum wheel logic)*

**[Samuel Saylor](https://github.com/SamuelSaylor):**
- Software Developer (collaborated to integrate screen into purchase sequence and collaborated to tune lid open-close logic)

**[Tri Nguyen](https://github.com/Tringuyen2007):**
- Software Developer (wrote AI customer finding logic, wrote AI customer following logic, and tuned movement logic)

**[Cayden Hutcheson](https://github.com/cayden-h):**
- Software Developer (developed lid open-close for purchase sequence, collaborated to integrate screen into purchase sequence, tuned servos, and collaborated to integrate backend for the website, muchin.us)

## Basic Information
The hardware section of the project focused on transforming a collection of individual components into a fully functional, interactive robot. This involved carefully integrating motors, sensors, microcontrollers, and power systems so that each part could communicate and operate in synchronization. Significant attention was given to wiring, power distribution, and physical assembly to ensure reliability during operation. The team also had to troubleshoot issues such as signal interference, inconsistent motor performance, and battery limitations, refining the system until all components worked cohesively.

In addition to internal functionality, the robot was designed to interact seamlessly with an external website that manages user payments and requests. This required establishing a communication pipeline between the robot’s onboard computing system and the web platform, allowing the robot to respond dynamically to user inputs. For example, once a payment is processed through the website, a signal is transmitted to the robot, prompting it to execute a specific behavior or task. Ensuring low latency and consistent connectivity was crucial, as any delay or failure in communication could disrupt the user experience.

Finally, the robot’s mobility and physical presence were key to achieving the project’s goal of attracting attention. The hardware was configured to allow smooth navigation through its environment, whether through programmed paths or remote control. Design considerations such as movement speed, turning precision, and obstacle avoidance played an important role in making the robot both engaging and safe to operate. Altogether, the hardware system not only supports the robot’s core functionality but also enhances its ability to interact with users and operate effectively as part of a larger integrated system.
