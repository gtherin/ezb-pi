import os
from flask import Flask
import threading

import ezblock
import Music as music_mod
from vilib import Vilib
from picar import PiCar


appx = Flask(__name__)

px = PiCar()


@appx.route('/move/<speed>/<angle>/<delay>')
def move(speed, angle, delay):
    print(f'move({speed}, {angle}): start)')
    px.forward(int(speed)) # -100/100
    px.set_steering_angle(int(angle)) # -45/45
    ezblock.delay(int(delay))
    px.forward(0) # -100/100
    px.set_steering_angle(0) # -45/45
    return f'move({speed}, {angle}): done)'

@appx.route('/servo/<sid>/<angle>')
def servo(sid, angle):
    print(f'servo({sid}, {angle}): start)')
    total_angle = px.set_servo_angle(sid, angle, sum=True)
    return f'servo({sid}) = {total_angle} +=  {angle}: done'


@appx.route('/blink_led')
def blink_led():
    # Start LED
    led = ezblock.Pin("LED")
    for i in range(10):
        led.on()
        ezblock.delay(500)
        led.off()
        ezblock.delay(500)
    return "blink_led done"


@appx.route('/vent')
def vent():
    for i in range(10):
        angle = 100 * (i%2-0.5)
        px.servos["P7"].angle(angle)
        px.servos["P6"].angle(angle)
        ezblock.delay(100)
    return "vent done"

@appx.route('/music_play/<music>')
def play_music(music):
    # show the user profile for that user
    if music == "nothing":
        music_mod.music_stop()
    else:
        music_mod.background_music(f'{music}.mp3', loops=10)
    return f'User play_music({music}): done'

@appx.route('/music_volume/<level>')
def music_volume(level):
    music_mod.music_set_volume(int(level))
    return f'music_volume({level}: done)'


@appx.route('/video_color/<color>')
def video_color(color):
    if "DIEZ_" in color:
        color = color.replace("DIEZ_", "#")
    print(f'video_color({color}): start)')
    if color in "off":
        Vilib.color_detect_switch(False)
    else:
        Vilib.detect_color_name(color)
    return f'video_color({color}: done)'


@appx.route('/video_face_is/<status>')
def video_face_is(status):
    Vilib.human_detect_switch(status != "off") 
    return f'video_face_is({status}: done)'

@appx.route('/video_object_is/<status>')
def video_object_is(status):
    #Vilib.object_detect_switch(status != "off") 
    return f'video_object_is({status}: done)'

@appx.route('/say_text/<text>')
def say_text(text):
    tts = ezblock.TTS()
    tts.lang('fr-FR')
    tts.say(text)
    print(text)
    return f'say_text({text}): done'



@appx.route('/horn')
def horn(): 
    status, result = utils.run_command('sudo killall pulseaudio')
    music.sound_effect_threading('./sounds/car-double-horn.wav')
    

@appx.route('/avoid_obstacles')
def avoid_obstacles():
    while True:
        px.forward(50)
        distance = px.get_distance()
        ezblock.delay(100)

        if distance > 0 and distance < 300:
            if distance < 25:
                px.set_dir_servo_angle(-35)
            else:
                px.set_dir_servo_angle(0)   
    return f'avoid_obstacles({distance}): done'

@appx.route('/take_photos')
def take_photos():
    while True:
        px.forward(50)
        distance = px.get_distance()
        ezblock.delay(100)

        if distance > 0 and distance < 300:
            if distance < 25:
                px.set_dir_servo_angle(-35)
            else:
                px.set_dir_servo_angle(0)   
    return f'avoid_obstacles({distance}): done'


@appx.route('/line_following')
def line_following():
    gm_val_list = px.get_grayscale_data()
    return ""
    gm_status = px.get_line_status(gm_val_list)
    if gm_status == 'forward':
        px.forward(line_following_speed) 
    elif gm_status == 'left':
        px.set_dir_servo_angle(line_following_angle_offset)
        px.forward(line_following_speed) 
    elif gm_status == 'right':
        px.set_dir_servo_angle(-line_following_angle_offset)
        px.forward(line_following_speed) 
    else:
        px.set_dir_servo_angle(0)
        px.stop()



def mv_start():
    ip_address = '192.168.0.47' if "PICARX_ROGUE_MODE" in os.environ.keys() else '0.0.0.0'
    port = 9001
    print(f"LOGGGGGGGGGGGGGGG: picarx.mv_start ({ip_address}:{port}) [PICARX_ROGUE_MODE]")
    appx.run(host=ip_address, port=port, threaded=True, debug=False)

def start_px_server():
    worker_c = threading.Thread(target=mv_start, name="Threadc")
    worker_c.start()
    print("worker_c:", worker_c)
