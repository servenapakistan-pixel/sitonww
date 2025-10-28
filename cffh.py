#!/usr/bin/env python3
# terminal_client.py - Текстовый клиент для мультиплеер терминала

import asyncio
import websockets
import json
import sys
import threading
from datetime import datetime

class TextTerminalClient:
    def __init__(self, server_url="ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.username = "user"
        self.connected = False
        
    async def connect(self):
        """Подключение к серверу"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            print("✅ Подключено к серверу")
            print("📝 Вводите команды (exit для выхода)")
            print("-" * 50)
            
            # Запускаем прием сообщений
            asyncio.create_task(self.receive_messages())
            
            # Основной цикл ввода
            await self.input_loop()
            
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            
    async def input_loop(self):
        """Цикл ввода команд"""
        while self.connected:
            try:
                command = await asyncio.get_event_loop().run_in_executor(
                    None, input, f"{self.username}@terminal> "
                )
                
                if command.strip().lower() in ['exit', 'quit']:
                    break
                    
                if command.strip():
                    message = {
                        'type': 'command',
                        'content': command,
                        'username': self.username
                    }
                    await self.websocket.send(json.dumps(message))
                    
            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                print(f"❌ Ошибка отправки: {e}")
                
        await self.disconnect()
        
    async def receive_messages(self):
        """Прием сообщений от сервера"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.display_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            print("❌ Соединение разорвано")
            self.connected = False
            
    def display_message(self, data):
        """Отображение полученного сообщения"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if data['type'] == 'command':
            print(f"[{timestamp}] 🎮 {data['username']}: {data['content']}")
        elif data['type'] == 'output':
            print(f"[{timestamp}] 📋 {data['username']}:")
            print(data['content'])
            print("-" * 40)
        elif data['type'] == 'system':
            print(f"[{timestamp}] 🔔 {data['content']}")
        elif data['type'] == 'error':
            print(f"[{timestamp}] ❌ {data['content']}")
            
    async def disconnect(self):
        """Отключение от сервера"""
        self.connected = False
        if self.websocket:
            await self.websocket.close()
        print("👋 Отключено от сервера")

async def main():
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    else:
        server_url = "ws://localhost:8765"
        
    client = TextTerminalClient(server_url)
    await client.connect()

if __name__ == "__main__":
    asyncio.run(main())