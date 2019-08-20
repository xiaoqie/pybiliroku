# -*- coding:utf-8 -*-
import socket
import urllib.request
import xml.etree.ElementTree
import random
import json
import asyncio
import traceback
import time
import websockets
import zlib
import argparse
from logger import Logger


ACTION_HEARTBEAT = 2
ACTION_HEARTBEAT_REPLY = 3
ACTION_MESSAGE = 5
ACTION_CONNECT_SUCCESS = 8

parser = argparse.ArgumentParser()
parser.add_argument("--room-id", action="store", dest="room_id", type=int, required=True)
args, _ = parser.parse_known_args()
log = Logger(f"{args.room_id} danmaku")


def get_cmt_server(room_id):
    with urllib.request.urlopen(f"https://api.live.bilibili.com/room/v1/Danmu/getConf?room_id={room_id}&platform=pc&player=web:%d", timeout=5) as conn:
        content = json.loads(conn.read().decode("utf-8"))
        server = random.choice(content['data']['host_server_list'])
        return server


def prepare_message(action, body="", packet_lenght=0, magic=16, ver=1, param=1):
    payload = body.encode("utf-8")
    if packet_lenght == 0:
        packet_lenght = len(payload) + 16

    # theoretically it is not a buffer
    buffer = packet_lenght.to_bytes(4, byteorder="big")
    buffer += magic.to_bytes(2, byteorder="big")
    buffer += ver.to_bytes(2, byteorder="big")
    buffer += action.to_bytes(4, byteorder="big")
    buffer += param.to_bytes(4, byteorder="big")
    buffer += payload

    return buffer


async def connect_once(room_id, on_danmaku):
    cmt_server = get_cmt_server(room_id)
    cmt_server_host = cmt_server['host']
    cmt_server_port = cmt_server['wss_port']
    uri = f"wss://{cmt_server_host}:{cmt_server_port}/sub"

    log.info(f"connecting danmaku server: {uri}")

    async with websockets.connect(uri) as websocket:
        payload = json.dumps({"uid": 0, "roomid": room_id, "protover": 2})
        await websocket.send(prepare_message(7, payload))
        
        async def heartbeat():
            while True:
                log.info("sending heartbeat")
                await websocket.send(prepare_message(2, "[object Object]"))
                await asyncio.sleep(30)
        
        async def message():
            def parse(data):
                while data:
                    length = int.from_bytes(data[0:4], byteorder="big", signed=False)
                    if length < 16:
                        raise ValueError("packet length too small")
                    headerLength = int.from_bytes(data[4:6], byteorder="big", signed=False)
                    ver = int.from_bytes(data[6:8], byteorder="big", signed=False)
                    op = int.from_bytes(data[8:12], byteorder="big", signed=False)
                    seq = int.from_bytes(data[12:16], byteorder="big", signed=False)
                    if ver == 2:
                        parse(zlib.decompress(data[16:length]))
                    else:
                        if op == 8:
                            log.info("danmaku server connected")
                        elif op == 3:
                            log.info("heartbeat received")
                        elif op == 5:
                            json_data = json.loads(data[16:length].decode("utf-8"))
                            if json_data['cmd'] == "DANMU_MSG":
                                on_danmaku(json_data)
                        else:
                            log.info(f"unknown op:{op}")
                    data = data[length:]

            while True:
                data = await websocket.recv()
                parse(data)

        heartbeat_task = asyncio.create_task(heartbeat())
        try:
            await message()
        finally:
            heartbeat_task.cancel()


async def connect(room_id, on_danmaku):
    while True:
        try:
            await connect_once(room_id, on_danmaku)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.error(f"danmaku server disconnected: {str(e)}")
