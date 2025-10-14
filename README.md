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
