import network
import socket
import math
import ujson
import ubinascii
import os
import uasyncio as asyncio
from mpu6050 import MPU6050

# -------------------------------
# WiFi Connection Setup (using APwifi)
# -------------------------------
import APwifi

# -------------------------------
# Non-blocking WebSocket Client Functions
# -------------------------------
async def websocket_connect(host, port):
    """
    Connects to the WebSocket server and performs the handshake asynchronously.
    Returns a (reader, writer) pair or None if the handshake fails.
    """
    try:
        reader, writer = await asyncio.open_connection(host, port)
    except Exception as e:
        print("Error connecting to {}:{} -> {}".format(host, port, e))
        return None

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
    writer.write(handshake.encode())
    await writer.drain()
    
    # Read handshake response
    response = await reader.read(1024)
    if b"101 Switching Protocols" not in response:
        print("WebSocket handshake failed. Received response:")
        print(response)
        writer.close()
        await writer.wait_closed()
        return None

    print("WebSocket handshake successful.")
    return reader, writer

def send_ws_frame(writer, data):
    """
    Sends a WebSocket frame containing text data to the server.
    Note: Client frames must be masked.
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
    writer.write(header + masked_payload)

# -------------------------------
# Sensor Data Processing Functions
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
# Sensor Data Task: Reads sensor data and sends it via WebSocket
# -------------------------------
async def sensor_task(writer, mpu):
    while True:
        try:
            # Read accelerometer and gyroscope data
            accel = mpu.read_accel_data()  # Expected to return a dict {"x": ..., "y": ..., "z": ...}
            gyro = mpu.read_gyro_data()    # Expected to return a dict {"x": ..., "y": ..., "z": ...}
            
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
            send_ws_frame(writer, json_data)
            await writer.drain()
            print("Sensor data sent:", json_data)
            
            # Delay for 50 milliseconds
            await asyncio.sleep(0.05)
        except Exception as e:
            print("Error in sensor task:", e)
            await asyncio.sleep(1)
            # Optionally, reconnect if an error occurs.

# -------------------------------
# Main asynchronous function
# -------------------------------
async def main():
    # Start WiFi connection
    APwifi.start()
    
    # WebSocket server settings; for AP mode, the server IP is usually "192.168.4.1"
    host = "192.168.4.1"  # Change if necessary
    port = 8800

    ws = await websocket_connect(host, port)
    if ws is None:
        print("WebSocket connection failed.")
        return
    reader, writer = ws

    # Create MPU6050 instance to read sensor data
    mpu = MPU6050()

    # Create sensor task to continuously read and send sensor data
    sensor = asyncio.create_task(sensor_task(writer, mpu))
    
    # Await the sensor task (runs indefinitely)
    await sensor

# Run the main function using uasyncio
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program stopped.")
