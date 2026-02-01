#include <RadioLib.h>
#include "hal/RPi/PiHal.h"

#include <sio_client.h>

#include <queue>
#include <mutex>
#include <optional>
#include <string>

std::queue<std::string> event_queue;
std::mutex queue_mutex;

void enqueue_event(const std::string &cmd) {
    std::lock_guard<std::mutex> lock(queue_mutex);
    event_queue.push(cmd);
}

std::optional<std::string> get_next_event() {
    std::lock_guard<std::mutex> lock(queue_mutex);
    if (!event_queue.empty()) {
        std::string cmd = event_queue.front();
        event_queue.pop();
        return cmd;
    }
    return std::nullopt;
}

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

// TODO: remove the weird c and c++ mix
// the entry point for the program
int main(int argc, char** argv) {

  // init socketio socketio client
  // TODO: pack the init code into seperate functions
  sio::client c;

  c.socket()->on("command", [&](sio::event &ev) {
        std::string cmd = ev.get_message()->get_map()["cmd"]->get_string();
        enqueue_event(cmd); // thread-safe push
    });

  c.connect("http://localhost:5000");

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
  while(1) {

    auto maybe_cmd = get_next_event();
    if (maybe_cmd) {
        std::string cmd = *maybe_cmd;
        std::cout << "Processing command in main loop: " << cmd << std::endl;

        // Do some sending here
        printf("[LLCC68] Transmitting packet ... ");
        char str[64];
        sprintf(str, "Hello World! #%d", count++); // obviously this should send the command instead of hello world
        state = radio.transmit(str);
        if(state == RADIOLIB_ERR_NONE) {
          // the packet was successfully transmitted
          printf("success!\n");

        } else {
          printf("failed, code %d\n", state);

        }
    }

    // TODO: add receiving
    hal->delay(1000);

  }

  return(0);
}
