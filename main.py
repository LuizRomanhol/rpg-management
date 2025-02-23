from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import uuid

app = Flask(__name__)
socketio = SocketIO(app)

# Armazenamento de sessões e jogadores (substitua por um banco de dados real, se necessário)
sessao_db = {}
jogadores_db = {}

# Função para pegar o jogador por ID
def get_jogador_por_id(jogador_id):
    return jogadores_db.get(jogador_id)

# Função para salvar o jogador
def save_jogador(jogador):
    jogadores_db[jogador['id']] = jogador

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/criar_sessao', methods=['POST'])
def criar_sessao():
    sessao_id = str(uuid.uuid4())  # Gerar um ID único para a sessão
    sessao_db[sessao_id] = {'nome': request.form['nome'], 'jogadores': []}
    return redirect(url_for('painel', sessao_id=sessao_id))

@app.route('/painel/<sessao_id>', methods=['GET', 'POST'])
def painel(sessao_id):
    sessao = sessao_db.get(sessao_id)
    if request.method == 'POST':
        jogador_id = str(uuid.uuid4())
        nome_jogador = request.form['nome']
        jogador = {'id': jogador_id, 'nome': nome_jogador, 'sessao_id': sessao_id}
        jogadores_db[jogador_id] = jogador
        sessao['jogadores'].append(jogador)
    return render_template('panel.html', sessao_id=sessao_id, sessao=sessao)

@app.route('/room/<sessao_id>/<jogador_id>')
def room(sessao_id, jogador_id):
    sessao = sessao_db.get(sessao_id)
    jogador = get_jogador_por_id(jogador_id)
    return render_template('room.html', sessao_id=sessao_id, jogador_id=jogador_id, nome_jogador=jogador['nome'])

@socketio.on('atualizar_nome')
def atualizar_nome(data):
    jogador_id = data['jogadorId']
    novo_nome = data['novoNome']

    # Atualizar nome no banco de dados
    jogador = get_jogador_por_id(jogador_id)
    jogador['nome'] = novo_nome
    save_jogador(jogador)

    # Emitir para todos os jogadores na sessão
    emit(f'atualizar_nome_jogador_{jogador["sessao_id"]}', {
        'jogadorId': jogador['id'],
        'novoNome': novo_nome
    }, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)

