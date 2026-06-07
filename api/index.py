from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse
from wechatpy.enterprise.crypto import WeChatCrypto
import xml.etree.ElementTree as ET
from google import genai
import os
import time

app = FastAPI(docs_url=None, redoc_url=None)

# 微信配置
TOKEN = "9Sc"
ENCODING_AES_KEY = "RzYFJY1KxtNSf6Yrwtbdrh8Up5rDUaApFtxLKNOKquB"
CORP_ID = "wwc62d41c4d8e389bf" 

crypto = WeChatCrypto(TOKEN, ENCODING_AES_KEY, CORP_ID)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/api")
async def verify_url(
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...)
):
    try:
        echo_str = crypto.check_signature(msg_signature, timestamp, nonce, echostr)
        return PlainTextResponse(content=echo_str)
    except Exception as e:
        return PlainTextResponse(content="error", status_code=403)

@app.post("/api")
async def receive_message(
    request: Request,
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...)
):
    body = await request.body()
    try:
        # 解密微信消息
        decrypted_xml = crypto.decrypt_message(body, msg_signature, timestamp, nonce)
        xml_tree = ET.fromstring(decrypted_xml)
        
        from_user = xml_tree.find("FromUserName").text
        to_user = xml_tree.find("ToUserName").text
        user_input = xml_tree.find("Content").text

        # 尝试让 AI 回复
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=f"作为科研助理，请精炼回复：{user_input}",
            )
            ai_reply = response.text
        except Exception:
            ai_reply = "大脑正在超频运行中，请稍后再试。"

        # 构造 XML 回复格式
        reply_xml = f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{ai_reply}]]></Content>
</xml>"""
        
        # 加密并返回
        return PlainTextResponse(content=crypto.encrypt_message(reply_xml, nonce, timestamp))
            
    except Exception as e:
        # 如果处理失败，返回空字符串让微信不报错
        return PlainTextResponse(content="")
