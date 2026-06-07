from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse
from wechatpy.enterprise.crypto import WeChatCrypto
import xml.etree.ElementTree as ET
from google import genai
import os
import time  # 新增了时间模块，微信回复需要时间戳

app = FastAPI(docs_url=None, redoc_url=None)

# 微信的配置
TOKEN = "9Sc"
ENCODING_AES_KEY = "RzYFJY1KxtNSf6Yrwtbdrh8Up5rDUaApFtxLKNOKquB"
CORP_ID = "wwc62d41c4d8e389bf" 

crypto = WeChatCrypto(TOKEN, ENCODING_AES_KEY, CORP_ID)

# 唤醒 Google 引擎
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
        # 1. 拆开微信寄来的密文信封
        decrypted_xml = crypto.decrypt_message(body, msg_signature, timestamp, nonce)
        xml_tree = ET.fromstring(decrypted_xml)
        msg_type = xml_tree.find("MsgType").text
        
        if msg_type == "text":
            # 抓取用户说的话，以及发件人、收件人的名字
            user_input = xml_tree.find("Content").text
            from_user = xml_tree.find("FromUserName").text
            to_user = xml_tree.find("ToUserName").text
            
            reply_content = "云端大脑思考中，请稍后再试..."
            
            # 2. 召唤 AI 引擎
            if client:
                try:
                    # 注入专属的硬核提示词，直接锁定你的高频使用场景
                    prompt = f"作为我的专属科研与投资助理，请用精炼、锐利的语言回答。若涉及固态电池、新能源材料或股市盘面，请提供硬核分析。回答请控制在200字以内：\n\n{user_input}"
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    reply_content = response.text
                except Exception as e:
                    reply_content = f"脑电波暂时阻塞: {e}"
                    
            # 3. 写回信：构造回复的 XML 明文（注意：To和From要反转过来）
            reply_xml = f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{reply_content}]]></Content>
</xml>"""
            
            # 4. 把明文装进加密信封，打上微信认识的火漆印章
            encrypted_reply = crypto.encrypt_message(reply_xml, nonce, timestamp)
            
            # 5. 原路发射，直达你的手机！
            return PlainTextResponse(content=encrypted_reply)
            
        return PlainTextResponse(content="success")
    except Exception as e:
        print(f"处理报错: {e}")
        return PlainTextResponse(content="success")
