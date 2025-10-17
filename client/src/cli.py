from typing import Any, Dict, List, Tuple

import sys
import glob
import serial
import time
import click
import json
from enum import Enum


json_rpc_request_id = 0


SERIAL_TIMEOUT_SEC = 2
REQUEST_WAIT_TIMEOUT_SEC = 2


class Operation(Enum):
    LIST = "list"
    RUN = "run"


class Method(Enum):
    LED_ON = "led_on"
    LED_OFF = "led_off"


def list_serial_ports() -> List[str]:
    # supports MacOS only, sorry
    if sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/cu.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException) as ex:
            click.echo(f"failed to open serial port: {str(ex)}")
    return result


def build_json_rpc_request(method, params):
    global json_rpc_request_id
    json_rpc_request_id += 1
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": json_rpc_request_id
    }


def read_json_response(ser: serial.Serial, timeout: int) -> Tuple[str, int]:
    start = time.time()
    deadline = start + timeout

    buffer = b""

    while time.time() < deadline:
        if ser.in_waiting > 0:
            buffer += ser.read(ser.in_waiting)
            try:
                wait_period = time.time() - start
                data = json.loads(buffer.decode())
                return (data, wait_period)
            except json.JSONDecodeError:
                pass  # Keep reading until full JSON is received
        time.sleep(0.05)

    return (None, timeout)


def run_method(port: str, baudrate: int, init_timeout: int, method: str) -> int:
    if method == Method.LED_ON:
        request = build_json_rpc_request("set_builtin_led", {"status": 1})
        return process_rpc_request(port, baudrate, init_timeout, request)

    elif method == Method.LED_OFF:
        request = build_json_rpc_request("set_builtin_led", {"status": 0})
        return process_rpc_request(port, baudrate, init_timeout, request)

    else:
        click.echo(f"unknown method: {method}")
        return 1


def process_rpc_request(port: str, baudrate: int, init_timeout: int, request: Dict[str, Any]) -> int:
    ser = serial.Serial(port=port, baudrate=baudrate,
                        timeout=SERIAL_TIMEOUT_SEC)

    # arduino auto-resets on every new serial session
    # so we need to wait for the full board initialization
    response, wait_period = read_json_response(
        ser, timeout=init_timeout)
    if response is not None:
        click.echo(
            f"init [{wait_period:.2f} sec]:\n{json.dumps(response, indent=2)}")

    # send request and read the amount of written bytes
    w_res = ser.write((json.dumps(request) + '\n').encode())
    click.echo(f"request [{w_res}]:\n{json.dumps(request, indent=2)}")

    # flush the data to the board
    ser.flush()

    # wait for the response from the board
    # should be real quick
    response, wait_period = read_json_response(
        ser, timeout=REQUEST_WAIT_TIMEOUT_SEC)
    if response is None:
        click.echo(f"no response [{wait_period}]")
        return 1
    else:
        click.echo(
            f"response [{wait_period:.2f} sec]:\n{json.dumps(response, indent=2)}")
        return 0


@click.command()
@click.argument("operation", required=False, type=click.Choice([op.value for op in Operation], case_sensitive=False))
@click.argument("method", required=False, type=click.Choice([fu.value for fu in Method], case_sensitive=False))
@click.option('--port', default=None)
@click.option('--baudrate', default=115200)
@click.option('--init-timeout', default=3)
def cli(operation, method, port, baudrate, init_timeout):
    if operation is None or operation == Operation.LIST.value:
        ports = list_serial_ports()
        click.echo("available serial ports:")
        for port in ports:
            click.echo(f"> {port}")
        return 0

    elif operation == Operation.RUN.value:
        if port is None:
            click.echo("specify serial port")
            return 1
        if method is None:
            click.echo("specify method to run")
            return 1

        return run_method(port, baudrate, init_timeout, Method(method.lower()))

    else:
        click.echo(f"unknown operation: {operation}")
        return 1


if __name__ == '__main__':
    sys.exit(cli())
