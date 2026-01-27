# Transceiver module datasheet:
# https://robu.in/wp-content/uploads/2024/07/E220-400M30S_UserManual_EN_v1.1.pdf
#
# Transceiver chip datasheet:
# https://www.mouser.com/pdfDocs/DS_LLCC68_V10-2.pdf

import time
import spidev

# We only have SPI bus 0 available to us on the Pi
bus = 0

#Device is the chip select pin. Set to 0 or 1, depending on the connections on the pi
device = 1

# Enable SPI
spi = spidev.SpiDev()

# Open a connection to a specific bus and device (chip select pin)
spi.open(bus, device)

# Set SPI speed
spi.max_speed_hz = 500000

# this is the correct spi mode, because the datasheet specifies CPOL=0, CPHA=0
spi.mode = 0

# here some actual txrx could happen
msg = [0x76]
spi.xfer2(msg)

time.sleep(5)

spi.close()
