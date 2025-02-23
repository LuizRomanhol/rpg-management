from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import uuid

app = Flask(__name__)
socketio = SocketIO(app)

# Armazenamento de sessões e jogadores
sessao_db = {}
jogadores_db = {}

# Função para pegar o jogador por ID
def get_jogador_por_id(jogador_id):
    return jogadores_db.get(jogador_id)

# Função para salvar o jogador
def save_jogador(jogador):
    jogadores_db[jogador['id']] = jogador

# Função para remover jogador
def remove_jogador(jogador_id):
    if jogador_id in jogadores_db:
        del jogadores_db[jogador_id]

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
        jogador = {'id': jogador_id, 'nome': nome_jogador, 'sessao_id': sessao_id, 
                   'localizacao': '', 'hp': 100, 'hp_max': 100}
        jogadores_db[jogador_id] = jogador
        sessao['jogadores'].append(jogador)
    return render_template('panel.html', sessao_id=sessao_id, sessao=sessao)

@app.route('/room/<sessao_id>/<jogador_id>')
def room(sessao_id, jogador_id):
    sessao = sessao_db.get(sessao_id)
    jogador = get_jogador_por_id(jogador_id)
    return render_template('room.html', sessao_id=sessao_id, jogador_id=jogador_id, jogador=jogador)

@socketio.on('atualizar_jogador')
def atualizar_jogador(data):
    jogador_id = data['jogadorId']
    novo_nome = data['novoNome']
    nova_localizacao = data['novaLocalizacao']
    novo_hp = data['novoHp']
    novo_hp_max = data['novoHpMax']

    # Atualizar jogador no banco de dados
    jogador = get_jogador_por_id(jogador_id)
    jogador['nome'] = novo_nome
    jogador['localizacao'] = nova_localizacao
    jogador['hp'] = novo_hp
    jogador['hp_max'] = novo_hp_max
    save_jogador(jogador)

    # Emitir para todos os jogadores na sessão
    emit(f'atualizar_jogador_{jogador["sessao_id"]}', {
        'jogadorId': jogador['id'],
        'novoNome': novo_nome,
        'novaLocalizacao': nova_localizacao,
        'novoHp': novo_hp,
        'novoHpMax': novo_hp_max
    }, broadcast=True)

@socketio.on('remover_jogador')
def remover_jogador(data):
    jogador_id = data['jogadorId']
    remove_jogador(jogador_id)

    # Emitir para todos os jogadores na sessão para atualizar a lista
    emit(f'remover_jogador_{data["sessaoId"]}', {'jogadorId': jogador_id}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)

