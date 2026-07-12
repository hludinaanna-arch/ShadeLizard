from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Хранилище названий комнат
room_titles = {}

# Хранилище сообщений каждой комнаты
rooms_messages = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        room_id = uuid.uuid4().hex[:8]
        return redirect(url_for('chat_room', room_name=room_id))
    return render_template('chat.html')

@app.route('/create-room', methods=['POST'])
def create_room():
    data = request.get_json()
    title = data.get('title', 'Без названия')
    room_id = uuid.uuid4().hex[:8]
    room_titles[room_id] = title
    rooms_messages[room_id] = []
    return jsonify({'room_id': room_id, 'title': title})

@app.route('/chat/<room_name>')
def chat_room(room_name):
    return render_template('chat_room.html', room_name=room_name)

@app.route('/audio_call')
def audio_call():
    return render_template('audio_call.html')

@app.route('/call')
def call():
    return render_template('call.html')

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    is_reconnect = data.get('is_reconnect', False)
    
    join_room(room)
    
    if room not in rooms_messages:
        rooms_messages[room] = []
    
    for msg in rooms_messages[room]:
        emit('message', msg, room=room)
    
    if not is_reconnect:
        system_msg = {'username': 'Система', 'message': f'{username} присоединился к комнате'}
        rooms_messages[room].append(system_msg)
        emit('message', system_msg, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    system_msg = {'username': 'Система', 'message': f'{username} покинул комнату'}
    rooms_messages[room].append(system_msg)
    emit('message', system_msg, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    if room not in rooms_messages:
        rooms_messages[room] = []
    rooms_messages[room].append(data)
    emit('message', data, room=room)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
