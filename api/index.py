from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse
from wechatpy.enterprise.crypto import WeChatCrypto
import xml.etree.ElementTree as ET

app = FastAPI(docs_url=None, redoc_url=None)

# 你的专属密钥（我已经帮你完整填好了，千万别动这里！）
TOKEN = "9Sc"
ENCODING_AES_KEY = "RzYFJY1KxtNSf6Yrwtbdrh8Up5rDUaApFtxLKNOKquB"
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
    except Exception:
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
        print(f"Error: {e}")
        return PlainTextResponse(content="success")
