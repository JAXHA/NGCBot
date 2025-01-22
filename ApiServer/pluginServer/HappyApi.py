from meme_generator import get_meme, get_meme_keys
import FileCache.FileCacheServer as Fcs
import Config.ConfigServer as Cs
from OutPut.outPut import op
import requests
import asyncio
import random
import time
import lz4.block as lb
import os
import re


class HappyApi:
    def __init__(self):
        """
        不要直接调用此类
        娱乐功能Api文件
        """
        # 读取配置文件
        configData = Cs.returnConfigData()
        # 读取系统版权设置
        self.systemCopyright = configData['systemConfig']['systemCopyright']
        self.txKey = configData['apiServer']['apiConfig']['txKey']
        self.picUrlList = configData['apiServer']['picApi']
        self.videoUrlList = configData['apiServer']['videosApi']
        self.dogApi = configData['apiServer']['dogApi']
        self.fishApi = configData['apiServer']['fishApi']
        self.kfcApi = configData['apiServer']['kfcApi']
        self.shortPlayApi = configData['apiServer']['shortPlayApi']
        self.dpKey = configData['apiServer']['apiConfig']['dpKey']
        self.dpVideoAnalysisApi = configData['apiServer']['dpVideoAnalysisAPi']
        self.dpWechatVideoApi = configData['apiServer']['dpWechatVideoApi']
        self.dpTaLuoApi = configData['apiServer']['dpTaLuoApi']
        self.musicApi = configData['apiServer']['musicApi']

    def downloadFile(self, url, savePath):
        """
        通用下载文件函数
        :param url:
        :param savePath:
        :return:
        """
        try:
            content = requests.get(url, timeout=30, verify=True).content
            if len(content) < 200:
                return None
            with open(savePath, mode='wb') as f:
                f.write(content)
            return savePath
        except Exception as e:
            op(f'[-]: 通用下载文件函数出现错误, 错误信息: {e}')
            return None

    def getMusic(self, musicName):
        op(f'[*]: 正在调用点歌接口... ...')
        for musicApi in self.musicApi:
            try:
                jsonData = requests.get(musicApi.format(musicName), verify=True, timeout=30).json()
                result = jsonData.get('response', {}).get('data', {}).get('song', {}).get('list', [])
                if result:
                    firstSong = result[0]
                    songName = firstSong.get('songname')
                    songMid = firstSong.get('songmid')
                    singers = firstSong.get('singer', [])
                    firstSingerName = singers[0].get('name', '')
                    singerPic = None  # 默认值为 None
                    zhida_singer = jsonData.get('response', {}).get('data', {}).get('zhida', {}).get('zhida_singer', [])
                    if zhida_singer:
                        singerPic = zhida_singer.get('singerPic')  # 获取第一个歌手的图片链接
                    musicPlayApi = f"https://qqmusic.qqovo.cn/getMusicPlay?songmid={songMid}&quality=m4a"
                    music_response = requests.get(musicPlayApi)
                    api = 1
                    if music_response.status_code == 400:
                        fallbackMusicApi = f"https://www.hhlqilongzhu.cn/api/dg_wyymusic.php?gm={musicName}&n=1&num=1&type=json"
                        music_response = requests.get(fallbackMusicApi)
                        api = 2
                    if music_response.status_code == 200:
                        music_data = music_response.json()
                        if (api == 1):
                            play_url = music_data.get('data', {}).get('playUrl', {}).get(songMid, {}).get('url')
                            if not play_url:  # 如果主接口返回的play_url为空，使用备用接口
                                fallbackMusicApi = f"https://www.hhlqilongzhu.cn/api/dg_wyymusic.php?gm={musicName}&n=1&num=1&type=json"
                                music_response = requests.get(fallbackMusicApi)
                                music_response = music_response.json()
                                songName = music_response.get('title', '')
                                firstSingerName = music_response.get('singer', '')
                                play_url = music_response.get('music_url', '')  # 备用接口返回的播放链接字段
                                singerPic = music_response.get('cover', '')
                                dataurl = music_response.get('link', '')
                            else:
                                dataurl = f"https://y.qq.com/n/ryqq/songDetail/{songMid}"
                        else:
                            # 处理备用接口的返回结果
                            songName = music_data.get('title', '')
                            firstSingerName = music_data.get('singer', '')
                            play_url = music_data.get('music_url', '')  # 备用接口返回的播放链接字段
                            singerPic = music_data.get('cover', '')
                            dataurl = music_data.get('link', '')
                        if play_url:
                            # 构造 XML 消息
                            xml_message = f"""<?xml version="1.0"?>
            <msg>
                    <appmsg appid="wx8dd6ecd81906fd84" sdkver="0">
                            <title>{songName}</title>
                            <des>{firstSingerName}\n❤Bot-祝您天天开心❤</des>
                            <action>view</action>
                            <type>3</type>
                            <showtype>0</showtype>
                            <content />
                            <url>{dataurl}</url>
                            <dataurl>{play_url}</dataurl>
                            <lowurl/>
                            <lowdataurl/>
                            <recorditem />
                            <thumburl />
                            <messageaction />
                            <laninfo />
                            <extinfo />
                            <sourceusername />
                            <sourcedisplayname />
                            <commenturl />
                            <appattach>
                                    <totallen>0</totallen>
                                    <attachid />
                                    <emoticonmd5></emoticonmd5>
                                    <fileext />
                                    <aeskey></aeskey>
                            </appattach>
                            <webviewshared>
                                    <publisherId />
                                    <publisherReqId>0</publisherReqId>
                            </webviewshared>
                            <weappinfo>
                                    <pagepath />
                                    <username />
                                    <appid />
                                    <appservicetype>0</appservicetype>
                            </weappinfo>
                            <websearch />
                            <songalbumurl>{singerPic}</songalbumurl>
                    </appmsg>
                    <scene>0</scene>
                    <appinfo>
                            <version>49</version>
                            <appname>网易云音乐</appname>
                    </appinfo>
                    <commenturl />
            </msg>"""

                            # 将文本编码成字节
                            text_bytes = xml_message.encode('utf-8')
                            # 使用 lz4 压缩
                            compressed_data = lb.compress(text_bytes,store_size=False)
                            # 将压缩后的数据转为十六进制字符串，以便存储到数据库
                            compressed_data_hex = compressed_data.hex()
                            return compressed_data_hex
            except Exception as e:
                op(f'[-]: 点歌API出现错误, 错误信息: {e}')
                continue
            return None


    def getTaLuo(self, ):
        """
        塔罗牌占卜
        :return:
        """
        op(f'[*]: 正在调用塔罗牌占卜接口... ...')
        try:
            jsonData = requests.get(self.dpTaLuoApi.format(self.dpKey), verify=True).json()
            code = jsonData.get('code')
            if code == 200:
                savePath = Fcs.returnPicCacheFolder() + '/' + str(int(time.time() * 1000)) + '.jpg'
                result = jsonData.get('result')
                Pai_Yi_deduction = result.get('Pai_Yi_deduction')
                core_prompt = result.get('core_prompt')
                Knowledge_expansion = result.get('Knowledge_expansion')
                Card_meaning_extension = result.get('Card_meaning_extension')
                e_image = result.get('e_image')
                picPath = self.downloadFile(e_image, savePath)
                content = f'描述: {Pai_Yi_deduction}\n\n建议: {core_prompt}\n\n描述: {Knowledge_expansion}\n\n建议: {Card_meaning_extension}'
                return content, picPath
            return '', ''
        except Exception as e:
            op(f'[-]: 塔罗牌占卜接口出现错误, 错误信息: {e}')
            return '', ''

    def getWechatVideo(self, objectId, objectNonceId):
        """
        微信视频号处理下载, 返回Url
        :param objectId:
        :param objectNonceId:
        :return:
        """
        op(f'[*]: 正在调用视频号API接口... ...')
        try:
            jsonData = requests.get(self.dpWechatVideoApi.format(self.dpKey, objectId, objectNonceId), verify=True,
                                    timeout=500).json()
            code = jsonData.get('code')
            if code == 200:
                videoData = jsonData.get('data')
                description = videoData.get('description').replace("\n", "")
                nickname = videoData.get('nickname')
                videoUrl = videoData.get('url')
                content = f'视频描述: {description}\n视频作者: {nickname}\n视频链接: {videoUrl}'
                return content
            elif code == 202:
                time.sleep(200)
                return self.getWechatVideo(objectId, objectNonceId)
            return None
        except Exception as e:
            op(f'[-]: 视频号API接口出现错误, 错误信息: {e}')
            return None

    def getVideoAnalysis(self, videoText):
        """
        抖音视频解析去水印
        :param videoText: 短视频连接或者分享文本
        :return: 视频地址
        """
        op(f'[*]: 正在调用视频解析去水印API接口... ....')
        try:
            douUrl = re.search(r'(https?://[^\s]+)', videoText).group()
            jsonData = requests.get(self.dpVideoAnalysisApi.format(self.dpKey, douUrl), verify=True).json()
            code = jsonData.get('code')
            if code == 200:
                videoData = jsonData.get('data')
                videoUrl = videoData.get('video_url')
                savePath = Fcs.returnVideoCacheFolder() + '/' + str(int(time.time() * 1000)) + '.mp4'
                savePath = self.downloadFile(videoUrl, savePath)
                if savePath:
                    return savePath
            return None
        except Exception as e:
            op(f'[-]: 视频解析去水印API出现错误, 错误信息: {e}')
            return None

    def getShortPlay(self, playName):
        """
        短剧搜索
        :param playName: 短剧名称
        :return:
        """
        op(f'[*]: 正在调用短剧搜索API接口... ...')
        content = f'🔍搜索内容: {playName}\n'
        try:
            jsonData = requests.get(self.shortPlayApi.format(playName), verify=True).json()
            statusCode = jsonData.get('code')
            if statusCode != 200:
                return False
            dataList = jsonData.get('data')
            if not dataList:
                content += '💫搜索的短剧不存在哦 ~~~\n'
            else:
                for data in dataList:
                    content += f'🌟{data.get("name")}\n'
                    content += f'🔗{data.get("link")}\n\n'
            content += f"{self.systemCopyright + '整理分享，更多内容请戳 #' + self.systemCopyright if self.systemCopyright else ''}\n{time.strftime('%Y-%m-%d %X')}"
            return content
        except Exception as e:
            op(f'[-]: 短剧搜索API出现错误, 错误信息: {e}')
            return False

    def getPic(self, ):
        """
        美女图片下载
        :return:
        """
        op(f'[*]: 正在调用美女图片Api接口... ...')
        picUrl = random.choice(self.picUrlList)
        savePath = Fcs.returnPicCacheFolder() + '/' + str(int(time.time() * 1000)) + '.jpg'
        picPath = self.downloadFile(picUrl, savePath)
        if not picPath:
            for picUrl in self.picUrlList:
                picPath = self.downloadFile(picUrl, savePath)
                if picPath:
                    break
                continue
        return picPath

    def getVideo(self, ):
        """
        美女视频下载
        :return:
        """
        op(f'[*]: 正在调用美女视频Api接口... ...')
        videoUrl = random.choice(self.videoUrlList)
        savePath = Fcs.returnVideoCacheFolder() + '/' + str(int(time.time() * 1000)) + '.mp4'
        videoPath = self.downloadFile(videoUrl, savePath)
        if not videoPath:
            for videoUrl in self.videoUrlList:
                videoPath = self.downloadFile(videoUrl, savePath)
                if videoPath:
                    break
                continue
        return videoPath

    def getFish(self, ):
        """
        摸鱼日历下载
        :return:
        """
        op(f'[*]: 正在调用摸鱼日历Api接口... ...')
        savePath = Fcs.returnPicCacheFolder() + '/' + str(int(time.time() * 1000)) + '.jpg'
        fishPath = self.downloadFile(url=self.fishApi, savePath=savePath)
        if not fishPath:
            for i in range(2):
                fishPath = self.downloadFile(self.fishApi, savePath)
                if fishPath:
                    break
                continue
        if not fishPath:
            op(f'[-]: 摸鱼日历接口出现错误, 请检查！')
        return fishPath

    def getKfc(self, ):
        """
        疯狂星期四
        :return:
        """
        op(f'[*]: 正在调用KFC疯狂星期四Api接口... ... ')
        try:
            jsonData = requests.get(url=self.kfcApi, timeout=30).json()
            result = jsonData.get('text')
            if result:
                return result
            return None
        except Exception as e:
            op(f'[-]: KFC疯狂星期四Api接口出现错误, 错误信息: {e}')
            return None

    def getDog(self, ):
        """
        舔狗日记Api接口
        :return:
        """
        op(f'[*]: 正在调用舔狗日记Api接口... ... ')
        try:
            jsonData = requests.get(url=self.dogApi.format(self.txKey), timeout=30).json()
            result = jsonData.get('result')
            if result:
                content = result.get('content')
                if content:
                    return content
            return None
        except Exception as e:
            op(f'[-]: 舔狗日记Api接口出现错误, 错误信息: {e}')
            return None

    def getEmoticon(self, avatarPathList, memeKey=None):
        """
        表情包Api接口
        :param memeKey: 消息内容
        :param avatarPathList: 头像列表
        :return:
        """
        op(f'[*]: 正在调用表情包Api接口... ...')
        if not avatarPathList:
            op(f'[-]: 表情包Api接口出现错误, 错误信息: avatarPathList不能为空')
            return
        if not avatarPathList:
            raise 'avatarPathList None'
        if not memeKey:
            memeKey = random.choices(get_meme_keys())[0]

        savePath = Fcs.returnPicCacheFolder() + '/' + str(int(time.time() * 1000)) + '.gif'
        try:
            async def makeEmo():
                meme = get_meme(memeKey)
                result = await meme(images=avatarPathList, texts=[], args={"circle": False})
                with open(savePath, "wb") as f:
                    f.write(result.getvalue())

            loop = asyncio.new_event_loop()
            loop.run_until_complete(makeEmo())
            # 图片大小判断 如果大于1mb 就以图片形式发送
            file_size_bytes = os.path.getsize(savePath)
            size_limit_bytes = 1024 * 1024
            sizeBool = file_size_bytes <= size_limit_bytes
            return savePath, sizeBool
        except Exception as e:
            op(f'[-]: 表情包Api接口出现错误, 错误信息: {e}')
            return None, None


if __name__ == '__main__':
    Ha = HappyApi()
    # print(Ha.getDog())
    # print(Ha.getKfc())
    # Ha.getEmoticon('C:/Users/Administrator/Desktop/NGCBot V2.2/avatar.jpg')
    # print(Ha.getShortPlay('霸道总裁爱上我'))
    # print(Ha.getPic())
    # print(Ha.getVideoAnalysis(
    #     '3.84 复制打开抖音，看看【SQ的小日常的作品】师傅：门可以让我踹吗 # 情侣 # 搞笑 # 反转... https://v.douyin.com/iydr37xU/ bAg:/ F@H.vS 01/06'))
    # print(Ha.getWechatVideo('14258814955767007275', '14776806611926650114_15_140_59_32_1735528000805808'))
    # print(Ha.getTaLuo())
    # print(Ha.getFish())
    print(Ha.getMusic('晴天'))
