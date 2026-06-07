from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse
from wechatpy.enterprise.crypto import WeChatCrypto
import xml.etree.ElementTree as ET
from google import genai  # 这是 Google 最新的引用方式
import os

app = FastAPI(docs_url=None, redoc_url=None)

# 微信的配置
TOKEN = "9Sc"
ENCODING_AES_KEY = "RzYFJY1KxtNSf6Yrwtbdrh8Up5rDUaApFtxLKNOKquB"
CORP_ID = "wwc62d41c4d8e389bf" 

crypto = WeChatCrypto(TOKEN, ENCODING_AES_KEY, CORP_ID)

# 唤醒最新版 Gemini 引擎！
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
client = None
if GOOGLE_API_KEY:
    client = genai.Client(api_key=GOOGLE_API_KEY)

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
        print(f"❌ 验证解密失败！原因: {e}")
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
        decrypted_xml = crypto.decrypt_message(body, msg_signature, timestamp, nonce)
        xml_tree = ET.fromstring(decrypted_xml)
        msg_type = xml_tree.find("MsgType").text
        
        if msg_type == "text":
            user_input = xml_tree.find("Content").text
            print(f"📥 收到微信消息: {user_input}")
            
            # 使用最新版客户端发送请求
            if client:
                prompt = f"你是一个硬核的研究助理。请用简洁锐利的语言，帮我总结或回应以下内容，不要超过100字：\n\n{user_input}"
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt,
                )
                print(f"✨ 脑电波分析完成: {response.text}")
            else:
                print("⚠️ 没找到 Gemini API Key，AI 引擎未启动！")
            
        return PlainTextResponse(content="success")
    except Exception as e:
        print(f"处理报错: {e}")
        return PlainTextResponse(content="success")
# 强制重启读取 API KEY
