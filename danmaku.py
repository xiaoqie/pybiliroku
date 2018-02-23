# -*- coding:utf-8 -*-
import socket
import urllib.request
import xml.etree.ElementTree
import random
import json
import asyncio
import traceback
import time
from _logging import log, verbose, error


def get_cmt_server(room_id):
    with urllib.request.urlopen("http://live.bilibili.com/api/player?id=cid:%d" % room_id) as conn:
        content = conn.read().decode("utf-8")
        content = "<root>%s</root>" % content
        root = xml.etree.ElementTree.fromstring(content)
        server = root.find("server").text
        return server


def send_socket_data(send, action, body="", packet_lenght=0, magic=16, ver=1, param=1):
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

    send(buffer)


def join_channel(send, room_id):
    r = random.uniform(0, 1)
    tmpuid = int(1e14 + 2e14 * r)
    payload = json.dumps({"roomid": room_id, "uid": tmpuid})
    send_socket_data(send, 7, payload)


reader = None
writer = None


def connect(room_id, loop, on_danmakus):
    async def tcp_message_client(loop):
        global reader, writer
        cmt_server = get_cmt_server(room_id)
        verbose("Got cmt server: %s" % cmt_server)
        if reader is None and writer is None:
            reader, writer = await asyncio.open_connection(cmt_server, 788, loop=loop)

        join_channel(writer.write, room_id)
        verbose("Joined channel %s in cmt server %s" %
                        (room_id, cmt_server))

        while True:
            data = await reader.read(4)
            if data == b'':
                raise RuntimeError("ooops, disconnected")
            packet_length = int.from_bytes(data, byteorder="big")
            if packet_length < 16:
                raise ValueError("packet_length too small")
            data = await reader.read(4)  # magic
            data = await reader.read(4)
            type_id = int.from_bytes(data, byteorder="big") - 1
            data = await reader.read(4)  # magic
            payload_length = packet_length - 16
            if payload_length == 0:
                continue

            data = b''
            # it's weird, that sometimes it won't read all of them at once
            while len(data) < payload_length:
                data += await reader.read(payload_length - len(data))
            verbose("type id: %d, length: %d" % (type_id, len(data)))
            if type_id == 4:
                json_obj = json.loads(data.decode("utf-8"))
                for on_danmaku in on_danmakus:
                    try:
                        on_danmaku(json_obj)
                    except Exception as e:
                        error(e)

    async def heartbeat(loop):
        global reader, writer
        while True:
            while reader is None and writer is None:
                await asyncio.sleep(0)
            send_socket_data(writer.write, 2)
            verbose("sent heartbeat")
            await asyncio.sleep(30)

    return [asyncio.ensure_future(tcp_message_client(loop), loop=loop), asyncio.ensure_future(heartbeat(loop), loop=loop)]


def close():
    global reader, writer
    try:
        writer.close()
    except Exception:
        pass

    reader = None
    writer = None

    log("closed connection with cmt server")
