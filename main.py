#https://wokwi.com/projects/422213791627018241
import machine  # وارد کردن ماژول machine برای کنترل سخت‌افزار
import time  # وارد کردن ماژول time برای عملکردهای زمانی و تأخیر
import math  # وارد کردن ماژول math برای توابع ریاضی
import GY25_data  # وارد کردن ماژول GY25_data که باید تابع main() را برای برگرداندن pitch، roll و yaw ارائه دهد
import uasyncio as asyncio  # وارد کردن uasyncio برای برنامه‌نویسی غیرهمزمان و نامگذاری آن به asyncio

# ===============================
# پیکربندی پین‌ها و ثوابت
# ===============================
TRIG_PIN = 28  # تعیین شماره پین GPIO برای تریگر سنسور اولتراسونیک (28)
ECHO_PIN = 27  # تعیین شماره پین GPIO برای اکو سنسور اولتراسونیک (27)
BUZZER_PIN = 10  # تعیین شماره پین GPIO برای بیزر (10)

# پین‌های درایور موتور L298
IN1_PIN = 4    # تعیین پین جهت‌دهی موتور ۱ (سمت چپ فرضی) (4)
IN2_PIN = 5    # تعیین پین جهت‌دهی معکوس موتور ۱ (5)
IN3_PIN = 6    # تعیین پین جهت‌دهی موتور ۲ (سمت راست فرضی) (6)
IN4_PIN = 7    # تعیین پین جهت‌دهی معکوس موتور ۲ (7)
ENA_PIN = 8    # تعیین پین PWM برای موتور ۱ (کنترل سرعت) (8)
ENB_PIN = 9    # تعیین پین PWM برای موتور ۲ (کنترل سرعت) (9)

POT_PIN = 26   # تعیین پین GPIO برای پتانسیومتر (ADC) (26)

THRESHOLD_ANGLE = 10  # تعیین آستانه زاویه برای اعمال منطقه مرده (10 درجه)
SMOOTHING_ALPHA = 0.4  # تعیین ضریب فیلتر پایین‌گذر برای صاف‌سازی داده‌های حسگر (0.4)

DIAGONAL_FACTOR = 0.01  # تعیین ضریب کاهش سرعت موتور در سمت چرخش هنگام حرکت مورب (0.01)

# ===============================
# راه‌اندازی سنسور اولتراسونیک
# ===============================
trig = machine.Pin(TRIG_PIN, machine.Pin.OUT)  # مقداردهی اولیه پین تریگر به عنوان خروجی با استفاده از TRIG_PIN
echo = machine.Pin(ECHO_PIN, machine.Pin.IN)  # مقداردهی اولیه پین اکو به عنوان ورودی با استفاده از ECHO_PIN

def get_distance():  # تعریف تابعی برای اندازه‌گیری فاصله با استفاده از سنسور اولتراسونیک
    """اندازه‌گیری فاصله با استفاده از سنسور اولتراسونیک."""  # توضیح عملکرد تابع
    trig.value(0)  # پایین آوردن پین تریگر برای شروع
    time.sleep_us(2)  # انتظار به مدت ۲ میکروثانیه
    trig.value(1)  # بالا بردن پین تریگر برای ارسال پالس
    time.sleep_us(10)  # نگه داشتن پالس به مدت ۱۰ میکروثانیه
    trig.value(0)  # پایین آوردن پین تریگر پس از ارسال پالس
    
    duration = machine.time_pulse_us(echo, 1, 30000)  # اندازه‌گیری مدت زمان پالس برگشتی (تایم‌اوت ۳۰ میلی‌ثانیه)
    if duration < 0:  # بررسی منفی بودن مدت زمان (اشاره به خطا یا تایم‌اوت)
        return None  # بازگرداندن None در صورت بروز خطا
    return duration / 58.0  # تبدیل مدت زمان به فاصله (سانتی‌متر) و بازگرداندن آن

# ===============================
# راه‌اندازی بیزر با افکت‌های موسیقایی
# ===============================
buzzer = machine.PWM(machine.Pin(BUZZER_PIN))  # مقداردهی PWM برای بیزر با استفاده از BUZZER_PIN
buzzer.freq(1000)  # تنظیم فرکانس پیش‌فرض بیزر به ۱۰۰۰ هرتز

async def play_melody(melody):  # تعریف تابع غیرهمزمان برای پخش ملودی
    """
    پخش یک ملودی.
    :param melody: لیستی از تاپل‌ها به صورت (فرکانس به هرتز، مدت زمان به ثانیه).
                   فرکانس 0 نشان‌دهنده توقف است.
    """  # توضیح پارامترها و عملکرد تابع
    for note in melody:  # پیمایش هر نوت در ملودی
        freq, duration = note  # استخراج فرکانس و مدت زمان از تاپل
        if freq > 0:  # در صورت عدم توقف (فرکانس > 0)
            buzzer.freq(freq)  # تنظیم فرکانس بیزر به مقدار فرکانس نوت
            buzzer.duty_u16(30000)  # تنظیم نسبت کار (duty cycle) به 30000 برای تولید صدا
        else:  # در صورت توقف (فرکانس برابر 0)
            buzzer.duty_u16(0)  # خاموش کردن بیزر
        await asyncio.sleep(duration)  # انتظار به مدت زمان نوت
        buzzer.duty_u16(0)  # خاموش کردن بیزر پس از پایان نوت
        await asyncio.sleep(0.05)  # توقف کوتاه بین نوت‌ها (۵۰ میلی‌ثانیه)

async def play_sound(pattern):  # تعریف تابع غیرهمزمان برای پخش افکت صوتی بر اساس الگوی حرکت
    """افکت‌های بیزر موسیقایی مختلف را بر اساس الگوی حرکت پخش می‌کند."""  # توضیح عملکرد تابع
    if pattern == "forward":  # در صورت الگوی حرکت "forward"
        # ملودی صعودی: A4, B4, C5
        melody = [(440, 0.1), (494, 0.1), (523, 0.1)]  # تعریف ملودی برای حرکت به جلو
    elif pattern == "backward":  # در صورت الگوی حرکت "backward"
        # ملودی نزولی: C5, B4, A4
        melody = [(523, 0.1), (494, 0.1), (440, 0.1)]  # تعریف ملودی برای حرکت به عقب
    elif pattern == "left":  # در صورت الگوی حرکت "left"
        # ملودی جذاب برای چرخش به چپ
        melody = [(349, 0.1), (330, 0.1), (294, 0.1)]  # تعریف ملودی برای چرخش به چپ
    elif pattern == "right":  # در صورت الگوی حرکت "right"
        # ملودی جذاب برای چرخش به راست
        melody = [(294, 0.1), (330, 0.1), (349, 0.1)]  # تعریف ملودی برای چرخش به راست
    elif pattern == "northeast":  # در صورت الگوی حرکت "northeast"
        # ملودی برای حرکت مورب به شمال-شرقی
        melody = [(440, 0.1), (392, 0.1), (494, 0.1)]  # تعریف ملودی برای حرکت شمال شرقی
    elif pattern == "northwest":  # در صورت الگوی حرکت "northwest"
        # ملودی برای حرکت مورب به شمال-غربی
        melody = [(440, 0.1), (349, 0.1), (494, 0.1)]  # تعریف ملودی برای حرکت شمال غربی
    elif pattern == "southeast":  # در صورت الگوی حرکت "southeast"
        # ملودی برای حرکت مورب به جنوب-شرقی
        melody = [(523, 0.1), (392, 0.1), (494, 0.1)]  # تعریف ملودی برای حرکت جنوب شرقی
    elif pattern == "southwest":  # در صورت الگوی حرکت "southwest"
        # ملودی برای حرکت مورب به جنوب-غربی
        melody = [(523, 0.1), (349, 0.1), (494, 0.1)]  # تعریف ملودی برای حرکت جنوب غربی
    elif pattern == "stop":  # در صورت الگوی حرکت "stop"
        # صدای آرام توقف
        melody = [(0, 0.1)]  # تعریف ملودی توقف (بی‌صدا)
    else:  # در صورت عدم تطابق الگو
        melody = [(0, 0.1)]  # پیش‌فرض: ملودی توقف (بی‌صدا)
    await play_melody(melody)  # پخش ملودی انتخاب‌شده با فراخوانی تابع play_melody

# ===============================
# کنترل موتور L298
# ===============================
# فرض بر این است که موتور ۱ در سمت چپ و موتور ۲ در سمت راست قرار دارند.
motor_1_forward = machine.Pin(IN1_PIN, machine.Pin.OUT)  # مقداردهی اولیه پین حرکت رو به جلو موتور ۱ به عنوان خروجی
motor_1_backward = machine.Pin(IN2_PIN, machine.Pin.OUT)  # مقداردهی اولیه پین حرکت به عقب موتور ۱ به عنوان خروجی
motor_2_forward = machine.Pin(IN3_PIN, machine.Pin.OUT)  # مقداردهی اولیه پین حرکت رو به جلو موتور ۲ به عنوان خروجی
motor_2_backward = machine.Pin(IN4_PIN, machine.Pin.OUT)  # مقداردهی اولیه پین حرکت به عقب موتور ۲ به عنوان خروجی

motor_1_pwm = machine.PWM(machine.Pin(ENA_PIN))  # مقداردهی اولیه PWM برای موتور ۱ (سمت چپ) با استفاده از پین ENA
motor_2_pwm = machine.PWM(machine.Pin(ENB_PIN))  # مقداردهی اولیه PWM برای موتور ۲ (سمت راست) با استفاده از پین ENB

motor_1_pwm.freq(1000)  # تنظیم فرکانس PWM موتور ۱ به ۱۰۰۰ هرتز
motor_2_pwm.freq(1000)  # تنظیم فرکانس PWM موتور ۲ به ۱۰۰۰ هرتز

# ===============================
# راه‌اندازی پتانسیومتر (ADC)
# ===============================
potentiometer = machine.ADC(machine.Pin(POT_PIN))  # مقداردهی اولیه ADC برای پتانسیومتر متصل به POT_PIN

def read_potentiometer():  # تعریف تابعی برای خواندن مقدار پتانسیومتر
    """مقدار پتانسیومتر را خوانده و مقداری بین 0 تا 65535 برای PWM برمی‌گرداند."""  # توضیح عملکرد تابع
    pot_value = potentiometer.read_u16()  # خواندن مقدار خام ADC از پتانسیومتر (بین 0 تا 65535)
    return pot_value  # بازگرداندن مقدار خوانده‌شده

# -------------------------------
# تابع کمکی: اعمال منطقه مرده به یک مقدار
# -------------------------------
def apply_dead_zone(value, threshold):  # تعریف تابعی برای اعمال منطقه مرده بر روی مقدار داده شده
    """اگر قدر مطلق مقدار کمتر از آستانه باشد، 0 برمی‌گرداند؛ در غیر این صورت همان مقدار را برمی‌گرداند."""  # توضیح عملکرد تابع
    if abs(value) < threshold:  # بررسی اینکه آیا مقدار مطلق کمتر از آستانه است
        return 0  # بازگرداندن 0 در صورت قرار گرفتن در منطقه مرده
    return value  # در غیر این صورت بازگرداندن همان مقدار

# -------------------------------
# توابع حرکت غیرهمزمان
# -------------------------------
async def stop_motors():  # تعریف تابع غیرهمزمان برای توقف تمامی موتورها
    motor_1_forward.value(0)  # پایین آوردن پین حرکت رو به جلو موتور ۱
    motor_1_backward.value(0)  # پایین آوردن پین حرکت به عقب موتور ۱
    motor_2_forward.value(0)  # پایین آوردن پین حرکت رو به جلو موتور ۲
    motor_2_backward.value(0)  # پایین آوردن پین حرکت به عقب موتور ۲
    motor_1_pwm.duty_u16(0)  # تنظیم duty cycle موتور ۱ به 0 برای توقف
    motor_2_pwm.duty_u16(0)  # تنظیم duty cycle موتور ۲ به 0 برای توقف
    await play_sound("stop")  # پخش صدای توقف

async def move_forward():  # تعریف تابع غیرهمزمان برای حرکت به جلو
    motor_1_forward.value(1)  # بالا بردن پین حرکت رو به جلو موتور ۱
    motor_1_backward.value(0)  # پایین نگه داشتن پین حرکت به عقب موتور ۱
    motor_2_forward.value(1)  # بالا بردن پین حرکت رو به جلو موتور ۲
    motor_2_backward.value(0)  # پایین نگه داشتن پین حرکت به عقب موتور ۲
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم duty cycle موتور ۱ بر اساس مقدار پتانسیومتر
    motor_2_pwm.duty_u16(speed)  # تنظیم duty cycle موتور ۲ بر اساس مقدار پتانسیومتر
    await play_sound("forward")  # پخش صدای حرکت به جلو

async def move_backward():  # تعریف تابع غیرهمزمان برای حرکت به عقب
    motor_1_forward.value(0)  # پایین نگه داشتن پین حرکت رو به جلو موتور ۱
    motor_1_backward.value(1)  # بالا بردن پین حرکت به عقب موتور ۱
    motor_2_forward.value(0)  # پایین نگه داشتن پین حرکت رو به جلو موتور ۲
    motor_2_backward.value(1)  # بالا بردن پین حرکت به عقب موتور ۲
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم duty cycle موتور ۱ بر اساس مقدار پتانسیومتر
    motor_2_pwm.duty_u16(speed)  # تنظیم duty cycle موتور ۲ بر اساس مقدار پتانسیومتر
    await play_sound("backward")  # پخش صدای حرکت به عقب
    await asyncio.sleep(0.2)  # انتظار به مدت 0.2 ثانیه
    await stop_motors()  # توقف موتورها پس از حرکت به عقب
    await asyncio.sleep(0.2)  # انتظار به مدت 0.2 ثانیه پس از توقف

async def turn_right():  # تعریف تابع غیرهمزمان برای چرخش در محل به سمت راست
    # چرخش پیکانی برای چرخش در محل: استفاده از ملودی "right"
    motor_1_forward.value(1)  # بالا بردن پین حرکت رو به جلو موتور ۱ برای چرخش
    motor_1_backward.value(0)  # پایین نگه داشتن پین حرکت به عقب موتور ۱
    motor_2_forward.value(0)  # پایین نگه داشتن پین حرکت رو به جلو موتور ۲
    motor_2_backward.value(1)  # بالا بردن پین حرکت به عقب موتور ۲ برای چرخش
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم duty cycle موتور ۱ بر اساس مقدار پتانسیومتر
    motor_2_pwm.duty_u16(speed)  # تنظیم duty cycle موتور ۲ بر اساس مقدار پتانسیومتر
    await play_sound("right")  # پخش صدای چرخش به راست

async def turn_left():  # تعریف تابع غیرهمزمان برای چرخش در محل به سمت چپ
    # چرخش پیکانی برای چرخش در محل: استفاده از ملودی "left"
    motor_1_forward.value(0)  # پایین نگه داشتن پین حرکت رو به جلو موتور ۱
    motor_1_backward.value(1)  # بالا بردن پین حرکت به عقب موتور ۱ برای چرخش
    motor_2_forward.value(1)  # بالا بردن پین حرکت رو به جلو موتور ۲ برای چرخش
    motor_2_backward.value(0)  # پایین نگه داشتن پین حرکت به عقب موتور ۲
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم duty cycle موتور ۱ بر اساس مقدار پتانسیومتر
    motor_2_pwm.duty_u16(speed)  # تنظیم duty cycle موتور ۲ بر اساس مقدار پتانسیومتر
    await play_sound("left")  # پخش صدای چرخش به چپ

# --- توابع حرکت مورب ---
async def move_northeast():  # تعریف تابع غیرهمزمان برای حرکت مورب به سمت شمال شرقی
    """
    حرکت به جلو همراه با کمی چرخش به راست.
    موتور چپ با سرعت کامل و موتور راست با سرعت کاهش‌یافته کار می‌کند.
    """  # توضیح عملکرد حرکت مورب شمال شرقی
    motor_1_forward.value(1)  # بالا بردن پین حرکت رو به جلو موتور چپ
    motor_1_backward.value(0)  # پایین نگه داشتن پین حرکت به عقب موتور چپ
    motor_2_forward.value(1)  # بالا بردن پین حرکت رو به جلو موتور راست
    motor_2_backward.value(0)  # پایین نگه داشتن پین حرکت به عقب موتور راست
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم duty cycle موتور چپ به سرعت کامل
    motor_2_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))  # تنظیم duty cycle موتور راست به سرعت کاهش‌یافته
    await play_sound("northeast")  # پخش صدای حرکت شمال شرقی

async def move_northwest():  # تعریف تابع غیرهمزمان برای حرکت مورب به سمت شمال غربی
    """
    حرکت به جلو همراه با کمی چرخش به چپ.
    موتور راست با سرعت کامل و موتور چپ با سرعت کاهش‌یافته کار می‌کند.
    """  # توضیح عملکرد حرکت مورب شمال غربی
    motor_1_forward.value(1)  # بالا بردن پین حرکت رو به جلو موتور چپ
    motor_1_backward.value(0)  # پایین نگه داشتن پین حرکت به عقب موتور چپ
    motor_2_forward.value(1)  # بالا بردن پین حرکت رو به جلو موتور راست
    motor_2_backward.value(0)  # پایین نگه داشتن پین حرکت به عقب موتور راست
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))  # تنظیم duty cycle موتور چپ به سرعت کاهش‌یافته
    motor_2_pwm.duty_u16(speed)  # تنظیم duty cycle موتور راست به سرعت کامل
    await play_sound("northwest")  # پخش صدای حرکت شمال غربی

async def move_southeast():  # تعریف تابع غیرهمزمان برای حرکت مورب به سمت جنوب شرقی
    """
    حرکت به عقب همراه با کمی چرخش به راست.
    موتور چپ با سرعت کامل و موتور راست با سرعت کاهش‌یافته کار می‌کند.
    """  # توضیح عملکرد حرکت مورب جنوب شرقی
    motor_1_forward.value(0)  # پایین نگه داشتن پین حرکت رو به جلو موتور چپ
    motor_1_backward.value(1)  # بالا بردن پین حرکت به عقب موتور چپ برای حرکت به عقب
    motor_2_forward.value(0)  # پایین نگه داشتن پین حرکت رو به جلو موتور راست
    motor_2_backward.value(1)  # بالا بردن پین حرکت به عقب موتور راست برای حرکت به عقب
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم duty cycle موتور چپ به سرعت کامل (حرکت به عقب)
    motor_2_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))  # تنظیم duty cycle موتور راست به سرعت کاهش‌یافته
    await play_sound("southeast")  # پخش صدای حرکت جنوب شرقی

async def move_southwest():  # تعریف تابع غیرهمزمان برای حرکت مورب به سمت جنوب غربی
    """
    حرکت به عقب همراه با کمی چرخش به چپ.
    موتور راست با سرعت کامل و موتور چپ با سرعت کاهش‌یافته کار می‌کند.
    """  # توضیح عملکرد حرکت مورب جنوب غربی
    motor_1_forward.value(0)  # پایین نگه داشتن پین حرکت رو به جلو موتور چپ
    motor_1_backward.value(1)  # بالا بردن پین حرکت به عقب موتور چپ برای حرکت به عقب
    motor_2_forward.value(0)  # پایین نگه داشتن پین حرکت رو به جلو موتور راست
    motor_2_backward.value(1)  # بالا بردن پین حرکت به عقب موتور راست برای حرکت به عقب
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))  # تنظیم duty cycle موتور چپ به سرعت کاهش‌یافته
    motor_2_pwm.duty_u16(speed)  # تنظیم duty cycle موتور راست به سرعت کامل
    await play_sound("southwest")  # پخش صدای حرکت جنوب غربی

# ===============================
# حلقه اصلی (غیرهمزمان)
# ===============================
async def main():  # تعریف تابع اصلی غیرهمزمان برای حلقه کنترل
    smoothed_pitch, smoothed_roll, smoothed_yaw = None, None, None  # مقداردهی اولیه مقادیر صاف‌شده سنسور به None

    while True:  # شروع حلقه بی‌نهایت برای خواندن مداوم داده‌های حسگر و کنترل موتورها
        distance = get_distance()  # دریافت فاصله از سنسور اولتراسونیک
        if distance is not None and distance < 20:  # اگر فاصله معتبر بوده و کمتر از 20 سانتی‌متر باشد
            print("Obstacle detected! Distance: {:.1f} cm. Stopping motors.".format(distance))  # چاپ پیام هشدار درباره مانع
            await stop_motors()  # توقف فوری موتورها در صورت تشخیص مانع
            await asyncio.sleep(0.1)  # انتظار به مدت 0.1 ثانیه قبل از ادامه حلقه
            continue  # رد کردن بقیه دستورات این دور حلقه در صورت تشخیص مانع

        try:  # تلاش برای خواندن داده‌های حسگر از GY25
            pitch, roll, yaw = GY25_data.main()  # دریافت مقادیر pitch، roll و yaw از تابع main در ماژول GY25_data
        except Exception as e:  # در صورت بروز خطا در خواندن داده‌های حسگر
            print("Error reading sensor data:", e)  # چاپ پیام خطا
            await asyncio.sleep(0.1)  # انتظار به مدت 0.1 ثانیه قبل از تلاش مجدد
            continue  # رد کردن این دور حلقه در صورت خطا

        if smoothed_pitch is None:  # اگر اولین بار است و داده‌های صاف‌شده مقداردهی نشده‌اند
            smoothed_pitch, smoothed_roll, smoothed_yaw = pitch, roll, yaw  # مقداردهی اولیه داده‌های صاف‌شده با مقادیر خوانده‌شده
        else:  # در غیر این صورت، به‌روزرسانی داده‌های صاف‌شده با استفاده از فیلتر پایین‌گذر
            smoothed_pitch = SMOOTHING_ALPHA * pitch + (1 - SMOOTHING_ALPHA) * smoothed_pitch  # صاف‌سازی مقدار pitch
            smoothed_roll = SMOOTHING_ALPHA * roll + (1 - SMOOTHING_ALPHA) * smoothed_roll  # صاف‌سازی مقدار roll
            smoothed_yaw = SMOOTHING_ALPHA * yaw + (1 - SMOOTHING_ALPHA) * smoothed_yaw  # صاف‌سازی مقدار yaw

        # اعمال منطقه مرده به هر محور به‌طور جداگانه
        pitch_effective = apply_dead_zone(smoothed_pitch, THRESHOLD_ANGLE)  # اعمال منطقه مرده به مقدار صاف‌شده pitch
        roll_effective = apply_dead_zone(smoothed_roll, THRESHOLD_ANGLE)  # اعمال منطقه مرده به مقدار صاف‌شده roll

        # تصمیم‌گیری بر اساس مقادیر موثر (پس از اعمال منطقه مرده)
        if pitch_effective == 0 and roll_effective == 0:  # اگر هر دو مقدار pitch و roll در منطقه مرده باشند
            print("Action: Stopping (Dead Zone)")  # چاپ پیام توقف به دلیل منطقه مرده
            await stop_motors()  # توقف تمامی موتورها
        # حرکات مورب (هر دو محور غیر صفر)
        elif pitch_effective > 0 and roll_effective > 0:  # اگر هر دو مقدار pitch و roll مثبت باشند (حرکت مورب به شمال شرقی)
            print("Action: Moving Northeast")  # چاپ پیام حرکت به سمت شمال شرقی
            await move_northeast()  # اجرای تابع حرکت مورب به شمال شرقی
        elif pitch_effective > 0 and roll_effective < 0:  # اگر pitch مثبت و roll منفی باشد (حرکت مورب به شمال غربی)
            print("Action: Moving Northwest")  # چاپ پیام حرکت به سمت شمال غربی
            await move_northwest()  # اجرای تابع حرکت مورب به شمال غربی
        elif pitch_effective < 0 and roll_effective > 0:  # اگر pitch منفی و roll مثبت باشد (حرکت مورب به جنوب شرقی)
            print("Action: Moving Southeast")  # چاپ پیام حرکت به سمت جنوب شرقی
            await move_southeast()  # اجرای تابع حرکت مورب به جنوب شرقی
        elif pitch_effective < 0 and roll_effective < 0:  # اگر هر دو مقدار pitch و roll منفی باشند (حرکت مورب به جنوب غربی)
            print("Action: Moving Southwest")  # چاپ پیام حرکت به سمت جنوب غربی
            await move_southwest()  # اجرای تابع حرکت مورب به جنوب غربی
        # حرکات ساده در صورت فعال بودن تنها یک محور
        elif pitch_effective > 0:  # اگر فقط مقدار pitch مثبت باشد (حرکت به جلو)
            print("Action: Moving forward")  # چاپ پیام حرکت به جلو
            await move_forward()  # اجرای تابع حرکت به جلو
        elif pitch_effective < 0:  # اگر فقط مقدار pitch منفی باشد (حرکت به عقب)
            print("Action: Moving backward")  # چاپ پیام حرکت به عقب
            await move_backward()  # اجرای تابع حرکت به عقب
        elif roll_effective > 0:  # اگر فقط مقدار roll مثبت باشد (چرخش به راست)
            print("Action: Turning right")  # چاپ پیام چرخش به راست
            await turn_right()  # اجرای تابع چرخش به راست
        elif roll_effective < 0:  # اگر فقط مقدار roll منفی باشد (چرخش به چپ)
            print("Action: Turning left")  # چاپ پیام چرخش به چپ
            await turn_left()  # اجرای تابع چرخش به چپ
        else:  # حالت پیش‌فرض (اغلب رخ نمی‌دهد)
            print("Action: Stopping")  # چاپ پیام توقف
            await stop_motors()  # توقف تمامی موتورها
        
        await asyncio.sleep(0.05)  # انتظار به مدت 0.05 ثانیه قبل از شروع دور بعدی حلقه

if __name__ == '__main__':  # بررسی اینکه آیا اسکریپت به عنوان ماژول اصلی اجرا شده است
    asyncio.run(main())  # اجرای حلقه اصلی غیرهمزمان با استفاده از asyncio.run
