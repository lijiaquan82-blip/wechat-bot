from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse
from wechatpy.enterprise.crypto import WeChatCrypto
import xml.etree.ElementTree as ET
import uvicorn
import os

app = FastAPI(docs_url=None, redoc_url=None)

TOKEN = "9Sc"
ENCODING_AES_KEY = "RzYFJY1KxtNSf6Yrwtbdrh8Up5rDUaApFtxLKNOKquB"
# 确保这里是你真实的 ww 开头的企业 ID
CORP_ID = "wwc62d41c4d8e389bf"

crypto = WeChatCrypto(TOKEN, ENCODING_AES_KEY, CORP_ID)

# 路径我统一改回了 /wechat，更标准
@app.get("/wechat")
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

@app.post("/wechat")
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
            print(f"🚀 [云端接收成功] 你的灵感: {content}")
            
        return PlainTextResponse(content="success")
    except Exception as e:
        print(f"处理报错: {e}")
        return PlainTextResponse(content="success")

# 这是给 Zeabur 服务器专门准备的启动引擎
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
