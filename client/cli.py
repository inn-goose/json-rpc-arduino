from enum import Enum

import sys

import click

from json_rpc import client



class Method(Enum):
    LED_ON = "led_on"
    LED_OFF = "led_off"



def execute_method(json_rpc_client: client.JsonRpcClient, method: str) -> str:
    if method == Method.LED_ON:
        return json_rpc_client.send_request("set_builtin_led", {"status": 1})

    elif method == Method.LED_OFF:
        return json_rpc_client.send_request("set_builtin_led", {"status": 0})

    else:
        raise Exception(f"unknown method: {method}")


@click.command()
@click.argument("serial-port")
@click.option('--baudrate', default=115200)
@click.option('--init-timeout', default=3)
@click.argument("method", type=click.Choice([m.value for m in Method], case_sensitive=False))
def cli(serial_port: str, baudrate: int, init_timeout: int, method: str) -> int:
    method = method.lower()

    # init
    json_rpc_client = client.JsonRpcClient(port=serial_port, baudrate=baudrate, init_timeout=float(init_timeout))
    init_result = json_rpc_client.init()
    if init_result is not None:
        click.echo(f"init: {init_result}")

    # execute
    try:
        result = execute_method(json_rpc_client, Method(method))
        click.echo(f"{method}: {result}")
        return 0
    except Exception as ex:
        click.echo(f"failed to execute {method} method with: {str(ex)}")
        return 1


if __name__ == '__main__':
    sys.exit(cli())
