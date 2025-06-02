# Ali Rashidi
# t.me/WriteYourway

import network
import time
import uasyncio as asyncio             # وارد کردن ماژول uasyncio برای برنامه‌نویسی به‌صورت غیرهمزمان (async)

# اطلاعات شبکه WiFi
SSID = "CarControlAP"  # نام شبکه
PASSWORD = "12345678"  # رمز عبور

# مقداردهی اولیه WLAN
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# تابع اتصال به WiFi
def connect_wifi():
    if wlan.isconnected():
        print("✅ Already connected. IP Address:", wlan.ifconfig()[0])
        return True

    print("\n🔄 Connecting to WiFi...")
    wlan.connect(SSID, PASSWORD)

    timeout = 10  # حداکثر زمان تلاش برای اتصال (ثانیه)
    start_time = time.time()

    while not wlan.isconnected():
        if time.time() - start_time > timeout:
            print("\n❌ Connection timed out!")
            return False
        print(".", end="")
        time.sleep(1)

    wifi_status()
    return True

# بررسی وضعیت WiFi
def wifi_status():
    if wlan.isconnected():
        ip, subnet, gateway, dns = wlan.ifconfig()
        print("📡 WiFi Info:\n")
        print(f"  - IP Address: {ip}")
        print(f"  - Subnet Mask: {subnet}")
        print(f"  - Gateway: {gateway}")
        print(f"  - DNS Server: {dns}")
    else:
        print("❌ Not connected to WiFi")


# تابع غیرهمزمان برای اطمینان از اتصال به WiFi
async def ensure_wifi():
    # در حالی که اتصال WiFi برقرار نیست، تلاش برای اتصال انجام می‌شود
    while not wlan.isconnected():
        print("\n⚠ WiFi lost! Reconnecting...")
        connect_wifi()            # فراخوانی تابع اتصال به WiFi
        await asyncio.sleep(2)         # توقف غیرهمزمان به مدت 2 ثانیه قبل از تلاش مجدد
    # چاپ آدرس IP پس از برقراری اتصال موفق
    print(f"\nWiFi Connected!✅. IP Address:", wlan.ifconfig()[0])
    print(f"\n")

    return True


async def main():
    await ensure_wifi()  


def start():
    asyncio.run(main())    


'''

# تابع غیرهمزمان برای اطمینان از اتصال به WiFi
async def ensure_wifi():
    # در حالی که اتصال WiFi برقرار نیست، تلاش برای اتصال انجام می‌شود
    while not wifi.wlan.isconnected():
        wifi.connect_wifi()            # فراخوانی تابع اتصال به WiFi
        wifi.wifi_status()
        await asyncio.sleep(2)         # توقف غیرهمزمان به مدت 2 ثانیه قبل از تلاش مجدد
    wifi.ensure_wifi_connection()      # بررسی نهایی اتصال و اطمینان از پایداری اتصال
    # چاپ آدرس IP پس از برقراری اتصال موفق
    print("WiFi متصل است. IP Address:", wifi.wlan.ifconfig()[0])
    print(f"\n")


# تابع اصلی غیرهمزمان جهت اجرای هر دو سرور به‌صورت همزمان
async def main():
    await ensure_wifi()   

# ====================== اجرای برنامه ======================
def start():
    asyncio.run(main())  

'''