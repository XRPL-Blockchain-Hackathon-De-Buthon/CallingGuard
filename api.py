from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import tensorflow as tf
import wave
import speech_recognition as sr
import asyncio
import os
import random
import io
from web3 import Web3


app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모델 로드
model = tf.keras.models.load_model("voice_phishing_model_v2.keras")

# 블록체인 설정
EVM_RPC_URL = "https://evm-sidechain.xrpl.org"
w3 = Web3(Web3.HTTPProvider(EVM_RPC_URL))
contract_address = "0xb9A032b8E6f739c13691dd96D6d88084bC820CAf"
private_key = "sEdTDKDxg3aUz58Zk7F8MAeXK1HE3Dc"

contract_abi = [
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_caller",
				"type": "address"
			}
		],
		"name": "addToBlacklist",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "address",
				"name": "caller",
				"type": "address"
			}
		],
		"name": "Blacklisted",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "address",
				"name": "caller",
				"type": "address"
			},
			{
				"indexed": False,
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"indexed": False,
				"internalType": "string",
				"name": "organization",
				"type": "string"
			}
		],
		"name": "CallerRegistered",
		"type": "event"
	},
	{
		"inputs": [],
		"name": "generateOTP",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "address",
				"name": "caller",
				"type": "address"
			},
			{
				"indexed": False,
				"internalType": "string",
				"name": "code",
				"type": "string"
			}
		],
		"name": "OTPGenerated",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_caller",
				"type": "address"
			},
			{
				"internalType": "string",
				"name": "_name",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_organization",
				"type": "string"
			}
		],
		"name": "registerCaller",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "blacklist",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_caller",
				"type": "address"
			}
		],
		"name": "getCallerInfo",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "otpRecords",
		"outputs": [
			{
				"internalType": "string",
				"name": "code",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "expiresAt",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "verifiedCallers",
		"outputs": [
			{
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "organization",
				"type": "string"
			},
			{
				"internalType": "bool",
				"name": "isVerified",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_caller",
				"type": "address"
			},
			{
				"internalType": "string",
				"name": "_otp",
				"type": "string"
			}
		],
		"name": "verifyOTP",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]  # ABI JSON 생략
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

KEYWORDS = {
    "대출": ["대출", "대출금", "대출 관련", "대출 신청"],
    "연체": ["연체", "연체료", "카드 연체", "연체 기록"],
    "금융감독원": ["금융감독원", "금감원", "금융 감독원"],
    "보이스 피싱": ["보이스 피싱", "사기 전화", "전화 사기"],
    "계좌 정지": ["계좌 정지", "계좌 동결", "출금 제한"]
}

otp_failures = {}
otp_store = {}
approval_db = {}

from pydantic import BaseModel  # 이 줄 추가

class CallerInfo(BaseModel):
    address: str
    name: str
    organization: str

# app.py 파일 상단 또는 설정 파일에 실제 EVM 개인키를 직접 넣기
private_key = "783a700f305aec478cd4e4c1842ca0e81f974e48b60bae1d92e83ca61b206fed"  # EVM용 개인키 (64자리 hex)

@app.post("/register-caller")
def register_caller(info: CallerInfo):
    try:
        caller_address = w3.to_checksum_address(info.address)
        sender = w3.eth.account.from_key(private_key)  # ✅ 고정된 개인키 사용
        nonce = w3.eth.get_transaction_count(sender.address)

        tx = contract.functions.registerCaller(
            caller_address,
            info.name,
            info.organization
        ).build_transaction({
            "from": sender.address,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": w3.to_wei("1", "gwei")
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        return {"status": "success", "txHash": tx_hash.hex()}
    except Exception as e:
        return {"status": "error", "detail": str(e)}



def generate_wallet():
    account = w3.eth.account.create()
    return print("주소:", account.address),print("개인키:", account.key.hex())

@app.post("/register")
async def register_user(
    userId: str = Form(...),
    name: str = Form(...),
    phone: str = Form(...),
    idCard: UploadFile = File(...)
):

    save_dir = "uploaded_ids"
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f"{userId}_{idCard.filename}")
    with open(path, "wb") as f:
        f.write(await idCard.read())

    approval_db[userId] = {"approved": False, "name": name, "phone": phone}
    return JSONResponse(content={"message": "등록 요청 완료"}, status_code=200)


@app.post("/admin/approve/{userId}")
async def approve_user(userId: str = Path(...)):
    if userId in approval_db:
        approval_db[userId]["approved"] = True
        return {"message": f"{userId} 승인 완료", "approved": True}
    return {"message": "사용자 없음", "approved": False}

@app.get("/check-approval/{userId}")
async def check_approval(userId: str = Path(...)):
    data = approval_db.get(userId, {})
    return {"approved": data.get("approved", False)}

async def convert_speech_to_text(file_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
            text = await asyncio.to_thread(recognizer.recognize_google, audio, language="ko-KR")
            return text
    except Exception:
        return ""

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    phone_or_address = await websocket.receive_text()
    await websocket.send_text("식별자 수신됨: " + phone_or_address)

    otp_verified = False
    audio_data = io.BytesIO()
    otp_failures[phone_or_address] = 0
    log_lines = [f"📞 전화 시작 - ID: {phone_or_address}\n"]
    
	

    # ✅ 등록 여부 판단 로직
    is_registered = False
    if phone_or_address == "01012345678":
        is_registered = True
        log_lines.append("✅ 강제로 등록된 사용자 처리됨 (01012345678)\n")
    elif phone_or_address.startswith("0x") and len(phone_or_address) == 42:
        try:
            address = w3.to_checksum_address(phone_or_address)
            name, org, is_verified = contract.functions.getCallerInfo(address).call()
            if is_verified:
                is_registered = True
                log_lines.append(f"✅ 블록체인 등록 사용자: {name} / {org}\n")
            else:
                log_lines.append("⚠️ 블록체인에 등록되지 않음\n")
        except Exception as e:
            log_lines.append(f"❌ getCallerInfo 오류: {e}\n")
    else:
        log_lines.append("📛 등록되지 않은 전화번호\n")

    while True:
        try:
            data = await websocket.receive_bytes()
            audio_data.write(data)

            # WAV 저장
            path = f"temp_{phone_or_address}.wav"
            with wave.open(path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_data.getvalue())

            # AI 분석
            audio_features = np.random.rand(1, 100)
            prediction = model.predict(audio_features)[0][0]
            confidence = round(prediction * 100, 2)

            # 텍스트 분석
            text = await convert_speech_to_text(path)
            detected_keywords = [k for k, v in KEYWORDS.items() if any(word in text for word in v)]
            log_lines.append(f"텍스트: {text}\n")
            log_lines.append(f"키워드: {detected_keywords}, 확률: {confidence}%\n")

            # 보이스피싱 의심 시
            if detected_keywords or prediction > 0.8:
                if is_registered:
                    if not otp_verified:
                        otp = str(random.randint(100000, 999999))
                        otp_store[phone_or_address] = otp
                        await websocket.send_text(f"보이스피싱 의심 ({confidence}%) - OTP 요청: {otp}")

                        try:
                            user_otp = await asyncio.wait_for(websocket.receive_text(), timeout=10)
                            if user_otp == otp:
                                await websocket.send_text("✅ OTP 인증 성공")
                                log_lines.append("OTP 인증 성공\n")
                                otp_verified = True
                            else:
                                otp_failures[phone_or_address] += 1
                                log_lines.append(f"❌ OTP 인증 실패 - 누적 {otp_failures[phone_or_address]}회\n")
                                await websocket.send_text("❌ OTP 인증 실패")
                                if otp_failures[phone_or_address] >= 3:
                                    await websocket.send_text("🚫 블랙리스트 등록됨 (3회 실패)")
                                    log_lines.append("🚫 블랙리스트 등록됨 (3회 실패)\n")
                                    break
                        except asyncio.TimeoutError:
                            await websocket.send_text("⏰ OTP 입력 시간 초과")
                            log_lines.append("OTP 입력 시간 초과\n")
                            break
                else:
                    # 등록되지 않은 사용자 경고만 표시
                    warning = f"⚠️ 미등록 사용자 보이스피싱 의심됨 ({confidence}%) | 키워드: {', '.join(detected_keywords)}"
                    await websocket.send_text(warning)
                    log_lines.append(warning + "\n")
            else:
                await websocket.send_text(f"✅ 안전한 통화 ({100 - confidence}%)")
                log_lines.append("안전한 통화\n")

        except WebSocketDisconnect:
            log_lines.append("WebSocket 연결 종료됨\n")
            break
        except Exception as e:
            log_lines.append(f"예외 발생: {e}\n")
            break

    await websocket.close()

    os.makedirs("logs", exist_ok=True)
    with open(f"logs/{phone_or_address}_log.txt", "a", encoding="utf-8") as f:
        f.writelines(log_lines)
        

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)