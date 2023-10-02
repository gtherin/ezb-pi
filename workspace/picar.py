import ezblock
import time
import numpy as np
from ezblock.user_info import USER, USER_HOME


class PiCar(object):
    PERIOD = 4095
    PRESCALER = 10
    TIMEOUT = 0.02

    state = {"P7": 0, "P6": 0, "P0": 0, "P1": 0, "P2": 0}
    calib = {"P7": 0, "P6": 0, "P0": 0, "P1": 0, "P2": 3}

    def __init__(self):

        self.servos = {k: ezblock.Servo(ezblock.PWM(k)) for k in PiCar.state.keys()}

        self.config_flie = ezblock.fileDB(f'{USER_HOME}/.config')

        for k, v in PiCar.state.items():
            self.servos[k].angle(v)

        self.left_rear_pwm_pin = ezblock.PWM("P13")
        self.right_rear_pwm_pin = ezblock.PWM("P12")
        self.left_rear_dir_pin = ezblock.Pin("D4")
        self.right_rear_dir_pin = ezblock.Pin("D5")

        self.pin_D0 = ezblock.Pin("D0")
        self.pin_D1 = ezblock.Pin("D1")
        self.ultrasonic = ezblock.Ultrasonic(self.pin_D0, self.pin_D1)

        self.S0 = ezblock.ADC('A0')
        self.S1 = ezblock.ADC('A1')
        self.S2 = ezblock.ADC('A2')

        self.motor_direction_pins = [self.left_rear_dir_pin, self.right_rear_dir_pin]
        self.motor_speed_pins = [self.left_rear_pwm_pin, self.right_rear_pwm_pin]
        self.cali_dir_value = self.config_flie.get("picarx_dir_motor", default_value="[1,1]")
        self.cali_dir_value = [int(i.strip()) for i in self.cali_dir_value.strip("[]").split(",")]
        self.cali_speed_value = [0, 0]

        for pin in self.motor_speed_pins:
            pin.period(self.PERIOD)
            pin.prescaler(self.PRESCALER)

    def set_motor_speed(self, motor, speed):
        # global cali_speed_value,cali_dir_value
        motor -= 1
        if speed >= 0:
            direction = 1 * self.cali_dir_value[motor]
        elif speed < 0:
            direction = -1 * self.cali_dir_value[motor]
        speed = abs(speed)
        if speed != 0:
            speed = int(speed / 2) + 50
        speed = speed - self.cali_speed_value[motor]
        if direction < 0:
            self.motor_direction_pins[motor].high()
            self.motor_speed_pins[motor].pulse_width_percent(speed)
        else:
            self.motor_direction_pins[motor].low()
            self.motor_speed_pins[motor].pulse_width_percent(speed)

    def motor_speed_calibration(self, value):
        if value < 0:
            self.cali_speed_value[0] = 0
            self.cali_speed_value[1] = abs(value)
        else:
            self.cali_speed_value[0] = abs(value)
            self.cali_speed_value[1] = 0

    def motor_direction_calibration(self, motor, value):
        # 0: positive direction
        # 1:negative direction
        # global cali_dir_value
        motor -= 1
        if value == 1:
            self.cali_dir_value[motor] = -1 * self.cali_dir_value[motor]
        self.config_flie.set("picarx_dir_motor", self.cali_dir_value)

    def set_steering_angle(self, value):
        self.state["P2"] = value
        angle_value = value + self.calib["P2"]
        if angle_value != 0:
            print("angle_value:", round(angle_value, 2))
        self.servos["P2"].angle(angle_value)

    def set_camera_pan_angle(self, value):
        self.set_servo_angle("P0", -1*(value + -1*self.state["P0"]), sum=False)

    def set_camera_tilt_angle(self, value):
        self.set_servo_angle("P1", -1*(value + -1*self.state["P1"]), sum=False)

    def set_servo_angle(self, sid, angle, sum=True):

        angle = int(angle)
        if sid in ["UP", "RIGHT", "VERTICAL", "HORIZONTAL"]:
            angle *= -1

        if sid in ["PAN", "HOR", "LEFT", "RIGHT", "HORIZONTAL"]:
            sid = "P0"
        if sid in ["TILT", "VER", "DOWN", "UP", "VERTICAL"]:
            sid = "P1"
        if sid in ["DIR", "STEER"]:
            sid = "P2"

        # P7 cap 90
        ideal_angle = self.state[sid] + angle if sum else angle
        ideal_angle = int(np.clip(ideal_angle, -45, 45))

        self.state[sid] = ideal_angle
        print(f"{sid}, {angle}, {self.state[sid]}")
        self.servos[sid].angle(self.state[sid])
        return self.state[sid]

    def get_distance(self):
        return self.ultrasonic.read()

    def get_grayscale_data(self):
        my_3ch = [self.S0.read(), self.S1.read(), self.S2.read()]
        print("%s"%my_3ch)

    def set_power(self, speed):
        self.set_motor_speed(1, speed)
        self.set_motor_speed(2, speed)

    def backward(self, speed):
        current_angle = self.state["P2"]
        if current_angle != 0:
            abs_current_angle = abs(current_angle)
            if abs_current_angle > 40:
                abs_current_angle = 40
            power_scale = (100 - abs_current_angle) / 100.0
            print("power_scale:", round(power_scale, 2))
            if (current_angle / abs_current_angle) > 0:
                self.set_motor_speed(1, -1*speed)
                self.set_motor_speed(2, speed * power_scale)
            else:
                self.set_motor_speed(1, -1*speed * power_scale)
                self.set_motor_speed(2, speed)
        else:
            self.set_motor_speed(1, -1*speed)
            self.set_motor_speed(2, speed)

    def forward(self, speed):
        current_angle = self.state["P2"]
        if current_angle != 0:
            abs_current_angle = abs(current_angle)
            if abs_current_angle > 40:
                abs_current_angle = 30
            power_scale = (100 - abs_current_angle) / 100.0
            print("power_scale:", round(power_scale, 2))
            if (current_angle / abs_current_angle) > 0:
                self.set_motor_speed(1, speed)
                self.set_motor_speed(2, -1*speed * power_scale)
            else:
                self.set_motor_speed(1, speed * power_scale)
                self.set_motor_speed(2, -1*speed)
        else:
            self.set_motor_speed(1, speed)
            self.set_motor_speed(2, -1*speed)

    def stop(self):
        self.set_motor_speed(1, 0)
        self.set_motor_speed(2, 0)
