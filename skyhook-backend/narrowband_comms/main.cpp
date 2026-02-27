#include <RadioLib.h>
#include "hal/RPi/PiHal.h"

#include <sio_client.h>

#include <queue>
#include <mutex>
#include <optional>
#include <string>
#include <format>

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


void bind_events(sio:client &c) {

    c.set_open_listener([&]() {
        std::cout << "Connected to Python server" << std::endl;
    });

    c.set_close_listener([&]() {
        std::cout << "Disconnected from server" << std::endl;
    });

    c.socket()->on("command", [&](sio::event &ev) {
        std::string cmd = ev.get_message()->get_map()["cmd"]->get_string();
        enqueue_event(cmd); // thread-safe push
    });

}

int init_radio(){

}

int main() {

    // init socketio socketio client
    sio::client c;
    bind_events(c);
    c.connect("http://localhost:3000");

    // initialize radio
    std::cout << "[LLCC68] Initializing ... ";
    int state = radio.beginFSK();
    if (state != RADIOLIB_ERR_NONE) {
        std::cout << "failed, code " << static_cast<int>state << std::endl;
        return(1);
    }
    std::cout << "success!" << std::endl;

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
            std::cout << "[LLCC68] Transmitting packet ... ";
            char str[64];
            auto result = std::format_to_n(str, sizeof(str) - 1, "Hello World! #{}", count++);
            str[result.size] = '\0';
            state = radio.transmit(str);
            if(state == RADIOLIB_ERR_NONE) {
                // the packet was successfully transmitted
                std::cout << "success!" << std::endl;

            } else {
                std::cout << "failed, code " << static_cast<int> state << std::endl;

            }
        }

      // TODO: add receiving
      hal->delay(1000);
    }

    return(0);
}
