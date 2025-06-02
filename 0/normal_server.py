import machine
import time
import math
import ujson
import socket
import ubinascii
import hashlib
import network  # برای تنظیم نقطه اتصال WiFi

# ===============================
# ایجاد نقطه اتصال (Access Point)
# ===============================
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid="CarControlAP", password="12345678")  # تنظیم SSID و PASSWORD
while not ap.active():
    pass
print("Access Point active with IP:", ap.ifconfig()[0])

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

# Potentiometer (for speed control)
POT_PIN = 26  # ADC pin for potentiometer

THRESHOLD_ANGLE = 10
SMOOTHING_ALPHA = 0.4  # Low-pass filter factor
DIAGONAL_FACTOR = 0.7  # To reduce speed for one motor during diagonal moves

# ===============================
# Ultrasonic Sensor Setup (optional for obstacle detection)
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
            buzzer.duty_u16(30000)  # Set duty cycle for an audible tone
        else:
            buzzer.duty_u16(0)
        time.sleep(duration)
        buzzer.duty_u16(0)
        time.sleep(0.05)  # Short pause between notes

def play_sound(pattern):
    """Plays musical effects based on the movement pattern."""
    if pattern == "forward":
        melody = [(440, 0.1), (494, 0.1), (523, 0.1)]  # Ascending: A4, B4, C5
    elif pattern == "backward":
        melody = [(523, 0.1), (494, 0.1), (440, 0.1)]  # Descending: C5, B4, A4
    elif pattern == "left":
        melody = [(349, 0.1), (330, 0.1), (294, 0.1)]  # Attractive melody for left turn
    elif pattern == "right":
        melody = [(294, 0.1), (330, 0.1), (349, 0.1)]  # Attractive melody for right turn
    elif pattern == "northeast":
        melody = [(440, 0.1), (392, 0.1), (494, 0.1)]
    elif pattern == "northwest":
        melody = [(440, 0.1), (349, 0.1), (494, 0.1)]
    elif pattern == "southeast":
        melody = [(523, 0.1), (392, 0.1), (494, 0.1)]
    elif pattern == "southwest":
        melody = [(523, 0.1), (349, 0.1), (494, 0.1)]
    elif pattern == "stop":
        melody = [(0, 0.1)]
    else:
        melody = [(0, 0.1)]
    play_melody(melody)

# ===============================
# L298 Motor Control Setup
# ===============================
motor_1_forward = machine.Pin(IN1_PIN, machine.Pin.OUT)
motor_1_backward = machine.Pin(IN2_PIN, machine.Pin.OUT)
motor_2_forward = machine.Pin(IN3_PIN, machine.Pin.OUT)
motor_2_backward = machine.Pin(IN4_PIN, machine.Pin.OUT)

motor_1_pwm = machine.PWM(machine.Pin(ENA_PIN))
motor_2_pwm = machine.PWM(machine.Pin(ENB_PIN))
motor_1_pwm.freq(1000)
motor_2_pwm.freq(1000)

# ===============================
# Potentiometer Setup (ADC for speed control)
# ===============================
potentiometer = machine.ADC(machine.Pin(POT_PIN))
def read_potentiometer():
    """Returns a value between 0 and 65535 to be used as PWM duty."""
    return potentiometer.read_u16()

# -------------------------------
# Helper: Apply Dead Zone to a value
# -------------------------------
def apply_dead_zone(value, threshold):
    """Returns 0 if the absolute value is below the threshold; otherwise, returns the value."""
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
    motor_1_forward.value(1)
    motor_1_backward.value(0)
    motor_2_forward.value(0)
    motor_2_backward.value(1)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(speed)
    motor_2_pwm.duty_u16(speed)
    play_sound("right")

def turn_left():
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
    motor_1_forward.value(1)
    motor_1_backward.value(0)
    motor_2_forward.value(1)
    motor_2_backward.value(0)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(speed)
    motor_2_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))
    play_sound("northeast")

def move_northwest():
    motor_1_forward.value(1)
    motor_1_backward.value(0)
    motor_2_forward.value(1)
    motor_2_backward.value(0)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))
    motor_2_pwm.duty_u16(speed)
    play_sound("northwest")

def move_southeast():
    motor_1_forward.value(0)
    motor_1_backward.value(1)
    motor_2_forward.value(0)
    motor_2_backward.value(1)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(speed)
    motor_2_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))
    play_sound("southeast")

def move_southwest():
    motor_1_forward.value(0)
    motor_1_backward.value(1)
    motor_2_forward.value(0)
    motor_2_backward.value(1)
    speed = read_potentiometer()
    motor_1_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))
    motor_2_pwm.duty_u16(speed)
    play_sound("southwest")

# ===============================
# WebSocket Handshake and Frame Reception Helpers
# ===============================
def create_accept_key(key):
    GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    sha1 = hashlib.sha1((key + GUID).encode()).digest()
    return ubinascii.b2a_base64(sha1).strip().decode()

def handle_handshake(conn):
    request = conn.recv(1024).decode()
    if 'Sec-WebSocket-Key' not in request:
        return False
    key = request.split('Sec-WebSocket-Key: ')[1].split('\r\n')[0].strip()
    accept_key = create_accept_key(key)
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Accept: {}\r\n\r\n".format(accept_key)
    )
    conn.send(response.encode())
    return True

def websocket_receive(conn):
    """
    Receives a WebSocket frame from the client and returns the payload as a UTF-8 string.
    (This simple implementation assumes payload length < 126 and that client frames are masked.)
    """
    data = conn.recv(1024)
    if not data:
        return None
    payload_length = data[1] & 0x7F
    index = 2
    if payload_length == 126:
        payload_length = int.from_bytes(data[index:index+2], 'big')
        index += 2
    elif payload_length == 127:
        payload_length = int.from_bytes(data[index:index+8], 'big')
        index += 8
    mask = data[index:index+4]
    index += 4
    masked_payload = data[index:index+payload_length]
    payload = bytearray(masked_payload)
    for i in range(len(payload)):
        payload[i] ^= mask[i % 4]
    return payload.decode('utf-8')

# ===============================
# Main WebSocket Server Loop (Control Car)
# ===============================
def main():
    smoothed_pitch, smoothed_roll, smoothed_yaw = None, None, None

    # Set up a simple socket server on port 8800
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 8800))
    s.listen(1)
    print("Control Car WebSocket server started on port 8800.")
    
    while True:
        try:
            conn, addr = s.accept()
            print("New connection from:", addr)
            if not handle_handshake(conn):
                conn.close()
                continue
            print("WebSocket handshake successful. Receiving data...")
            while True:
                ws_data = websocket_receive(conn)
                if ws_data is None:
                    break
                try:
                    sensor_data = ujson.loads(ws_data)
                except Exception as e:
                    print("JSON decode error:", e)
                    continue

                # Mapping received sensor data: posX -> pitch, posY -> roll, posZ -> yaw
                pitch = sensor_data.get("posX", 0)
                roll  = sensor_data.get("posY", 0)
                yaw   = sensor_data.get("posZ", 0)
                
                print("Received sensor data:", sensor_data)
                
                # Smoothing
                if smoothed_pitch is None:
                    smoothed_pitch, smoothed_roll, smoothed_yaw = pitch, roll, yaw
                else:
                    smoothed_pitch = SMOOTHING_ALPHA * pitch + (1 - SMOOTHING_ALPHA) * smoothed_pitch
                    smoothed_roll  = SMOOTHING_ALPHA * roll  + (1 - SMOOTHING_ALPHA) * smoothed_roll
                    smoothed_yaw   = SMOOTHING_ALPHA * yaw   + (1 - SMOOTHING_ALPHA) * smoothed_yaw

                # Apply dead zone to each axis
                pitch_effective = apply_dead_zone(smoothed_pitch, THRESHOLD_ANGLE)
                roll_effective  = apply_dead_zone(smoothed_roll, THRESHOLD_ANGLE)
                
                # Decision-making based on effective values
                if pitch_effective == 0 and roll_effective == 0:
                    print("Action: Stopping (Dead Zone)")
                    stop_motors()
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
        except Exception as e:
            print("Server error:", e)
            time.sleep(1)
        finally:
            try:
                conn.close()
            except:
                pass
            print("Client disconnected, waiting for a new connection...")

if __name__ == '__main__':
    main()
