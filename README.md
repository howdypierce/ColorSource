# color-source

Color-source is a simple example of how to use Raspberry Pi GPIO
inputs while simultaneously listening for and servicing incoming UDP
requests.

The color-source server assumes three momentary contact switches are
wired up to a Raspberry Pi, on the pins specified in the file. These
switches correspond to the colors red, green, and blue.

The server maintains a "current color", represented as a tuple:
`(red, green, blue)` with each value in the range 0-255 inclusive.

Initally this value is black (i.e., `(0,0,0)`). When one of the three
input switches is pressed, the value for the corresponding color goes
to 240 and slowly drops back to zero over 30 seconds.

At any point, a network client can query the current color, by
connecting to the server's UDP port 9099 and sending the ASCII message
`GET COLOR`. The server will respond with the ASCII message `COLOR <r> <g>
<b>` where each of `r`, `g`, and `b` are integers in the range 0-255
inclusive.

Debug information is logged using syslog, and can be viewed via the
command `sudo tail -f /var/log/messages`.

See the documentation in `color_source_rpi.py` for additional details.


## Starting/Stopping the Service

I created a systemd service so that the ColorSource server starts
automatically. To stop it from the command line: `sudo systemctl stop
color-source.service`

If installing on a new system, you need to symlink this file into the
proper location:

1. Edit the paths in `color-source.service` if needed.
1. `sudo ln -s color-source.service /etc/systemd/system/`
1. `sudo systemctl enable color-source.service`
1. `sudo systemctl start color-source.service`


