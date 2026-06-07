from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse
from wechatpy.enterprise.crypto import WeChatCrypto
import xml.etree.ElementTree as ET

app = FastAPI(docs_url=None, redoc_url=None)

TOKEN = "9Sc"
ENCODING_AES_KEY = "RzYFJY1KxtNSf6Yrwtbdrh8Up5rDUaApFtxLKNOKquB"
# ⚠️ 常见天坑：这里一定要填“我的企业”页面最底部的企业ID（ww开头），千万不要填应用的 AgentId！
CORP_ID = "wwc62d41c4d8e389bf" 

crypto = WeChatCrypto(TOKEN, ENCODING_AES_KEY, CORP_ID)

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
        # 这行代码是破局的关键！它会把报错原因精准打印到 Vercel 日志里
        print(f"❌ 微信验证解密失败！原因: {e}")
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
            content = xml_tree.find("Content").text
            print(f"🚀 [Vercel 云端接收成功] 你的灵感: {content}")
            
        return PlainTextResponse(content="success")
    except Exception as e:
        print(f"处理报错: {e}")
        return PlainTextResponse(content="success")
