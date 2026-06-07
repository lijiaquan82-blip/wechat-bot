from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse
from wechatpy.enterprise.crypto import WeChatCrypto
import xml.etree.ElementTree as ET
import os
import time

app = FastAPI(docs_url=None, redoc_url=None)

# 微信配置
TOKEN = "9Sc"
ENCODING_AES_KEY = "RzYFJY1KxtNSf6Yrwtbdrh8Up5rDUaApFtxLKNOKquB"
CORP_ID = "wwc62d41c4d8e389bf" 

crypto = WeChatCrypto(TOKEN, ENCODING_AES_KEY, CORP_ID)

@app.get("/api")
async def verify_url(msg_signature: str = Query(...), timestamp: str = Query(...), nonce: str = Query(...), echostr: str = Query(...)):
    echo_str = crypto.check_signature(msg_signature, timestamp, nonce, echostr)
    return PlainTextResponse(content=echo_str)

@app.post("/api")
async def receive_message(request: Request, msg_signature: str = Query(...), timestamp: str = Query(...), nonce: str = Query(...)):
    body = await request.body()
    decrypted_xml = crypto.decrypt_message(body, msg_signature, timestamp, nonce)
    xml_tree = ET.fromstring(decrypted_xml)
    
    # 核心策略：直接告诉微信“我收到了，正在处理中”，避免超时断连
    from_user = xml_tree.find("FromUserName").text
    to_user = xml_tree.find("ToUserName").text
    
    # 构建一个简短的“正在思考中...”回复
    reply_xml = f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[脑电波接收中... AI 正在解析，请稍等 5 秒！]]></Content>
</xml>"""
    
    # 立即加密并返回，这样微信那边就不会认为我们超时了
    encrypted_reply = crypto.encrypt_message(reply_xml, nonce, timestamp)
    
    # 注意：这里我们不做 AI 逻辑，只做回执。
    # 微信企业号现在支持“被动回复”处理复杂逻辑，但如果真要求极速，通常建议后续对接企业微信主动推送 API。
    # 这里我们尝试简单合并，如果还是超时，说明 Gemini 对你现在的网络来说太慢了。
    
    return PlainTextResponse(content=encrypted_reply)
