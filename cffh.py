# main.py
import asyncio
import aiohttp
from aiohttp import web
import json
import os
import subprocess
from datetime import datetime
import threading

# Глобальные переменные для хранения состояния
clients = []
command_history = []
users_online = 0

# Красивый HTML интерфейс
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Multiplayer Terminal</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #00ff88;
            --secondary: #0088ff;
            --accent: #ff0088;
            --background: #0a0a0f;
            --surface: #1a1a2f;
            --text: #e0e0ff;
            --text-secondary: #a0a0c0;
            --success: #00ff88;
            --warning: #ffaa00;
            --error: #ff4444;
        }
        
        body {
            font-family: 'JetBrains Mono', monospace;
            background: var(--background);
            color: var(--text);
            height: 100vh;
            overflow: hidden;
            background: linear-gradient(135deg, var(--background) 0%, #151525 100%);
        }
        
        .container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            padding: 0;
        }
        
        /* Header Styles */
        .header {
            background: rgba(26, 26, 47, 0.95);
            backdrop-filter: blur(20px);
            padding: 15px 25px;
            border-bottom: 2px solid var(--primary);
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 20px rgba(0, 255, 136, 0.1);
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.4em;
            font-weight: 600;
            color: var(--primary);
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }
        
        .logo-icon {
            font-size: 1.6em;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        .status-panel {
            display: flex;
            gap: 25px;
            align-items: center;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 15px;
            background: rgba(0, 136, 255, 0.1);
            border: 1px solid var(--secondary);
            border-radius: 8px;
            font-size: 0.9em;
        }
        
        .connection-status {
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }
        
        .connected {
            background: linear-gradient(135deg, var(--success), #00cc66);
            color: #000;
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
        }
        
        .disconnected {
            background: linear-gradient(135deg, var(--error), #cc3333);
            color: #fff;
        }
        
        /* Terminal Styles */
        .terminal-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            margin: 15px;
            gap: 15px;
        }
        
        .terminal {
            flex: 1;
            background: var(--surface);
            border: 2px solid rgba(0, 136, 255, 0.3);
            border-radius: 12px;
            padding: 20px;
            overflow-y: auto;
            font-size: 14px;
            line-height: 1.5;
            box-shadow: 
                inset 0 2px 10px rgba(0, 0, 0, 0.5),
                0 8px 32px rgba(0, 0, 0, 0.3);
            background: 
                radial-gradient(circle at 20% 80%, rgba(0, 136, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(0, 255, 136, 0.1) 0%, transparent 50%),
                var(--surface);
        }
        
        .terminal::-webkit-scrollbar {
            width: 8px;
        }
        
        .terminal::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
        }
        
        .terminal::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 4px;
        }
        
        /* Message Styles */
        .message {
            margin-bottom: 12px;
            padding: 8px 12px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.02);
            border-left: 3px solid transparent;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-10px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .message.command {
            border-left-color: var(--warning);
            background: rgba(255, 170, 0, 0.05);
        }
        
        .message.output {
            border-left-color: var(--success);
            background: rgba(0, 255, 136, 0.05);
        }
        
        .message.system {
            border-left-color: var(--secondary);
            background: rgba(0, 136, 255, 0.05);
        }
        
        .message.error {
            border-left-color: var(--error);
            background: rgba(255, 68, 68, 0.05);
        }
        
        .message-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 4px;
            font-size: 0.85em;
        }
        
        .username {
            font-weight: 600;
            color: var(--accent);
            text-shadow: 0 0 5px rgba(255, 0, 136, 0.3);
        }
        
        .timestamp {
            color: var(--text-secondary);
            font-size: 0.8em;
            margin-left: auto;
        }
        
        .message-content {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .command-content {
            color: var(--warning);
            font-weight: 500;
        }
        
        .output-content {
            color: var(--text);
        }
        
        .system-content {
            color: var(--secondary);
            font-style: italic;
        }
        
        .error-content {
            color: var(--error);
        }
        
        /* Input Area */
        .input-area {
            display: flex;
            gap: 12px;
            align-items: center;
            padding: 15px;
            background: var(--surface);
            border: 2px solid rgba(0, 136, 255, 0.3);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }
        
        .prompt {
            color: var(--primary);
            font-weight: 600;
            font-size: 1.1em;
            text-shadow: 0 0 5px rgba(0, 255, 136, 0.5);
        }
        
        .command-input {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text);
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            outline: none;
            caret-color: var(--primary);
            padding: 8px 0;
        }
        
        .command-input::placeholder {
            color: var(--text-secondary);
        }
        
        .user-controls {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .username-input {
            background: rgba(0, 136, 255, 0.1);
            border: 1px solid var(--secondary);
            color: var(--text);
            padding: 8px 12px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9em;
            min-width: 120px;
        }
        
        .clear-btn {
            background: rgba(255, 0, 136, 0.1);
            border: 1px solid var(--accent);
            color: var(--accent);
            padding: 8px 12px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9em;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .clear-btn:hover {
            background: rgba(255, 0, 136, 0.2);
            box-shadow: 0 0 10px rgba(255, 0, 136, 0.3);
        }
        
        /* Animations */
        .pulse {
            animation: pulseGlow 2s infinite;
        }
        
        @keyframes pulseGlow {
            0%, 100% { 
                box-shadow: 0 0 5px rgba(0, 255, 136, 0.5);
            }
            50% { 
                box-shadow: 0 0 20px rgba(0, 255, 136, 0.8);
            }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 10px;
                padding: 10px;
            }
            
            .status-panel {
                gap: 10px;
            }
            
            .status-item {
                padding: 6px 10px;
                font-size: 0.8em;
            }
            
            .terminal-container {
                margin: 10px;
            }
            
            .input-area {
                flex-direction: column;
                align-items: stretch;
            }
            
            .user-controls {
                justify-content: space-between;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <span class="logo-icon">🚀</span>
                <span>Multiplayer Terminal</span>
            </div>
            <div class="status-panel">
                <div class="status-item">
                    <span>👥</span>
                    <span id="users-count">0</span>
                </div>
                <div class="status-item">
                    <span>📁</span>
                    <span id="current-dir">/</span>
                </div>
                <div class="connection-status disconnected" id="connection-status">
                    ОФФЛАЙН
                </div>
            </div>
        </div>
        
        <div class="terminal-container">
            <div class="terminal" id="terminal">
                <div class="message system">
                    <div class="message-header">
                        <span class="username">🚀 Система</span>
                        <span class="timestamp" id="current-time">--:--:--</span>
                    </div>
                    <div class="message-content system-content">
                        Добро пожаловать в Multiplayer Terminal! 
                        Все команды и вывод видны всем участникам в реальном времени.
                    </div>
                </div>
            </div>
            
            <div class="input-area">
                <span class="prompt" id="prompt">$</span>
                <input type="text" class="command-input" id="command-input" 
                       placeholder="Введите команду..." disabled>
                <div class="user-controls">
                    <input type="text" class="username-input" id="username-input" 
                           placeholder="Ваше имя" value="user" maxlength="20">
                    <button class="clear-btn" id="clear-btn">Очистить</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        class MultiplayerTerminal {
            constructor() {
                this.ws = null;
                this.connected = false;
                this.terminal = document.getElementById('terminal');
                this.commandInput = document.getElementById('command-input');
                this.usernameInput = document.getElementById('username-input');
                this.connectionStatus = document.getElementById('connection-status');
                this.usersCount = document.getElementById('users-count');
                this.currentDir = document.getElementById('current-dir');
                this.prompt = document.getElementById('prompt');
                this.clearBtn = document.getElementById('clear-btn');
                
                this.commandHistory = [];
                this.historyIndex = -1;
                
                this.init();
            }
            
            init() {
                this.connect();
                this.setupEventListeners();
                this.updateTime();
                setInterval(() => this.updateTime(), 1000);
            }
            
            connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                console.log('Connecting to:', wsUrl);
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onopen = () => {
                    this.connected = true;
                    this.updateConnectionStatus();
                    this.addSystemMessage('✅ Подключено к серверу');
                    this.commandInput.disabled = false;
                    this.commandInput.focus();
                };
                
                this.ws.onclose = (event) => {
                    this.connected = false;
                    this.updateConnectionStatus();
                    this.addSystemMessage(`❌ Соединение потеряно (код: ${event.code}). Переподключение...`);
                    this.commandInput.disabled = true;
                    
                    setTimeout(() => this.connect(), 3000);
                };
                
                this.ws.onerror = (error) => {
                    this.addSystemMessage('❌ Ошибка соединения');
                    console.error('WebSocket error:', error);
                };
                
                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    } catch (e) {
                        console.error('Error parsing message:', e);
                        this.addSystemMessage('❌ Ошибка разбора сообщения');
                    }
                };
            }
            
            handleMessage(data) {
                switch(data.type) {
                    case 'command':
                        this.addCommandMessage(data.username, data.content, data.timestamp);
                        break;
                    case 'output':
                        this.addOutputMessage(data.username, data.content, data.timestamp);
                        break;
                    case 'system':
                        this.addSystemMessage(data.content, data.timestamp);
                        break;
                    case 'users_count':
                        this.usersCount.textContent = data.count;
                        break;
                    case 'current_dir':
                        this.currentDir.textContent = data.dir;
                        this.prompt.textContent = `[${data.dir}] $`;
                        break;
                    case 'error':
                        this.addErrorMessage(data.content, data.timestamp);
                        break;
                }
            }
            
            addCommandMessage(username, content, timestamp) {
                this.addMessage('command', username, content, timestamp);
            }
            
            addOutputMessage(username, content, timestamp) {
                this.addMessage('output', username, content, timestamp);
            }
            
            addSystemMessage(content, timestamp = null) {
                this.addMessage('system', '🚀 Система', content, timestamp);
            }
            
            addErrorMessage(content, timestamp) {
                this.addMessage('error', '❌ Ошибка', content, timestamp);
            }
            
            addMessage(type, username, content, timestamp = null) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                
                const time = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
                
                messageDiv.innerHTML = `
                    <div class="message-header">
                        <span class="username">${username}</span>
                        <span class="timestamp">${time}</span>
                    </div>
                    <div class="message-content ${type}-content">${this.escapeHtml(content)}</div>
                `;
                
                this.terminal.appendChild(messageDiv);
                this.terminal.scrollTop = this.terminal.scrollHeight;
            }
            
            escapeHtml(unsafe) {
                return unsafe
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;")
                    .replace(/\n/g, '<br>');
            }
            
            sendCommand(command) {
                if (!this.connected || !command.trim()) return;
                
                const message = {
                    type: 'command',
                    content: command,
                    username: this.usernameInput.value || 'user'
                };
                
                this.ws.send(JSON.stringify(message));
                this.commandInput.value = '';
            }
            
            updateConnectionStatus() {
                if (this.connected) {
                    this.connectionStatus.textContent = 'ОНЛАЙН';
                    this.connectionStatus.className = 'connection-status connected pulse';
                } else {
                    this.connectionStatus.textContent = 'ОФФЛАЙН';
                    this.connectionStatus.className = 'connection-status disconnected';
                }
            }
            
            updateTime() {
                const now = new Date();
                document.getElementById('current-time').textContent = now.toLocaleTimeString();
            }
            
            setupEventListeners() {
                // Command input
                this.commandInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        const command = this.commandInput.value.trim();
                        if (command) {
                            this.sendCommand(command);
                            this.commandHistory.push(command);
                            this.historyIndex = this.commandHistory.length;
                        }
                    }
                });
                
                // Command history with arrow keys
                this.commandInput.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        if (this.commandHistory.length > 0) {
                            if (this.historyIndex <= 0) {
                                this.historyIndex = this.commandHistory.length;
                            }
                            this.historyIndex--;
                            this.commandInput.value = this.commandHistory[this.historyIndex];
                        }
                    } else if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        if (this.historyIndex < this.commandHistory.length - 1) {
                            this.historyIndex++;
                            this.commandInput.value = this.commandHistory[this.historyIndex];
                        } else {
                            this.historyIndex = this.commandHistory.length;
                            this.commandInput.value = '';
                        }
                    }
                });
                
                // Clear terminal
                this.clearBtn.addEventListener('click', () => {
                    this.terminal.innerHTML = '';
                    this.addSystemMessage('📋 Терминал очищен');
                });
                
                // Focus on input when clicking anywhere
                document.addEventListener('click', () => {
                    this.commandInput.focus();
                });
                
                // Prevent form submission on Enter in username input
                this.usernameInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        this.commandInput.focus();
                    }
                });
            }
        }
        
        // Initialize the terminal when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new MultiplayerTerminal();
        });
    </script>
</body>
</html>
"""

async def handle_index(request):
    """Обработчик главной страницы"""
    return web.Response(text=HTML_INTERFACE, content_type='text/html')

async def handle_websocket(request):
    """Обработчик WebSocket соединений"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # Добавляем клиента
    clients.append(ws)
    global users_online
    users_online = len(clients)
    
    print(f"🔗 Новое подключение. Всего клиентов: {users_online}")
    
    # Отправляем текущее состояние новому клиенту
    current_dir = os.getcwd()
    await ws.send_json({
        'type': 'system',
        'content': f'Добро пожаловать! Подключено пользователей: {users_online}',
        'timestamp': datetime.now().isoformat()
    })
    
    await ws.send_json({
        'type': 'users_count',
        'count': users_online
    })
    
    await ws.send_json({
        'type': 'current_dir', 
        'dir': current_dir
    })
    
    # Отправляем историю команд
    for history_item in command_history[-50:]:
        await ws.send_json(history_item)
    
    # Уведомляем всех о новом пользователе
    system_message = {
        'type': 'system',
        'content': f'👤 Новый пользователь подключился. Онлайн: {users_online}',
        'timestamp': datetime.now().isoformat()
    }
    
    await broadcast(system_message)
    command_history.append(system_message)
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    
                    if data.get('type') == 'command':
                        command = data.get('content', '').strip()
                        username = data.get('username', 'anonymous')
                        
                        if command:
                            # Сохраняем команду
                            command_item = {
                                'type': 'command',
                                'content': command,
                                'username': username,
                                'timestamp': datetime.now().isoformat()
                            }
                            command_history.append(command_item)
                            
                            # Рассылаем команду всем
                            await broadcast(command_item)
                            
                            # Выполняем команду
                            try:
                                # Обработка команды cd
                                if command.startswith('cd '):
                                    new_dir = command[3:].strip()
                                    try:
                                        os.chdir(new_dir)
                                        current_dir = os.getcwd()
                                        output = f"📁 Текущая директория: {current_dir}"
                                    except Exception as e:
                                        output = f"❌ Ошибка cd: {str(e)}"
                                    
                                    # Отправляем обновленную директорию
                                    dir_update = {
                                        'type': 'current_dir',
                                        'dir': current_dir
                                    }
                                    await broadcast(dir_update)
                                    
                                else:
                                    # Выполняем обычную команду
                                    process = await asyncio.create_subprocess_shell(
                                        command,
                                        stdout=asyncio.subprocess.PIPE,
                                        stderr=asyncio.subprocess.STDOUT
                                    )
                                    
                                    stdout, _ = await process.communicate()
                                    output = stdout.decode('utf-8', errors='replace')
                                    
                                    if not output.strip():
                                        output = "✅ Команда выполнена"
                                    
                                    # Ограничиваем вывод
                                    if len(output) > 10000:
                                        output = output[:10000] + "\n... (вывод обрезан)"
                                
                                # Сохраняем и рассылаем вывод
                                output_item = {
                                    'type': 'output',
                                    'content': output,
                                    'username': username,
                                    'timestamp': datetime.now().isoformat()
                                }
                                command_history.append(output_item)
                                await broadcast(output_item)
                                
                            except Exception as e:
                                error_msg = {
                                    'type': 'error',
                                    'content': f'❌ Ошибка выполнения: {str(e)}',
                                    'timestamp': datetime.now().isoformat()
                                }
                                await broadcast(error_msg)
                                command_history.append(error_msg)
                                
                except json.JSONDecodeError:
                    error_msg = {
                        'type': 'error',
                        'content': '❌ Неверный формат сообщения',
                        'timestamp': datetime.now().isoformat()
                    }
                    await ws.send_json(error_msg)
                    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Удаляем клиента
        clients.remove(ws)
        users_online = len(clients)
        
        print(f"🔌 Отключение. Осталось клиентов: {users_online}")
        
        # Уведомляем об отключении
        system_message = {
            'type': 'system',
            'content': f'👤 Пользователь отключился. Онлайн: {users_online}',
            'timestamp': datetime.now().isoformat()
        }
        
        await broadcast(system_message)
        command_history.append(system_message)
        
        # Обновляем счетчик пользователей
        users_update = {
            'type': 'users_count',
            'count': users_online
        }
        await broadcast(users_update)
    
    return ws

async def broadcast(message):
    """Отправка сообщения всем подключенным клиентам"""
    if clients:
        for client in clients:
            try:
                await client.send_json(message)
            except:
                # Удаляем нерабочих клиентов
                try:
                    clients.remove(client)
                except:
                    pass

async def background_tasks(app):
    """Фоновые задачи"""
    asyncio.create_task(system_status_updater())

async def system_status_updater():
    """Периодическое обновление системной информации"""
    while True:
        try:
            if clients:
                # Отправляем текущую директорию
                current_dir = os.getcwd()
                dir_update = {
                    'type': 'current_dir',
                    'dir': current_dir
                }
                await broadcast(dir_update)
                
                # Отправляем количество пользователей
                users_update = {
                    'type': 'users_count', 
                    'count': len(clients)
                }
                await broadcast(users_update)
                
        except Exception as e:
            print(f"Error in system status updater: {e}")
        
        await asyncio.sleep(10)

def main():
    """Запуск сервера"""
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/ws', handle_websocket)
    
    # Запускаем фоновые задачи
    app.on_startup.append(background_tasks)
    
    port = int(os.environ.get("PORT", 5000))
    
    print("🚀 Multiplayer Terminal Server")
    print("=" * 50)
    print(f"🌐 Сервер запущен на порту: {port}")
    print(f"📡 WebSocket endpoint: ws://localhost:{port}/ws")
    print("🔗 Откройте в браузере: http://localhost:5000")
    print("👥 Мультиплеер: откройте в нескольких вкладках/устройствах")
    print("=" * 50)
    
    web.run_app(app, port=port, host='0.0.0.0')

if __name__ == '__main__':
    main()
