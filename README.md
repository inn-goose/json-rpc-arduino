# JSON RPC for Arduino

## TLDR

🚧 WIP 🚧


## Board

Requires:
* [ArduinoJson 7](https://arduinojson.org/)

Serial Monitor test / `115200` baud
```
{"jsonrpc":"2.0","id":0,"method": "set_builtin_led", "params": {"status": 1}}

{"jsonrpc":"2.0","id":0,"method": "set_builtin_led", "params": {"status": 0}}
```

## python CLI

### init

```
pip3 install virtualenv

cd client/

PATH=${PATH}:~/Library/Python/3.9/bin/ ./sh/init.sh

source venv/bin/activate

deactivate
```

### usage

> note, that arduino restarts on every serial session: [discussion](https://forum.arduino.cc/t/arduino-auto-resets-after-opening-serial-monitor/850915), so it require `<3 sec` to init before processing requests. use `--init-timeout` to configure

```
python -m serial.tools.list_ports

python3 ./src/cli.py list

python3 ./src/cli.py run --port /dev/cu.usbmodem101 led_on

python3 ./src/cli.py run --port /dev/cu.usbmodem101 led_off
```
