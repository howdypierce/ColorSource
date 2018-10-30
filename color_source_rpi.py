import RPi.GPIO as GPIO
from datetime import datetime, timedelta
from time import sleep
import socket
from syslog import syslog
import sys

SERVER_PORT = 9099
BUF_SIZE = 1024
DEBOUNCE = 100    # switch debounce time, in msec

# Raspberry Pi pins - using BOARD numbering
#    see https://pinout.xyz/
#  3.3v power: 1
#  ground: 6
GPIO_INPUT_RED = 18
GPIO_INPUT_GREEN = 16
GPIO_INPUT_BLUE = 22

class DecayButton():
    """Abstracts the state of a physical momentary-contact switch.

    A DecayButton has a value, which is 0 initially. When the user
    pushes the switch, the DecayButton's value is set to its maximum.
    It decays back to 0 as time passes.

    Parameters to the class control the duration and how many steps
    this decay takes. See the arguments to __init__ for details.

    The caller can call the value() function at any point to get the
    current value of the DecayButton.

    If the caller is not calling the value() function repeatedly, it
    should periodically call the check() function (typically from a
    main loop). This step is not needed if the value() function is
    already being polled frequently.
    """

    def __init__(self,
                 name: str,
                 input_pin: int,
                 pull_up_down: int = GPIO.PUD_UP,
                 init_value: int = 240,
                 decay_tm: int = 30000,
                 num_steps: int = 3) -> None:
        """Initialize a DecayButton instance.

        Args:
            name: The name of this DecayButton. Only used for debug
              messages.

            input_pin: RPi.GPIO pin (using BOARD numbering) which maps
              to a momentary-contact input switch. When a rising edge
              is detected on this pin, the timer will be set to 0 (and
              thus the color will be set to its maximum value)

            pull_up_down: either PUD_DOWN or PUD_UP depending on how
              the switch is wired.

            init_value: initial (maximum) value

            decay_tm: duration in msec until the value of the
              DecayButton returns to 0 after a button press

            num_steps: the number of decay steps.

        Examples:
            init_value=240, decay_tm=1000, num_steps=1: When the
              switch is pressed, the DecayButton will have value=240
              for one second (1000 msec), then value=0

            init_value=255, decay_tm=30000, num_steps=3: When the
              switch is pressed, the DecayButton will have value=255
              for 10 sec, then value=170 (2/3rds of 255) for 10 sec,
              then value=85 for 10 sec, then value=0
        """

        self.name = name
        self.pin = input_pin
        self.pull_up_down = pull_up_down
        self.init_value = init_value
        self.decay_tm = decay_tm
        self.num_steps = num_steps
        self.press_tm = datetime(2018, 1, 1)

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=self.pull_up_down)
        GPIO.add_event_detect(self.pin, GPIO.BOTH, bouncetime=DEBOUNCE)

    def switch_state(self) -> bool:
        """Returns the instantaneous state of the switch: True if pressed"""
        if (self.pull_up_down == GPIO.PUD_UP):
            return not GPIO.input(self.pin)
        else:
            return GPIO.input(self.pin)

    def check(self) -> None:
        """Run periodically to poll if switch state has changed"""

        if (GPIO.event_detected(self.pin) and self.switch_state()):
            syslog(f"DecayButton({self.name}) triggered")
            self.press_tm = datetime.now()

    def value(self) -> int:
        """Returns the current value of the DecayButton"""
        self.check()
        dur = datetime.now() - self.press_tm
        if dur < timedelta(milliseconds=self.decay_tm):
            elapsed = (dur.seconds * 1000) + dur.microseconds / 1000  # in msec
            onestep = self.decay_tm / self.num_steps
            q = 1 - (int(elapsed / onestep) / self.num_steps)
            return int(self.init_value * q)
        return 0


def main_loop() -> None:
    """Runs the main loop

    Simple loop that checks switch state and listens for incoming
    network queries.
    """

    syslog("Starting up...")

    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", SERVER_PORT))  # bind to all IP addresses
    sock.settimeout(0.1)  # needs to be short, so we can check switch state

    red_btn = DecayButton("red", GPIO_INPUT_RED)
    green_btn = DecayButton("green", GPIO_INPUT_GREEN)
    blue_btn = DecayButton("blue", GPIO_INPUT_BLUE)

    last_debug_output = datetime.now()

    while True:
        color = (red_btn.value(), green_btn.value(), blue_btn.value())

        try:
            data, client_addr = sock.recvfrom(BUF_SIZE)
            syslog("received message: {data} from {client_addr}")

            if data == b'GET COLOR':
                ret = "COLOR {} {} {}".format(*color)
            else:
                ret = "ERROR"

            sent = sock.sendto(ret.encode('utf-8'), client_addr)
            syslog(f'sent {sent} bytes back to {client_addr}')
        except (socket.timeout):
            pass

        if (datetime.now() - last_debug_output) > timedelta(seconds=3):
            last_debug_output = datetime.now()
            syslog(f"RGB = {color}")


try:
    main_loop()
except:
    syslog(f"Received exception {sys.exc_info()[0]}")
    

GPIO.cleanup()
syslog("Exiting...")

