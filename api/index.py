from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse
from wechatpy.enterprise.crypto import WeChatCrypto
import xml.etree.ElementTree as ET
import google.generativeai as genai
import os

app = FastAPI(docs_url=None, redoc_url=None)

# 微信的配置
TOKEN = "9Sc"
ENCODING_AES_KEY = "RzYFJY1KxtNSf6Yrwtbdrh8Up5rDUaApFtxLKNOKquB"
CORP_ID = "wwc62d41c4d8e389bf" 

crypto = WeChatCrypto(TOKEN, ENCODING_AES_KEY, CORP_ID)

# 唤醒 Gemini 引擎！(它会自动去 Vercel 的保险箱里拿密码)
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    # 选用 flash 模型，速度最快，极其适合处理日常灵感和长文本总结
    model = genai.GenerativeModel('gemini-1.5-flash')

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
            # 1. 抓取你发在微信里的话
            user_input = xml_tree.find("Content").text
            print(f"📥 收到微信消息: {user_input}")
            
            # 2. 召唤 AI 进行处理！
            if GOOGLE_API_KEY:
                # 给 AI 设定一个人设和任务
                prompt = f"你是一个硬核的研究助理。请用简洁锐利的语言，帮我总结或回应以下内容，不要超过100字：\n\n{user_input}"
                response = model.generate_content(prompt)
                
                # 3. 打印出 AI 的神级回复
                print(f"✨ 脑电波分析完成: {response.text}")
            else:
                print("⚠️ 没找到 Gemini API Key，AI 引擎未启动！")
            
        return PlainTextResponse(content="success")
    except Exception as e:
        print(f"处理报错: {e}")
        return PlainTextResponse(content="success")
