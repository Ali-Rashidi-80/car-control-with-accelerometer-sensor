import machine
import time
import math
import GY25_data  # This module should provide a main() function returning pitch, roll, and yaw.

# ===============================
# Pin Configurations and Constants
# ===============================
TRIG_PIN = 28
ECHO_PIN = 27
BUZZER_PIN = 10  # Buzzer pin

# L298 Motor Driver Pins
IN1_PIN = 4   # Motor 1 direction pin (assumed LEFT motor)
IN2_PIN = 5   # Motor 1 direction pin
IN3_PIN = 6   # Motor 2 direction pin (assumed RIGHT motor)
IN4_PIN = 7   # Motor 2 direction pin
ENA_PIN = 8   # Motor 1 PWM (Speed)
ENB_PIN = 9   # Motor 2 PWM (Speed)

POT_PIN = 26  # Potentiometer connected to GPIO 26 (ADC)

THRESHOLD_ANGLE = 10
SMOOTHING_ALPHA = 0.4  # Low-pass filter factor

DIAGONAL_FACTOR = 0.01  # Factor to reduce speed for the motor on the turning side during diagonal movement

# ===============================
# Ultrasonic Sensor Setup
# ===============================
trig = machine.Pin(TRIG_PIN, machine.Pin.OUT)
echo = machine.Pin(ECHO_PIN, machine.Pin.IN)

def get_distance():
    """Measures distance using the ultrasonic sensor."""
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    
    duration = machine.time_pulse_us(echo, 1, 30000)  # Timeout 30ms
    if duration < 0:
        return None
    return duration / 58.0

# ===============================
# Buzzer Setup with Musical Effects
# ===============================
buzzer = machine.PWM(machine.Pin(BUZZER_PIN))
buzzer.freq(1000)  # Default frequency

def play_melody(melody):
    """
    Plays a melody.
    :param melody: A list of tuples (frequency in Hz, duration in seconds).
                   A frequency of 0 indicates a rest.
    """
    for note in melody:
        freq, duration = note
        if freq > 0:
            buzzer.freq(freq)
            buzzer.duty_u16(30000)  # Set duty cycle for audible tone
        else:
            buzzer.duty_u16(0)
        time.sleep(duration)
        buzzer.duty_u16(0)
        time.sleep(0.05)  # Short pause between notes

def play_sound(pattern):
    """Plays different musical buzzer effects based on movement pattern."""
    if pattern == "forward":
        # Ascending melody: A4, B4, C5
        melody = [(440, 0.1), (494, 0.1), (523, 0.1)]
    elif pattern == "backward":
        # Descending melody: C5, B4, A4
        melody = [(523, 0.1), (494, 0.1), (440, 0.1)]
    elif pattern == "left":
        # Attractive melody for turning left
        melody = [(349, 0.1), (330, 0.1), (294, 0.1)]
    elif pattern == "right":
        # Attractive melody for turning right
        melody = [(294, 0.1), (330, 0.1), (349, 0.1)]
    elif pattern == "northeast":
        # Melody for diagonal forward-right movement
        melody = [(440, 0.1), (392, 0.1), (494, 0.1)]
    elif pattern == "northwest":
        # Melody for diagonal forward-left movement
        melody = [(440, 0.1), (349, 0.1), (494, 0.1)]
    elif pattern == "southeast":
        # Melody for diagonal backward-right movement
        melody = [(523, 0.1), (392, 0.1), (494, 0.1)]
    elif pattern == "southwest":
        # Melody for diagonal backward-left movement
        melody = [(523, 0.1), (349, 0.1), (494, 0.1)]
    elif pattern == "stop":
        # A gentle rest sound
        melody = [(0, 0.1)]
    else:
        melody = [(0, 0.1)]
    play_melody(melody)

# ===============================
# L298 Motor Control
# ===============================
# Assume Motor 1 is on the LEFT side and Motor 2 is on the RIGHT side.
motor_1_forward = machine.Pin(IN1_PIN, machine.Pin.OUT)
motor_1_backward = machine.Pin(IN2_PIN, machine.Pin.OUT)
motor_2_forward = machine.Pin(IN3_PIN, machine.Pin.OUT)
motor_2_backward = machine.Pin(IN4_PIN, machine.Pin.OUT)

motor_1_pwm = machine.PWM(machine.Pin(ENA_PIN))  # PWM for Motor 1 (LEFT)
motor_2_pwm = machine.PWM(machine.Pin(ENB_PIN))  # PWM for Motor 2 (RIGHT)

motor_1_pwm.freq(1000)  # Set PWM frequency
motor_2_pwm.freq(1000)  # Set PWM frequency

# ===============================
# Potentiometer Setup (ADC)
# ===============================
potentiometer = machine.ADC(machine.Pin(POT_PIN))

def read_potentiometer():
    """Reads the potentiometer value and returns a value between 0 and 65535 for PWM."""
    pot_value = potentiometer.read_u16()  # Read potentiometer value (0-65535)
    return pot_value

# -------------------------------
# Helper: Apply Dead Zone to a value
# -------------------------------
def apply_dead_zone(value, threshold):
    """Returns 0 if abs(value) is below threshold; otherwise returns value."""
    if abs(value) < threshold:
        return 0
    return value

def stop_motors():
    motor_1_forward.value(0)
    motor_1_backward.value(0)
    motor_2_forward.value(0)
    motor_2_backward.value(0)
    motor_1_pwm.duty_u16(0)
    motor_2_pwm.duty_u16(0)
    play_sound("stop")

def move_forward():
    motor_1_forward.value(1)
    motor_1_backward.value(0)
    motor_2_forward.value(1)
    motor_2_backward.value(0)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(speed)
    motor_2_pwm.duty_u16(speed)
    play_sound("forward")

def move_backward():
    motor_1_forward.value(0)
    motor_1_backward.value(1)
    motor_2_forward.value(0)
    motor_2_backward.value(1)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(speed)
    motor_2_pwm.duty_u16(speed)
    play_sound("backward")
    time.sleep(0.2)
    stop_motors()
    time.sleep(0.2)

def turn_right():
    # Pivot turn for in-place turning: use "right" melody
    motor_1_forward.value(1)
    motor_1_backward.value(0)
    motor_2_forward.value(0)
    motor_2_backward.value(1)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(speed)
    motor_2_pwm.duty_u16(speed)
    play_sound("right")

def turn_left():
    # Pivot turn for in-place turning: use "left" melody
    motor_1_forward.value(0)
    motor_1_backward.value(1)
    motor_2_forward.value(1)
    motor_2_backward.value(0)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(speed)
    motor_2_pwm.duty_u16(speed)
    play_sound("left")

# --- Diagonal Movement Functions ---
def move_northeast():
    """
    Move forward while turning right slightly.
    Left motor runs at full speed; right motor at reduced speed.
    """
    motor_1_forward.value(1)
    motor_1_backward.value(0)
    motor_2_forward.value(1)
    motor_2_backward.value(0)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(speed)
    motor_2_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))
    play_sound("northeast")

def move_northwest():
    """
    Move forward while turning left slightly.
    Right motor runs at full speed; left motor at reduced speed.
    """
    motor_1_forward.value(1)
    motor_1_backward.value(0)
    motor_2_forward.value(1)
    motor_2_backward.value(0)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))
    motor_2_pwm.duty_u16(speed)
    play_sound("northwest")

def move_southeast():
    """
    Move backward while turning right slightly.
    Left motor runs at full speed; right motor at reduced speed.
    """
    motor_1_forward.value(0)
    motor_1_backward.value(1)
    motor_2_forward.value(0)
    motor_2_backward.value(1)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(speed)
    motor_2_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))
    play_sound("southeast")

def move_southwest():
    """
    Move backward while turning left slightly.
    Right motor runs at full speed; left motor at reduced speed.
    """
    motor_1_forward.value(0)
    motor_1_backward.value(1)
    motor_2_forward.value(0)
    motor_2_backward.value(1)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))
    motor_2_pwm.duty_u16(speed)
    play_sound("southwest")

# ===============================
# Main Loop
# ===============================
def main():
    smoothed_pitch, smoothed_roll, smoothed_yaw = None, None, None

    while True:
        distance = get_distance()
        if distance is not None and distance < 20:
            print("Obstacle detected! Distance: {:.1f} cm. Stopping motors.".format(distance))
            stop_motors()
            time.sleep(0.1)
            continue

        try:
            pitch, roll, yaw = GY25_data.main()
        except Exception as e:
            print("Error reading sensor data:", e)
            time.sleep(0.1)
            continue

        if smoothed_pitch is None:
            smoothed_pitch, smoothed_roll, smoothed_yaw = pitch, roll, yaw
        else:
            smoothed_pitch = SMOOTHING_ALPHA * pitch + (1 - SMOOTHING_ALPHA) * smoothed_pitch
            smoothed_roll = SMOOTHING_ALPHA * roll + (1 - SMOOTHING_ALPHA) * smoothed_roll
            smoothed_yaw = SMOOTHING_ALPHA * yaw + (1 - SMOOTHING_ALPHA) * smoothed_yaw

        # Apply dead zone to each axis separately
        pitch_effective = apply_dead_zone(smoothed_pitch, THRESHOLD_ANGLE)
        roll_effective = apply_dead_zone(smoothed_roll, THRESHOLD_ANGLE)

        # Decision-making based on effective values
        if pitch_effective == 0 and roll_effective == 0:
            print("Action: Stopping (Dead Zone)")
            stop_motors()
        # Diagonal movements (both axes non-zero)
        elif pitch_effective > 0 and roll_effective > 0:
            print("Action: Moving Northeast")
            move_northeast()
        elif pitch_effective > 0 and roll_effective < 0:
            print("Action: Moving Northwest")
            move_northwest()
        elif pitch_effective < 0 and roll_effective > 0:
            print("Action: Moving Southeast")
            move_southeast()
        elif pitch_effective < 0 and roll_effective < 0:
            print("Action: Moving Southwest")
            move_southwest()
        # Pure movements if only one axis is active
        elif pitch_effective > 0:
            print("Action: Moving forward")
            move_forward()
        elif pitch_effective < 0:
            print("Action: Moving backward")
            move_backward()
        elif roll_effective > 0:
            print("Action: Turning right")
            turn_right()
        elif roll_effective < 0:
            print("Action: Turning left")
            turn_left()
        else:
            print("Action: Stopping")
            stop_motors()
        
        time.sleep(0.05)

if __name__ == '__main__':
    main()
