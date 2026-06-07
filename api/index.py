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
async def verify_url(msg_signature: str = Query(...), timestamp: str = Query(...), nonce: str = Query(...), echostr: str = Query(...)):
    return PlainTextResponse(content=crypto.check_signature(msg_signature, timestamp, nonce, echostr))

@app.post("/api")
async def receive_message(request: Request, msg_signature: str = Query(...), timestamp: str = Query(...), nonce: str = Query(...)):
    body = await request.body()
    decrypted_xml = crypto.decrypt_message(body, msg_signature, timestamp, nonce)
    xml_tree = ET.fromstring(decrypted_xml)
    
    from_user = xml_tree.find("FromUserName").text
    to_user = xml_tree.find("ToUserName").text
    user_input = xml_tree.find("Content").text

    # --- 灵魂注入区 ---
    # 定义你的“科研/投资助理”身份，AI 就会按这个标准回答你
    system_instruction = (
        "你是我专业的科研与投资助理。你的回答风格：1. 针对专业问题（电池/材料/股市），必须给出硬核、量化的分析；"
        "2. 不要说废话，不要礼貌寒暄，直接给结论；3. 如果我发的是长文章，请用【核心结论+关键数据+行动建议】格式总结。"
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=user_input,
            config={"system_instruction": system_instruction} # 这里注入灵魂！
        )
        ai_reply = response.text
    except Exception as e:
        ai_reply = "大脑正在超频处理你的深度问题，请稍后再发一次。"

    reply_xml = f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{ai_reply}]]></Content>
</xml>"""
    
    return PlainTextResponse(content=crypto.encrypt_message(reply_xml, nonce, timestamp))
