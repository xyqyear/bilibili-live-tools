from bilibili import bilibili
from statistics import Statistics
from printer import Printer
import utils
import asyncio
import random
import struct
import json
import sys

class bilibiliClient():

    def __init__(self, roomid, area_name):
        self.bilibili = bilibili()
        self._reader = None
        self._writer = None
        self._uid = None
        self.connected = False
        self._UserCount = 0
        self.dic_bulletin = {
            'cmd': 'str',
            'msg': 'str',
            'rep': 'int',
            'url': 'str'
        }
        self._roomId = roomid
        self.area_name = area_name

    def close_connection(self):
        self._writer.close()
        self._connected = False

    async def connectServer(self):
        try:
            reader, writer = await asyncio.open_connection(self.bilibili.dic_bilibili['_ChatHost'],
                                                           self.bilibili.dic_bilibili['_ChatPort'])
        except:
            print("连接无法建立，请检查本地网络状况")
            await asyncio.sleep(5)
            return
        self._reader = reader
        self._writer = writer
        if (await self.SendJoinChannel(self._roomId) == True):
            self.connected = True
            Printer().printer(f'连接 {self._roomId} [{self.area_name}]弹幕服务器成功', "Info", "green")
            await self.ReceiveMessageLoop()

    async def HeartbeatLoop(self):
        while not self.connected:
            await asyncio.sleep(0.5)

        while self.connected:
            await self.SendSocketData(0, 16, self.bilibili.dic_bilibili['_protocolversion'], 2, 1, "")
            await asyncio.sleep(30)

    async def SendJoinChannel(self, channelId):
        self._uid = (int)(100000000000000.0 + 200000000000000.0 * random.random())
        body = '{"roomid":%s,"uid":%s}' % (channelId, self._uid)
        await self.SendSocketData(0, 16, self.bilibili.dic_bilibili['_protocolversion'], 7, 1, body)
        return True

    async def SendSocketData(self, packetlength, magic, ver, action, param, body):
        bytearr = body.encode('utf-8')
        if packetlength == 0:
            packetlength = len(bytearr) + 16
        sendbytes = struct.pack('!IHHII', packetlength, magic, ver, action, param)
        if len(bytearr) != 0:
            sendbytes = sendbytes + bytearr
        try:
            self._writer.write(sendbytes)
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            self.connected = False

        await self._writer.drain()

    async def ReadSocketData(self, len_wanted):
        bytes_data = b''
        if len_wanted == 0:
            return bytes_data
        len_remain = len_wanted
        while len_remain != 0:
            try:
                tmp = await asyncio.wait_for(self._reader.read(len_remain), timeout=35.0)
            except asyncio.TimeoutError:
                Printer().printer(f'由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开 {self._roomId}',"Error","red")
                self._writer.close()
                self.connected = False
                await asyncio.sleep(1)
                return None
            except ConnectionResetError:
                Printer().printer(f'RESET，网络不稳定或者远端不正常断开 {self._roomId}',"Error","red")
                self._writer.close()
                self.connected = False
                await asyncio.sleep(5)
                return None
            except asyncio.CancelledError:

                return None
            except:
                Printer().printer(f"{sys.exc_info()[0]}, {sys.exc_info()[1]}","Error","red")
                Printer().printer(f'请联系开发者',"Error","red")
                self._writer.close()
                self.connected = False
                return None

            if not tmp:
                Printer().printer(f"主动关闭或者远端主动发来FIN {self._roomId}","Error","red")
                self._writer.close()
                self.connected = False
                await asyncio.sleep(1)
                return None
            else:
                bytes_data = bytes_data + tmp
                len_remain = len_remain - len(tmp)

        return bytes_data

    async def ReceiveMessageLoop(self):
        while self.connected == True:
            tmp = await self.ReadSocketData(16)
            if tmp is None:
                break

            expr, = struct.unpack('!I', tmp[:4])

            num, = struct.unpack('!I', tmp[8:12])

            num2 = expr - 16

            tmp = await self.ReadSocketData(num2)
            if tmp is None:
                break

            if num2 != 0:
                num -= 1
                if num == 0 or num == 1 or num == 2:
                    num3, = struct.unpack('!I', tmp)
                    self._UserCount = num3
                    continue
                elif num == 3 or num == 4:
                    try:
                        messages = tmp.decode('utf-8')
                    except:
                        continue
                    await self.parseDanMu(messages)
                    continue
                elif num == 5 or num == 6 or num == 7:
                    continue
                else:
                    if num != 16:
                        pass
                    else:
                        continue

    async def parseDanMu(self, messages):
        try:
            dic = json.loads(messages)

        except:
            return
        cmd = dic['cmd']

        if cmd == 'PREPARING':
            Printer().printer(f"[{self.area_name}] 房间 {self._roomId} 下播！将切换监听房间", "Info", "green")
            await utils.reconnect(self.area_name)
        elif cmd == 'DANMU_MSG':
            Printer().printer(f"{dic}", "Message", "cyan", printable=False)
            return
        elif cmd == 'SYS_GIFT':
            try:
                Printer().printer(f"出现了远古的SYS_GIFT,请尽快联系开发者{dic}", "Warning", "red")
            except:
                pass
            return
        elif cmd == 'SYS_MSG':
            pass
        elif cmd == "WELCOME":
            pass
        elif cmd == "SEND_GIFT":
            pass
        elif cmd == "WELCOME_GUARD":
            pass
        elif cmd == "WELCOME_ACTIVITY":  # 欢迎来到活动
            pass
        elif cmd == "WISH_BOTTLE":
            pass
        elif cmd == "COMBO_END":
            pass
        elif cmd == "ENTRY_EFFECT":
            pass
        elif cmd == "ROOM_RANK":
            pass
        elif cmd == "COMBO_SEND":
            pass
        elif cmd == "ROOM_BLOCK_MSG":
            pass
        elif cmd == "SPECIAL_GIFT":
            pass
        elif cmd == "NOTICE_MSG":
            pass
        elif cmd == "GUARD_MSG":
            pass
        elif cmd == "GUARD_BUY":
            pass
        elif cmd == "GUARD_LOTTERY_START":
            pass
        elif cmd == "PK_INVITE_INIT":
            pass
        elif cmd == "PK_CLICK_AGAIN":
            pass
        elif cmd == "PK_AGAIN":
            pass
        elif cmd == "PK_MATCH":  # pk匹配
            pass
        elif cmd == "PK_MIC_END":
            pass
        elif cmd == "PK_PRE":  # pk预备阶段
            pass
        elif cmd == "LIVE":  # 开播
            pass
        elif cmd == "PK_PROCESS":  # pk 过程值
            pass
        elif cmd == "PK_END":  # pk结束
            pass
        elif cmd == "PK_SETTLE":  # pk settle
            pass
        elif cmd == "PK_START":  # pk开始
            pass
        elif cmd == "ACTIVITY_EVENT":  # 没有用的充能值信息
            pass
        elif cmd == "WARNING":  # {'cmd': 'WARNING', 'msg': '违反直播分区规范，请立即更换至游戏区', 'roomid': 69956}
            pass
        elif cmd == "RAFFLE_END":  # 抽奖结束
            pass
        elif cmd == "RAFFLE_START":  # 抽奖开始
            pass
        elif cmd == "ROOM_SHIELD":  # 屏蔽{'cmd': 'ROOM_SHIELD', 'type': 1, 'user': '', 'keyword': '', 'roomid': 3051144}
            pass
        elif cmd == "TV_START":  # 小电视开始{'cmd': 'TV_START', 'data': {'id': '159720', 'dtime': 180, 'msg': {'cmd': 'SYS_MSG', 'msg': 'もやしパワー:? 送给:? 管珩心-中间的字念横:? 1个小电视飞船
            pass
        elif cmd == "TV_END":  # 小电视关闭{'cmd': 'TV_END', 'data': {'id': '159720', 'uname': '顾惜大哥哥', 'sname': 'もやしパワー', 'giftName': '100000x银瓜子', 'mobileTips': '恭喜 顾惜大哥哥 获得100000x银瓜子'
            pass
        elif cmd == "ROOM_ADMINS":  # 房管列表{'cmd': 'ROOM_ADMINS', 'uids': [25866878, 7026393, 240404878, 52054996]}
            pass
        elif cmd == "ROOM_SILENT_ON":  # 禁言开启{'cmd': 'ROOM_SILENT_ON', 'data': {'type': 'level', 'level': 1, 'second': -1}, 'roomid': 5225}
            pass
        elif cmd == "ROOM_SILENT_OFF":  # 禁言关闭{'cmd': 'ROOM_SILENT_OFF', 'data': [], 'roomid': 5225}
            pass
        else:
            Printer().printer(f"出现一个未知msg{dic}", "Info", "red")
            pass
