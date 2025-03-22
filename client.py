import asyncio
import websockets
import wave
from web3 import Web3
import requests

# 오디오 파일 경로
AUDIO_PATH = "data/test_call_converted.wav"
WS_URI = "ws://127.0.0.1:8000/ws"  # 필요 시 서버 주소 변경

async def send_audio():
    async with websockets.connect(WS_URI) as websocket:
        print("WebSocket 연결됨")

        choice = input("1. 앱 미설치 시나리오\n2. 회원가입 및 지갑 생성\n\n선택 (1/2): ")

        if choice == "1":
            phone_number = input("전화번호를 입력하세요: ")
            await websocket.send(phone_number)
            print(f"{phone_number} 전송 완료")

        elif choice == "2":
            phone_number = input("전화번호를 입력하세요: ")
            w3 = Web3()
            acct = w3.eth.account.create()
            address = acct.address
            private_key = acct.key.hex()

            print(f"주소: {address}\n개인키: {private_key}")

            # 👇 서버에 등록 요청 보내기
            register_url = "http://127.0.0.1:8000/register-caller"
            response = requests.post(register_url, json={
                "address": address,
                "name": "홍길동",
                "organization": "테스트은행"
            })

            print("등록 요청 결과:", response.text)

            await websocket.send(address)

            # 🚨 필요 시 여기서 FastAPI 서버에 registerCaller 요청 가능

        else:
            print("잘못된 선택입니다. 종료합니다.")
            return

        # 초기 서버 응답
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print("서버 응답:", response)
        except asyncio.TimeoutError:
            print("서버 응답 시간 초과")
            return

        # 오디오 파일 열기
        try:
            with wave.open(AUDIO_PATH, "rb") as wf:
                print(f"오디오 파일 전송 시작: {AUDIO_PATH}")
                while True:
                    chunk = wf.readframes(16000)
                    if not chunk:
                        print("오디오 전송 완료")
                        break

                    await websocket.send(chunk)

                    try:
                        msg = await asyncio.wait_for(websocket.recv(), timeout=3)
                        print("서버 메시지:", msg)

                        if "OTP 요청" in msg:
                            otp = input("OTP를 입력하세요: ")
                            await websocket.send(otp)

                            otp_result = await websocket.recv()
                            print("OTP 결과:", otp_result)

                            if "실패" in otp_result or "블랙리스트" in otp_result:
                                print("연결 종료")
                                return

                    except asyncio.TimeoutError:
                        # 응답 없음 → 계속 진행
                        pass
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {AUDIO_PATH}")
        except Exception as e:
            print("오류 발생:", e)

# 실행
if __name__ == "__main__":
    asyncio.run(send_audio())
