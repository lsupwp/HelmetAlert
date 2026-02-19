from .route import Routes, Request
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from fastapi.responses import JSONResponse
from typing import Dict, List
import json

class Images(Routes):
    def __init__(self):
        super().__init__()
        # หน้าแสดงผล
        self.router.add_api_route("/images", self.images, methods=["GET"])
        self.router.add_api_route("/images/{mac_address}", self.images_channel, methods=["GET"])
        
        # API สำหรับดึงรายการกล้อง (ใช้ JSONResponse)
        self.router.add_api_route("/api/cameras", self.get_cameras, methods=["GET"], response_class=JSONResponse)
        
        # เก็บ connections แยกตาม MAC address
        # Format: {"mac_address": {"camera": WebSocket, "viewers": [WebSocket, ...]}}
        self.channels: Dict[str, dict] = {}
        
        # Register WebSocket routes แบบถูกต้อง
        self._register_websocket_routes()
    
    def _register_websocket_routes(self):
        """Register WebSocket routes"""
        @self.router.websocket("/ws/images/camera/{mac_address}")
        async def camera_ws(websocket: WebSocket, mac_address: str):
            await self.camera_endpoint(websocket, mac_address)
        
        @self.router.websocket("/ws/images/view/{mac_address}")
        async def viewer_ws(websocket: WebSocket, mac_address: str):
            await self.viewer_endpoint(websocket, mac_address)
    
    def get_cameras(self):
        """API สำหรับดึงรายการกล้องทั้งหมด"""
        return {
            "channels": list(self.channels.keys()),
            "total": len(self.channels)
        }

    def images(self, request: Request):
        """หน้าแสดงรายการ channels ทั้งหมด"""
        return self.render(
            request=request,
            name="images.html",
            context={
                "title": "All Cameras",
                "channels": list(self.channels.keys())
            }
        )
    
    def images_channel(self, request: Request, mac_address: str):
        """หน้าแสดงภาพจากกล้องเฉพาะ MAC address"""
        return self.render(
            request=request,
            name="images_channel.html",
            context={
                "title": f"Camera {mac_address}",
                "mac_address": mac_address
            }
        )
    
    async def camera_endpoint(self, websocket: WebSocket, mac_address: str):
        """WebSocket สำหรับกล้องส่งภาพเข้ามา"""
        await websocket.accept()
        
        # สร้าง channel ใหม่ถ้ายังไม่มี
        if mac_address not in self.channels:
            self.channels[mac_address] = {
                "camera": None,
                "viewers": []
            }
        
        # บันทึก camera connection
        self.channels[mac_address]["camera"] = websocket
        print(f"📹 Camera connected: {mac_address}")
        
        try:
            while True:
                # รับข้อมูลจากกล้อง
                data = await websocket.receive()
                
                # ส่งภาพไปยัง viewers ทั้งหมดใน channel นี้
                if "text" in data:
                    await self.broadcast_to_viewers(mac_address, data["text"])
                elif "bytes" in data:
                    await self.broadcast_to_viewers_bytes(mac_address, data["bytes"])
                    
        except WebSocketDisconnect:
            print(f"📹 Camera disconnected: {mac_address}")
            if mac_address in self.channels:
                self.channels[mac_address]["camera"] = None
        except Exception as e:
            print(f"❌ Camera error ({mac_address}): {e}")
            if mac_address in self.channels:
                self.channels[mac_address]["camera"] = None
    
    async def viewer_endpoint(self, websocket: WebSocket, mac_address: str):
        """WebSocket สำหรับ viewers ดูภาพ"""
        await websocket.accept()
        
        # สร้าง channel ใหม่ถ้ายังไม่มี
        if mac_address not in self.channels:
            self.channels[mac_address] = {
                "camera": None,
                "viewers": []
            }
        
        # เพิ่ม viewer
        self.channels[mac_address]["viewers"].append(websocket)
        print(f"👁️  Viewer connected to: {mac_address} (total: {len(self.channels[mac_address]['viewers'])})")
        
        # ส่ง status ว่ากล้องออนไลน์หรือไม่
        camera_online = self.channels[mac_address]["camera"] is not None
        await websocket.send_json({"type": "status", "camera_online": camera_online})
        
        try:
            while True:
                # รับข้อมูลจาก viewer (ถ้ามี - เช่นคำสั่งควบคุม)
                data = await websocket.receive()
                # สามารถเพิ่ม logic สำหรับส่งคำสั่งกลับไปยังกล้องได้ที่นี่
                
        except WebSocketDisconnect:
            print(f"👁️  Viewer disconnected from: {mac_address}")
            if mac_address in self.channels and websocket in self.channels[mac_address]["viewers"]:
                self.channels[mac_address]["viewers"].remove(websocket)
        except Exception as e:
            print(f"❌ Viewer error ({mac_address}): {e}")
            if mac_address in self.channels and websocket in self.channels[mac_address]["viewers"]:
                self.channels[mac_address]["viewers"].remove(websocket)
    
    async def broadcast_to_viewers(self, mac_address: str, message: str):
        """ส่งข้อมูล text ไปยัง viewers ใน channel นี้"""
        if mac_address not in self.channels:
            return
        
        viewers = self.channels[mac_address]["viewers"]
        disconnected = []
        
        for viewer in viewers:
            try:
                await viewer.send_text(message)
            except:
                disconnected.append(viewer)
        
        # ลบ viewers ที่ disconnect
        for viewer in disconnected:
            viewers.remove(viewer)
    
    async def broadcast_to_viewers_bytes(self, mac_address: str, data: bytes):
        """ส่งข้อมูล bytes ไปยัง viewers ใน channel นี้"""
        if mac_address not in self.channels:
            return
        
        viewers = self.channels[mac_address]["viewers"]
        disconnected = []
        
        for viewer in viewers:
            try:
                await viewer.send_bytes(data)
            except:
                disconnected.append(viewer)
        
        # ลบ viewers ที่ disconnect
        for viewer in disconnected:
            viewers.remove(viewer)