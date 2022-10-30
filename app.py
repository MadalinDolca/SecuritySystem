from flask import Flask, render_template, url_for, copy_current_request_context, make_response, request
from flask_socketio import SocketIO, emit
from threading import Thread, Event

import RPi.GPIO as GPIO

import subprocess # pentru realizarea pozelor
import datetime, time

###################################################################

GPIO.setwarnings(False) # ignorare avertismente GPIO
GPIO.setmode(GPIO.BCM) # Utilizam numerotarea pentru pini GPIOX

# creare si configurare instanta Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# transforma aplicația Flask într-o aplicație SocketIO
socketIO = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

thread = Thread()
thread_stop_event = Event()

###################################################################

# configurare pin senzor de miscare
pir = 7 # Pinul 7 va corespunde pinului din mijloc al PIR
GPIO.setup(pir, GPIO.IN) # Setam pinul ca pin GPIO de INTRARE

# configurare pin LED
pinLED = 17
GPIO.setup(pinLED, GPIO.OUT) # Setam pinul ca pin GPIO de IESIRE

# configurare pin switch SW1
switchOnOff = 24
GPIO.setup(switchOnOff, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)

###################################################################

print("Asteptam ca senzorul sa fie operational...")
time.sleep(2)

# metoda pentru detectarea miscarilor, evectuarea pozelor si emiterea datelor catre aplicatia SocketIO
def detectie():
    print("Asteptam sa detectam o miscare...")

    while not thread_stop_event.isSet():
        if GPIO.input(pir): # verificam daca pinul senzorului de miscare este pe HIGH
            if GPIO.input(switchOnOff) == GPIO.HIGH: # verificam daca switch-ul SW1 este pornit
                print("S-a detectat o miscare!")
                    
                timpCurent = datetime.datetime.now() # obtinere timp curent
                timpCurentFormatat = timpCurent.strftime("%d-%m-%Y_%H-%M-%S") # formatare timp curent

                numePozaEfectuata = timpCurentFormatat + ".jpg" # numele imaginii efectuate

                GPIO.output(pinLED, GPIO.HIGH) # pornire LED

                subprocess.Popen("sudo fswebcam " + "static/imagini/" + numePozaEfectuata, shell = True).communicate() # realizare fotografie avand ca nume timpul curent si salvare in folderul "imagini/"
                print("S-a efectuat o fotografie!")

                GPIO.output(pinLED, GPIO.LOW) # oprire LED
                #GPIO.cleanup()

                socketIO.emit('poze_efectuate', {'numePozaEfectuata': numePozaEfectuata}, namespace='/test') # emitere nume poze efectuate   
                socketIO.emit('timestamp_miscare', {'timeStampDetectie': timpCurentFormatat}, namespace='/test') # emitere timestamp-uri miscari

                socketIO.sleep(2)

                time.sleep(1) # asteptam/evitam o detectie multipla
        time.sleep(0.1)


@app.route('/')
def index():
    return render_template('index.html')


@socketIO.on('connect', namespace='/test')
def test_connect():
    global thread
    print('Client conectat')

    if not thread.is_alive():
        print("Pornire Thread")
        thread = socketIO.start_background_task(detectie)


@socketIO.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client deconectat')

@app.route('/comenzi', methods=['POST'])
def formular_post():
    # text = request.form['text']
    # mesaj = text.upper()
    # comanda = "python pwm.py " + text
    # os.system(comanda)
    # mesaj = "numarul de aprinderi este " + mesaj
    return mesaj

if __name__ == '__main__':
    socketIO.run(app)