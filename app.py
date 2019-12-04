# coding=utf-8
from flask import Flask, render_template, request
import RPi.GPIO as GPIO
import spidev
import time
import threading

# 핀 번호 나열
buzzer_pin = 2
trig = 3
echo = 4

# 모드 설정
GPIO.setmode(GPIO.BCM)

# GPIO 초기화
GPIO.setup(buzzer_pin, GPIO.OUT)
GPIO.setup(trig, GPIO.OUT)
GPIO.setup(echo, GPIO.IN)

# SPI Dev 초기화
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

# 버저 PWM 초기화
p = GPIO.PWM(buzzer_pin, 100)
p.start(0)
p.ChangeDutyCycle(100)

# Ultrasonic 센서의 크기
globalDistance = None


# Photo Resistor 센서에서 값 읽기
def analog_read(channel):
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    adc_out = ((r[1] & 3) << 8) + r[2]
    return adc_out


# 백그라운드에서 Ultrasonic 센서에서
# 값을 읽어. globalDistance에 저장하기
def update_distance():
    global globalDistance
    while True:
        # 현재의 Ultrasonic을 구한다.
        GPIO.output(trig, False)
        time.sleep(0.5)

        GPIO.output(trig, True)
        time.sleep(0.00001)
        GPIO.output(trig, False)

        while GPIO.input(echo) == 0:
            pulse_start = time.time()

        while GPIO.input(echo) == 1:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start
        globalDistance = round(pulse_duration * 17000 * 1000, 2)

        time.sleep(0.2)


app = Flask(__name__)

# 브라우저에서 접속 시
@app.route('/')
def index():
    return render_template('index.html')


# 브라우저에서 피아노 버튼을 눌렀거나 뗐을 때
@app.route('/piano')
def piano_event():
    is_pressed = True if str(request.args.get('press')) == 'true' else False

    if is_pressed:
        frequency = float(str(request.args.get('value')))
        duty_cycle_value = round(globalDistance / 80) - 30
        duty_cycle_value = 0 if duty_cycle_value < 0 else (95 if duty_cycle_value > 95 else duty_cycle_value)

        print(duty_cycle_value)
        p.ChangeDutyCycle(duty_cycle_value)
        p.ChangeFrequency(frequency)

    else:
        p.ChangeDutyCycle(100)

    return 'success'


# 브라우저에서 색 변경을 위해
# Photo Resistor의 값을 읽어올 때
@app.route('/color')
def get_photo_resistor_value():
    reading = analog_read(2)
    voltage = reading * 3.3 / 1024
    return str(voltage)


# 어플리케이션 가동 실행문
t = threading.Thread(target=update_distance)
t.start()
app.run('0.0.0.0', 8080)

GPIO.cleanup()
