import machine  # ایمپورت ماژول machine برای کنترل سخت‌افزار
import time  # ایمپورت ماژول time برای مدیریت زمان و تأخیرها
import math  # ایمپورت ماژول math برای انجام محاسبات ریاضی
import GY25_data  # ایمپورت ماژول GY25_data؛ این ماژول باید تابع main() را فراهم کند که مقدار pitch، roll و yaw را برمی‌گرداند.

# ===============================
# پیکربندی پین‌ها و ثابت‌ها
# ===============================
TRIG_PIN = 28  # تنظیم پین TRIG سنسور اولتراسونیک به پین 28
ECHO_PIN = 27  # تنظیم پین ECHO سنسور اولتراسونیک به پین 27
BUZZER_PIN = 10  # تنظیم پین بوزر به پین 10

# پین‌های درایور موتور L298
IN1_PIN = 4   # تنظیم پین IN1 برای جهت موتور 1 (فرض بر چپ)
IN2_PIN = 5   # تنظیم پین IN2 برای جهت موتور 1
IN3_PIN = 6   # تنظیم پین IN3 برای جهت موتور 2 (فرض بر راست)
IN4_PIN = 7   # تنظیم پین IN4 برای جهت موتور 2
ENA_PIN = 8   # تنظیم پین ENA برای PWM موتور 1 (کنترل سرعت)
ENB_PIN = 9   # تنظیم پین ENB برای PWM موتور 2 (کنترل سرعت)

POT_PIN = 26  # تنظیم پین پتانسیومتر به پین 26 (ADC)

THRESHOLD_ANGLE = 10  # تعریف آستانه زاویه برای منطقه بی‌اثر (Dead Zone)
SMOOTHING_ALPHA = 0.4  # تعریف ضریب فیلتر پایین‌گذر برای صاف کردن سیگنال‌های سنسور

DIAGONAL_FACTOR = 0.01  # تعریف ضریب کاهش سرعت برای موتور در سمت چرخش هنگام حرکت مورب

# ===============================
# راه‌اندازی سنسور اولتراسونیک
# ===============================
trig = machine.Pin(TRIG_PIN, machine.Pin.OUT)  # ایجاد شیء پین برای TRIG و تنظیم آن به خروجی
echo = machine.Pin(ECHO_PIN, machine.Pin.IN)  # ایجاد شیء پین برای ECHO و تنظیم آن به ورودی

def get_distance():
    """فاصله را با استفاده از سنسور اولتراسونیک اندازه‌گیری می‌کند."""
    trig.value(0)  # تنظیم پین TRIG به 0 برای شروع تمیز
    time.sleep_us(2)  # انتظار به مدت 2 میکروثانیه
    trig.value(1)  # فعال کردن پین TRIG برای ارسال پالس
    time.sleep_us(10)  # نگه داشتن پالس به مدت 10 میکروثانیه
    trig.value(0)  # خاموش کردن پالس TRIG

    duration = machine.time_pulse_us(echo, 1, 30000)  # اندازه‌گیری مدت زمان دریافت پالس از ECHO با تایم‌اوت 30000 میکروثانیه
    if duration < 0:  # بررسی خطا در اندازه‌گیری (اگر مدت زمان منفی باشد)
        return None  # در صورت خطا، مقدار None را برمی‌گرداند
    return duration / 58.0  # محاسبه فاصله (سانتی‌متر) با تقسیم مدت زمان بر 58

# ===============================
# راه‌اندازی بوزر با افکت‌های موسیقایی
# ===============================
buzzer = machine.PWM(machine.Pin(BUZZER_PIN))  # ایجاد شیء PWM برای بوزر با استفاده از پین بوزر
buzzer.freq(1000)  # تنظیم فرکانس پیش‌فرض بوزر به 1000 هرتز

def play_melody(melody):
    """
    یک ملودی را پخش می‌کند.
    :param melody: یک لیست از تاپل‌ها (فراوانی به هرتز، مدت زمان به ثانیه).
                   فراوانی 0 به معنای سکوت است.
    """
    for note in melody:  # حلقه بر روی هر نت در ملودی
        freq, duration = note  # جداسازی فراوانی و مدت زمان هر نت
        if freq > 0:  # اگر فراوانی بیشتر از 0 باشد (یعنی نت دارای صدا است)
            buzzer.freq(freq)  # تنظیم فراوانی بوزر به مقدار فراوانی نت
            buzzer.duty_u16(30000)  # تنظیم Duty Cycle بوزر برای تولید صدای قابل شنیدن
        else:  # در صورت سکوت (فراوانی 0)
            buzzer.duty_u16(0)  # خاموش کردن بوزر
        time.sleep(duration)  # انتظار به مدت زمان تعیین شده برای نت
        buzzer.duty_u16(0)  # خاموش کردن بوزر پس از پایان نت
        time.sleep(0.05)  # ایجاد وقفه کوتاه بین نت‌ها (0.05 ثانیه)

def play_sound(pattern):
    """افکت‌های موسیقایی مختلف بوزر را بر اساس الگوی حرکت پخش می‌کند."""
    if pattern == "forward":  # بررسی الگوی حرکت "forward" (حرکت به جلو)
        # ملودی صعودی: A4، B4، C5
        melody = [(440, 0.1), (494, 0.1), (523, 0.1)]  # تعریف ملودی برای حرکت به جلو
    elif pattern == "backward":  # بررسی الگوی حرکت "backward" (حرکت به عقب)
        # ملودی نزولی: C5، B4، A4
        melody = [(523, 0.1), (494, 0.1), (440, 0.1)]  # تعریف ملودی برای حرکت به عقب
    elif pattern == "left":  # بررسی الگوی حرکت "left" (چرخش به چپ)
        # ملودی جذاب برای چرخش به چپ
        melody = [(349, 0.1), (330, 0.1), (294, 0.1)]  # تعریف ملودی برای چرخش به چپ
    elif pattern == "right":  # بررسی الگوی حرکت "right" (چرخش به راست)
        # ملودی جذاب برای چرخش به راست
        melody = [(294, 0.1), (330, 0.1), (349, 0.1)]  # تعریف ملودی برای چرخش به راست
    elif pattern == "northeast":  # بررسی الگوی حرکت "northeast" (حرکت مورب به جلو و راست)
        # ملودی برای حرکت مورب به جلو و راست
        melody = [(440, 0.1), (392, 0.1), (494, 0.1)]  # تعریف ملودی برای حرکت مورب به جلو و راست
    elif pattern == "northwest":  # بررسی الگوی حرکت "northwest" (حرکت مورب به جلو و چپ)
        # ملودی برای حرکت مورب به جلو و چپ
        melody = [(440, 0.1), (349, 0.1), (494, 0.1)]  # تعریف ملودی برای حرکت مورب به جلو و چپ
    elif pattern == "southeast":  # بررسی الگوی حرکت "southeast" (حرکت مورب به عقب و راست)
        # ملودی برای حرکت مورب به عقب و راست
        melody = [(523, 0.1), (392, 0.1), (494, 0.1)]  # تعریف ملودی برای حرکت مورب به عقب و راست
    elif pattern == "southwest":  # بررسی الگوی حرکت "southwest" (حرکت مورب به عقب و چپ)
        # ملودی برای حرکت مورب به عقب و چپ
        melody = [(523, 0.1), (349, 0.1), (494, 0.1)]  # تعریف ملودی برای حرکت مورب به عقب و چپ
    elif pattern == "stop":  # بررسی الگوی حرکت "stop" (توقف)
        # صدای آرام توقف
        melody = [(0, 0.1)]  # تعریف ملودی برای توقف (سکوت)
    else:  # در صورت عدم تطابق الگو
        melody = [(0, 0.1)]  # تعریف ملودی پیش‌فرض (سکوت)
    play_melody(melody)  # فراخوانی تابع play_melody برای پخش ملودی انتخاب‌شده

# ===============================
# کنترل موتور L298
# ===============================
# فرض کنید موتور ۱ در سمت چپ و موتور ۲ در سمت راست قرار دارند.
motor_1_forward = machine.Pin(IN1_PIN, machine.Pin.OUT)  # ایجاد شیء پین برای جهت جلو موتور ۱
motor_1_backward = machine.Pin(IN2_PIN, machine.Pin.OUT)  # ایجاد شیء پین برای جهت عقب موتور ۱
motor_2_forward = machine.Pin(IN3_PIN, machine.Pin.OUT)  # ایجاد شیء پین برای جهت جلو موتور ۲
motor_2_backward = machine.Pin(IN4_PIN, machine.Pin.OUT)  # ایجاد شیء پین برای جهت عقب موتور ۲

motor_1_pwm = machine.PWM(machine.Pin(ENA_PIN))  # ایجاد شیء PWM برای کنترل سرعت موتور ۱ (سمت چپ)
motor_2_pwm = machine.PWM(machine.Pin(ENB_PIN))  # ایجاد شیء PWM برای کنترل سرعت موتور ۲ (سمت راست)

motor_1_pwm.freq(1000)  # تنظیم فرکانس PWM موتور ۱ به 1000 هرتز
motor_2_pwm.freq(1000)  # تنظیم فرکانس PWM موتور ۲ به 1000 هرتز

# ===============================
# راه‌اندازی پتانسیومتر (ADC)
# ===============================
potentiometer = machine.ADC(machine.Pin(POT_PIN))  # ایجاد شیء ADC برای خواندن مقدار پتانسیومتر از پین POT_PIN

def read_potentiometer():
    """مقدار پتانسیومتر را می‌خواند و یک مقدار بین ۰ تا ۶۵۵۳۵ برای PWM برمی‌گرداند."""
    pot_value = potentiometer.read_u16()  # خواندن مقدار پتانسیومتر به صورت عددی بین 0 تا 65535
    return pot_value  # برگرداندن مقدار خوانده‌شده از پتانسیومتر

# -------------------------------
# تابع کمکی: اعمال منطقه بی‌اثر (Dead Zone) بر روی یک مقدار
# -------------------------------
def apply_dead_zone(value, threshold):
    """اگر مقدار مطلق value کمتر از threshold باشد، ۰ برمی‌گرداند؛ در غیر این صورت مقدار اصلی را برمی‌گرداند."""
    if abs(value) < threshold:  # بررسی اینکه آیا مقدار مطلق value کمتر از threshold است
        return 0  # در صورت کوچک بودن مقدار، برگرداندن 0 (اعمال منطقه بی‌اثر)
    return value  # در غیر این صورت، برگرداندن مقدار اصلی

def stop_motors():
    motor_1_forward.value(0)  # غیرفعال کردن جهت جلو موتور ۱
    motor_1_backward.value(0)  # غیرفعال کردن جهت عقب موتور ۱
    motor_2_forward.value(0)  # غیرفعال کردن جهت جلو موتور ۲
    motor_2_backward.value(0)  # غیرفعال کردن جهت عقب موتور ۲
    motor_1_pwm.duty_u16(0)  # تنظیم سرعت موتور ۱ به 0
    motor_2_pwm.duty_u16(0)  # تنظیم سرعت موتور ۲ به 0
    play_sound("stop")  # پخش افکت توقف

def move_forward():
    motor_1_forward.value(1)  # فعال کردن جهت جلو موتور ۱
    motor_1_backward.value(0)  # غیرفعال کردن جهت عقب موتور ۱
    motor_2_forward.value(1)  # فعال کردن جهت جلو موتور ۲
    motor_2_backward.value(0)  # غیرفعال کردن جهت عقب موتور ۲
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۱ به مقدار خوانده‌شده
    motor_2_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۲ به مقدار خوانده‌شده
    play_sound("forward")  # پخش افکت حرکت به جلو

def move_backward():
    motor_1_forward.value(0)  # غیرفعال کردن جهت جلو موتور ۱
    motor_1_backward.value(1)  # فعال کردن جهت عقب موتور ۱
    motor_2_forward.value(0)  # غیرفعال کردن جهت جلو موتور ۲
    motor_2_backward.value(1)  # فعال کردن جهت عقب موتور ۲
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۱ به مقدار خوانده‌شده
    motor_2_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۲ به مقدار خوانده‌شده
    play_sound("backward")  # پخش افکت حرکت به عقب
    time.sleep(0.2)  # توقف به مدت 0.2 ثانیه
    stop_motors()  # توقف موتورها
    time.sleep(0.2)  # توقف اضافی به مدت 0.2 ثانیه

def turn_right():
    # چرخش به صورت محوری برای چرخش در جای خود: استفاده از ملودی "right"
    motor_1_forward.value(1)  # فعال کردن جهت جلو موتور ۱
    motor_1_backward.value(0)  # غیرفعال کردن جهت عقب موتور ۱
    motor_2_forward.value(0)  # غیرفعال کردن جهت جلو موتور ۲
    motor_2_backward.value(1)  # فعال کردن جهت عقب موتور ۲
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۱ به مقدار خوانده‌شده
    motor_2_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۲ به مقدار خوانده‌شده
    play_sound("right")  # پخش افکت چرخش به راست

def turn_left():
    # چرخش به صورت محوری برای چرخش در جای خود: استفاده از ملودی "left"
    motor_1_forward.value(0)  # غیرفعال کردن جهت جلو موتور ۱
    motor_1_backward.value(1)  # فعال کردن جهت عقب موتور ۱
    motor_2_forward.value(1)  # فعال کردن جهت جلو موتور ۲
    motor_2_backward.value(0)  # غیرفعال کردن جهت عقب موتور ۲
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۱ به مقدار خوانده‌شده
    motor_2_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۲ به مقدار خوانده‌شده
    play_sound("left")  # پخش افکت چرخش به چپ

# --- توابع حرکت مورب ---
def move_northeast():
    """
    حرکت به جلو همراه با کمی چرخش به راست.
    موتور چپ با سرعت کامل و موتور راست با سرعت کاهش یافته عمل می‌کند.
    """
    motor_1_forward.value(1)  # فعال کردن جهت جلو موتور ۱
    motor_1_backward.value(0)  # غیرفعال کردن جهت عقب موتور ۱
    motor_2_forward.value(1)  # فعال کردن جهت جلو موتور ۲
    motor_2_backward.value(0)  # غیرفعال کردن جهت عقب موتور ۲
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۱ به سرعت کامل
    motor_2_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))  # تنظیم سرعت موتور ۲ به سرعت کاهش یافته برای چرخش به راست
    play_sound("northeast")  # پخش افکت حرکت مورب به جلو و راست

def move_northwest():
    """
    حرکت به جلو همراه با کمی چرخش به چپ.
    موتور راست با سرعت کامل و موتور چپ با سرعت کاهش یافته عمل می‌کند.
    """
    motor_1_forward.value(1)  # فعال کردن جهت جلو موتور ۱
    motor_1_backward.value(0)  # غیرفعال کردن جهت عقب موتور ۱
    motor_2_forward.value(1)  # فعال کردن جهت جلو موتور ۲
    motor_2_backward.value(0)  # غیرفعال کردن جهت عقب موتور ۲
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))  # تنظیم سرعت موتور ۱ به سرعت کاهش یافته برای چرخش به چپ
    motor_2_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۲ به سرعت کامل
    play_sound("northwest")  # پخش افکت حرکت مورب به جلو و چپ

def move_southeast():
    """
    حرکت به عقب همراه با کمی چرخش به راست.
    موتور چپ با سرعت کامل و موتور راست با سرعت کاهش یافته عمل می‌کند.
    """
    motor_1_forward.value(0)  # غیرفعال کردن جهت جلو موتور ۱
    motor_1_backward.value(1)  # فعال کردن جهت عقب موتور ۱
    motor_2_forward.value(0)  # غیرفعال کردن جهت جلو موتور ۲
    motor_2_backward.value(1)  # فعال کردن جهت عقب موتور ۲
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۱ به سرعت کامل
    motor_2_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))  # تنظیم سرعت موتور ۲ به سرعت کاهش یافته برای چرخش به راست
    play_sound("southeast")  # پخش افکت حرکت مورب به عقب و راست

def move_southwest():
    """
    حرکت به عقب همراه با کمی چرخش به چپ.
    موتور راست با سرعت کامل و موتور چپ با سرعت کاهش یافته عمل می‌کند.
    """
    motor_1_forward.value(0)  # غیرفعال کردن جهت جلو موتور ۱
    motor_1_backward.value(1)  # فعال کردن جهت عقب موتور ۱
    motor_2_forward.value(0)  # غیرفعال کردن جهت جلو موتور ۲
    motor_2_backward.value(1)  # فعال کردن جهت عقب موتور ۲
    speed = read_potentiometer()  # خواندن مقدار سرعت از پتانسیومتر
    motor_1_pwm.duty_u16(int(speed * DIAGONAL_FACTOR))  # تنظیم سرعت موتور ۱ به سرعت کاهش یافته برای چرخش به چپ
    motor_2_pwm.duty_u16(speed)  # تنظیم سرعت موتور ۲ به سرعت کامل
    play_sound("southwest")  # پخش افکت حرکت مورب به عقب و چپ

# ===============================
# حلقه اصلی
# ===============================
def main():
    smoothed_pitch, smoothed_roll, smoothed_yaw = None, None, None  # مقداردهی اولیه مقادیر صاف شده (smoothed) برای pitch، roll و yaw به None

    while True:  # شروع یک حلقه بی‌نهایت برای اجرای مداوم برنامه
        distance = get_distance()  # خواندن فاصله از سنسور اولتراسونیک
        if distance is not None and distance < 20:  # بررسی اینکه فاصله معتبر است و کمتر از 20 سانتی‌متر می‌باشد
            print("Obstacle detected! Distance: {:.1f} cm. Stopping motors.".format(distance))  # چاپ پیغام هشدار برای مانع نزدیک
            stop_motors()  # توقف موتورها در صورت نزدیک بودن مانع
            time.sleep(0.1)  # توقف برنامه به مدت 0.1 ثانیه
            continue  # رفتن به ابتدای حلقه و نادیده گرفتن بقیه کدها در این تکرار

        try:  # تلاش برای خواندن داده‌های سنسور
            pitch, roll, yaw = GY25_data.main()  # دریافت مقادیر pitch، roll و yaw از تابع main ماژول GY25_data
        except Exception as e:  # در صورت بروز خطا هنگام خواندن داده‌های سنسور
            print("Error reading sensor data:", e)  # چاپ پیغام خطا همراه با جزئیات خطا
            time.sleep(0.1)  # توقف برنامه به مدت 0.1 ثانیه
            continue  # رفتن به ابتدای حلقه

        if smoothed_pitch is None:  # بررسی اینکه آیا مقادیر صاف شده قبلاً مقداردهی نشده‌اند
            smoothed_pitch, smoothed_roll, smoothed_yaw = pitch, roll, yaw  # در اولین بار، مقداردهی اولیه با مقادیر خوانده‌شده
        else:
            smoothed_pitch = SMOOTHING_ALPHA * pitch + (1 - SMOOTHING_ALPHA) * smoothed_pitch  # اعمال فیلتر پایین‌گذر بر روی pitch
            smoothed_roll = SMOOTHING_ALPHA * roll + (1 - SMOOTHING_ALPHA) * smoothed_roll  # اعمال فیلتر پایین‌گذر بر روی roll
            smoothed_yaw = SMOOTHING_ALPHA * yaw + (1 - SMOOTHING_ALPHA) * smoothed_yaw  # اعمال فیلتر پایین‌گذر بر روی yaw

        # اعمال منطقه بی‌اثر برای هر محور به صورت جداگانه
        pitch_effective = apply_dead_zone(smoothed_pitch, THRESHOLD_ANGLE)  # اعمال منطقه بی‌اثر بر روی pitch صاف شده
        roll_effective = apply_dead_zone(smoothed_roll, THRESHOLD_ANGLE)  # اعمال منطقه بی‌اثر بر روی roll صاف شده

        # تصمیم‌گیری بر اساس مقادیر موثر جهت تعیین حرکت
        if pitch_effective == 0 and roll_effective == 0:  # اگر هر دو مقدار در منطقه بی‌اثر باشند
            print("Action: Stopping (Dead Zone)")  # چاپ پیغام توقف به دلیل منطقه بی‌اثر
            stop_motors()  # توقف موتورها
        # حرکات مورب (زمانی که هر دو محور مقدار غیر صفر دارند)
        elif pitch_effective > 0 and roll_effective > 0:  # اگر pitch و roll هر دو مثبت باشند
            print("Action: Moving Northeast")  # چاپ پیغام حرکت به سمت شمال شرق
            move_northeast()  # اجرای تابع حرکت مورب به جلو و راست
        elif pitch_effective > 0 and roll_effective < 0:  # اگر pitch مثبت و roll منفی باشند
            print("Action: Moving Northwest")  # چاپ پیغام حرکت به سمت شمال غرب
            move_northwest()  # اجرای تابع حرکت مورب به جلو و چپ
        elif pitch_effective < 0 and roll_effective > 0:  # اگر pitch منفی و roll مثبت باشند
            print("Action: Moving Southeast")  # چاپ پیغام حرکت به سمت جنوب شرق
            move_southeast()  # اجرای تابع حرکت مورب به عقب و راست
        elif pitch_effective < 0 and roll_effective < 0:  # اگر pitch و roll هر دو منفی باشند
            print("Action: Moving Southwest")  # چاپ پیغام حرکت به سمت جنوب غرب
            move_southwest()  # اجرای تابع حرکت مورب به عقب و چپ
        # حرکات ساده زمانی که تنها یکی از محور‌ها فعال باشد
        elif pitch_effective > 0:  # اگر تنها pitch مثبت باشد
            print("Action: Moving forward")  # چاپ پیغام حرکت به جلو
            move_forward()  # اجرای تابع حرکت به جلو
        elif pitch_effective < 0:  # اگر تنها pitch منفی باشد
            print("Action: Moving backward")  # چاپ پیغام حرکت به عقب
            move_backward()  # اجرای تابع حرکت به عقب
        elif roll_effective > 0:  # اگر تنها roll مثبت باشد
            print("Action: Turning right")  # چاپ پیغام چرخش به راست
            turn_right()  # اجرای تابع چرخش به راست
        elif roll_effective < 0:  # اگر تنها roll منفی باشد
            print("Action: Turning left")  # چاپ پیغام چرخش به چپ
            turn_left()  # اجرای تابع چرخش به چپ
        else:
            print("Action: Stopping")  # چاپ پیغام توقف در صورت عدم انطباق شرایط
            stop_motors()  # توقف موتورها

        time.sleep(0.05)  # توقف کوتاه به مدت 0.05 ثانیه برای جلوگیری از بارگذاری بیش از حد حلقه

if __name__ == '__main__':  # بررسی اینکه آیا این اسکریپت به عنوان برنامه اصلی اجرا شده است
    main()  # فراخوانی تابع main برای شروع اجرای برنامه
