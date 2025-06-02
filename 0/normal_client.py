import network
import socket
import time
import math
import ujson
import ubinascii
import os
import hashlib
from mpu6050 import MPU6050

# -------------------------------
# WiFi Connection Setup
# -------------------------------
import APwifi

# -------------------------------
# WebSocket Client Functions
# -------------------------------
def websocket_connect(host, port):
    """
    Connects to the WebSocket server and performs the handshake.
    Returns a connected socket or None if handshake fails.
    """
    s = socket.socket()
    s.connect((host, port))
    # Generate a random Sec-WebSocket-Key
    key = ubinascii.b2a_base64(os.urandom(16)).strip().decode()
    handshake = (
        "GET / HTTP/1.1\r\n"
        "Host: {}:{}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: {}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n".format(host, port, key)
    )
    s.send(handshake.encode())
    response = s.recv(1024)
    if b"101 Switching Protocols" not in response:
        print("Handshake failed, response:")
        print(response)
        s.close()
        return None
    print("WebSocket handshake successful.")
    return s

def send_ws_frame(s, data):
    """
    Sends a WebSocket frame with text data to the server.
    Client frames must be masked.
    """
    payload = data.encode('utf-8')
    mask = os.urandom(4)
    masked_payload = bytearray(payload)
    for i in range(len(masked_payload)):
        masked_payload[i] ^= mask[i % 4]
    
    header = bytearray()
    header.append(0x81)  # FIN=1, opcode=1 (text frame)
    length = len(payload)
    if length < 126:
        header.append(0x80 | length)  # set mask bit to 1
    elif length < (1 << 16):
        header.append(0x80 | 126)
        header += length.to_bytes(2, 'big')
    else:
        header.append(0x80 | 127)
        header += length.to_bytes(8, 'big')
    header += mask
    s.send(header + masked_payload)

# -------------------------------
# Sensor Data Processing
# -------------------------------
def calculate_angles(accel_data):
    Ax = accel_data["x"]
    Ay = accel_data["y"]
    Az = accel_data["z"]
    pitch = math.atan2(Ay, math.sqrt(Ax**2 + Az**2)) * 180 / math.pi
    roll = math.atan2(-Ax, math.sqrt(Ay**2 + Az**2)) * 180 / math.pi
    yaw = math.atan2(Ax, Ay) * 180 / math.pi
    return pitch, roll, yaw

# -------------------------------
# Main Client Loop
# -------------------------------
def main():
    APwifi.start()
    
    # تنظیمات سرور وب‌سوکت: در حالت AP، IP سرور معمولاً "192.168.4.1" است
    host = "192.168.4.1"  # در صورت نیاز این مقدار را تغییر دهید
    port = 8800
    
    ws = websocket_connect(host, port)
    if ws is None:
        print("WebSocket connection failed.")
        return
    
    # ایجاد شیء MPU6050 برای خواندن داده‌های شتاب‌سنج
    mpu = MPU6050()
    
    while True:
        try:
            accel = mpu.read_accel_data()  # فرض: برمی‌گرداند دیکشنری {"x": ..., "y": ..., "z": ...}
            gyro = mpu.read_gyro_data()    # فرض: برمی‌گرداند دیکشنری {"x": ..., "y": ..., "z": ...}
            
            pitch, roll, yaw = calculate_angles(accel)
            
            data = {
                "posX": pitch,
                "posY": roll,
                "posZ": yaw,
                "gyroX": gyro.get("x", 0),
                "gyroY": gyro.get("y", 0),
                "gyroZ": gyro.get("z", 0)
            }
            json_data = ujson.dumps(data)
            send_ws_frame(ws, json_data)
            print("Sent sensor data:", json_data)
            time.sleep_ms(50)
        except Exception as e:
            print("Error in main loop:", e)
            time.sleep(1)
            # در صورت بروز خطا، می‌توان اقدام به برقراری مجدد ارتباط کرد.
            
if __name__ == "__main__":
    main()
