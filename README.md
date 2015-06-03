# Crazyflie2 PC client for gps-ublox-cf2-firmware-almanac

Compatible with GPS receiver located on Ublox Max M8C Pico Breakout
Receiver connected to cf2 deck (expansion) port uart (RX1/TX1 on left side)
Serial communication uart baud rate 9600 bits/sec
Receiver message output rate - 1 Hz

This version of cfclient includes two new tabs: GPS & AssistNow;
  GPS Tab – lists gps data values the receiver outputs in proprietary binary
  messages UBX-NAV-PVT  (navigation position, velocity and time).  In addition
  an openstreet geographical map is shown, along with overlays for the home
  position (1st 3D-fix position - blue circle symbol) and the plotted current
  position (2D-fix or 3D-fix – red circle symbol)

  AssistNow Tab – push bar to activate the transfer of data to the cf2's gps
  receiver using proprietary binary messages in UBX-* format and passed as
  hexidecimal ascii character strings packed into crtp packets.  Flowcontrol
  between the cfclient & cf2 has been implemented in software.  Handshaking
  packet format is “<v>\n”, where v signifies various character controls.
  Data blocks contain a variable length ubx message, grouped in one or more
  packets, where the last packet in a block ends with “<>\n”, with or without
  preceding hexidecimal character pairs to complete a message.  The length of
  handshaking packets is four bytes.  The maximum length of a data packet is
  29 bytes and the ending packet in a block can contain as few as three bytes.
  All packets end in a end of string one character “\n” byte.

Currently, cf2 looks for nav-pvt messages from the gps receiver and handles
passing this navigation data to cfclient.  In addition, ebx messages generated
within cfclient and transferred to cf2 are passed on to the gps without
alteration.  At present there is no flowcontrol with the gps.   

The ebx-messages being sent to the gps receiver each contain a checksum and
this is used to verify message integrity prior to outputting it to the receiver.
If the checksum doesn't add up, the cf2 requests cfclient to repeat the entire
data block.  When the cf2 is expecting a transfer from cfclient, it activates a
watchdog timer and if a time out occurs, timeout >= M2T(4000), it requests a
repeat of the last packet.  Duplicate data block packets should not naturally
occur, and the cf2 discards them..  Unfortunately, unintended duplicate
handshaking packets cannot be as easily detected and can disrupt flowcontrol
coordination.

The sequence of messages is as follows: reset gps, turn-on pvt messages,
turn-off nmea messages, send utc time message, send llh position message, load
almanac messages (up to 32 satellites) from a web site (takes about 60 seconds),
then transfer a single dummy message followed by an almanac message for each
healthy satellite.  The dummy message as well as multiple pressing of the
AssistNow push bar to begin transfer of each message type, are only temporary
inclusions and will go away when testing and packet error detection and
analysis have come to a final conclusion.

Modules added to cfclient include: lib/cfclient/ui/tabs/GpsTab.py, Ablock.py,
ablockTab.ui; lib/cflib/crazyflie/ablock.py; parent-directory/gpstab_map.js,
gpstab_map.html, a-block.txt (working data block(s) packet file).

Modules modified in cfclient include: lib/cflib/crtp/crtpstack.py;
lib/cflib/crazyflie/__init__.py.

Currently, cf2 debug messages appear in the Console Tab, cfclient debug messages
appear in the command_window (show up after exiting cfclient) and cfclient
AssistNow messages appear in the AssistNow Tab.

# Crazyflie PC client

The Crazyflie PC client enables flashing and controlling the Crazyflie.
There's also a Python library that can be integrated into other applications
where you would like to use the Crazyflie.

## Windows

To install the Crazyflie PC client in Windows, download the installation
program from the [binary download
page](http://wiki.bitcraze.se/projects:crazyflie:binaries:index)."Crazyflie
client" will be added to the start menu.

Running from source
-------------------

## Windows

Install dependencies. With Windows installers (tested with 32-Bit versions):
 - Vcredist_86.exe
 - Python 2.7 2.7.9 (https://www.python.org/downloads/windows/)
 - PyQT4 for Python 2.7 4.11.3 (http://www.riverbankcomputing.com/software/pyqt/download)
 - Scipy for Python 2.7 0.15.1 (http://sourceforge.net/projects/scipy/files/scipy/)
 - PyQTGraph 0.9.10 (http://www.pyqtgraph.org/)
 - Numpy  for Python 2.7 0.6.9
 - Py2exe for Python 2.7 1.9.2

Python libs (to be install by running 'setup.py install'):
 - PyUSB 1.0.0 (https://github.com/walac/pyusb/releases)
 - Pysdl2 0.9.3 (https://bitbucket.org/marcusva/py-sdl2/downloads)

Download SDL2 2.0.3 from http://libsdl.org/download-2.0.php and copy SDL2.dll in the
crazyflie-clients-python folder.

Install Git 1.9.5

Install GitHub

Install Folium 0.1.2 with Leaflet 0.7.3 - with Jinja2 dependency

Add pointers to System Variables PATH 

Run with:
```
C:\Python27\python bin\cfclient
```
