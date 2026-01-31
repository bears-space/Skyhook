#include <RadioLib.h>
#include "hal/RPi/PiHal.h"

// create a new instance of the HAL class
// use SPI channel 0
// the LLC68 CS is connected to CE0
PiHal* hal = new PiHal(0);

// now we can create the radio module
// NSS pin:   08
// DIO1 pin:  25
// NRST pin:  23
// BUSY pin:  24
LLCC68 radio = new Module(hal, 8, 25, 23, 24);

// the entry point for the program
int main(int argc, char** argv) {
  // initialize just like with Arduino
  printf("[LLCC68] Initializing ... ");
  int state = radio.beginFSK();
  if (state != RADIOLIB_ERR_NONE) {
    printf("failed, code %d\n", state);
    return(1);
  }
  printf("success!\n");

  // RXEN pin: 12
  // TXEN is conncted to dio2
  radio.setRfSwitchPins(12, RADIOLIB_NC);

  // loop forever
  int count = 0;
  for(;;) {
    // send a packet
    printf("[LLCC68] Transmitting packet ... ");
    char str[64];
    sprintf(str, "Hello World! #%d", count++);
    state = radio.transmit(str);
    if(state == RADIOLIB_ERR_NONE) {
      // the packet was successfully transmitted
      printf("success!\n");

      // wait for a second before transmitting again
      hal->delay(1000);

    } else {
      printf("failed, code %d\n", state);

    }

  }

  return(0);
}
