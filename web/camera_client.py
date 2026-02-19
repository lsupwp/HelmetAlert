"""
Camera Stream Client - ส่งภาพจากกล้องขึ้น WebSocket Server (30 FPS)

Requirements:
    pip install opencv-python websockets
    
Usage:
    python camera_client.py [MAC_ADDRESS]
    
Example:
    python camera_client.py AA:BB:CC:DD:EE:FF
"""

import asyncio
import websockets
import cv2
import base64
import sys
import uuid

def get_mac_address():
    """ดึง MAC address หรือใช้จาก argument"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    # ถ้าไม่มี argument ให้สร้าง fake MAC address
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                    for elements in range(0,2*6,2)][::-1])
    return mac

async def stream_camera(mac_address: str):
    """ส่ง stream จากกล้องไปยัง server"""
    # ตั้งค่า
    WS_URL = f"ws://localhost:8000/ws/images/camera/{mac_address}"
    CAMERA_SOURCE = 0  # 0 = webcam, หรือใส่ RTSP URL
    WIDTH = 640
    HEIGHT = 480
    FPS = 30
    QUALITY = 80
    
    # เปิดกล้อง
    cap = cv2.VideoCapture(CAMERA_SOURCE)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    
    if not cap.isOpened():
        print("❌ ไม่สามารถเปิดกล้องได้")
        return
    
    print(f"📹 Camera MAC: {mac_address}")
    print(f"📹 เปิดกล้องสำเร็จ - ส่งภาพ {FPS} FPS")
    print(f"🔗 เชื่อมต่อไปยัง {WS_URL}...")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ เชื่อมต่อสำเร็จ! กำลังส่งภาพ...\n")
            
            frame_count = 0
            while True:
                # อ่านภาพจากกล้อง
                ret, frame = cap.read()
                if not ret:
                    break
                
                # ปรับขนาด
                frame = cv2.resize(frame, (WIDTH, HEIGHT))
                
                # เข้ารหัสเป็น JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, QUALITY])
                
                # แปลงเป็น base64
                jpg_as_text = base64.b64encode(buffer.tobytes()).decode('utf-8')
                
                # ส่งไปยัง WebSocket
                await websocket.send(f"data:image/jpeg;base64,{jpg_as_text}")
                
                frame_count += 1
                if frame_count % 100 == 0:
                    print(f"📊 ส่งแล้ว {frame_count} frames")
                
                # หน่วง เพื่อให้ได้ 30 FPS
                await asyncio.sleep(1.0 / FPS)
                
    except websockets.exceptions.ConnectionClosed:
        print("⚠️  การเชื่อมต่อถูกปิด")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        cap.release()
        print("🔒 ปิดกล้องแล้ว")

if __name__ == "__main__":
    mac_address = get_mac_address()
    
    print("=" * 60)
    print("🎥 Camera Stream Client - 30 FPS")
    print("=" * 60)
    print(f"📱 MAC Address: {mac_address}")
    print(f"🌐 View at: http://localhost:8000/images/{mac_address}")
    print("💡 กด Ctrl+C เพื่อหยุด")
    print("=" * 60)
    print()
    
    try:
        asyncio.run(stream_camera(mac_address))
    except KeyboardInterrupt:
        print("\n👋 หยุดโปรแกรม")
