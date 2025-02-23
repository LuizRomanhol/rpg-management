from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import uuid

app = Flask(__name__)
socketio = SocketIO(app)

# Armazenamento de sessões e jogadores
sessao_db = {}
jogadores_db = {}

def get_jogador_por_id(jogador_id):
    return jogadores_db.get(jogador_id)

def save_jogador(jogador):
    jogadores_db[jogador['id']] = jogador

def remove_jogador(jogador_id):
    if jogador_id in jogadores_db:
        del jogadores_db[jogador_id]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/criar_sessao', methods=['POST'])
def criar_sessao():
    sessao_id = str(uuid.uuid4())
    sessao_db[sessao_id] = {'nome': request.form['nome'], 'jogadores': []}
    return redirect(url_for('painel', sessao_id=sessao_id))

@app.route('/painel/<sessao_id>', methods=['GET', 'POST'])
def painel(sessao_id):
    sessao = sessao_db.get(sessao_id)
    if request.method == 'POST':
        jogador_id = str(uuid.uuid4())
        nome_jogador = request.form['nome']
        jogador = {
            'id': jogador_id,
            'nome': nome_jogador,
            'sessao_id': sessao_id,
            'localizacao': '',
            'hp': 100,
            'hp_max': 100
        }
        jogadores_db[jogador_id] = jogador
        sessao['jogadores'].append(jogador)
    return render_template('panel.html', sessao_id=sessao_id, sessao=sessao)

@app.route('/room/<sessao_id>/<jogador_id>')
def room(sessao_id, jogador_id):
    sessao = sessao_db.get(sessao_id)
    jogador = get_jogador_por_id(jogador_id)
    return render_template('room.html', sessao_id=sessao_id, jogador_id=jogador_id, jogador=jogador, sessao=sessao)

# Handler para atualizar informações gerais do jogador (nome, localização, HP e HP máximo)
@socketio.on('atualizar_jogador')
def atualizar_jogador(data):
    jogador_id = data['jogadorId']
    novo_nome = data['novoNome']
    nova_localizacao = data['novaLocalizacao']
    novo_hp = data['novoHp']
    novo_hp_max = data['novoHpMax']
    
    jogador = get_jogador_por_id(jogador_id)
    if jogador:
        jogador['nome'] = novo_nome
        jogador['localizacao'] = nova_localizacao
        jogador['hp'] = novo_hp
        jogador['hp_max'] = novo_hp_max
        save_jogador(jogador)
        emit(f'atualizar_jogador_{jogador["sessao_id"]}', {
            'jogadorId': jogador['id'],
            'novoNome': novo_nome,
            'novaLocalizacao': nova_localizacao,
            'novoHp': novo_hp,
            'novoHpMax': novo_hp_max
        }, broadcast=True)

# Handler para remover jogador
@socketio.on('remover_jogador')
def remover_jogador_event(data):
    jogador_id = data['jogadorId']
    sessao_id = data['sessaoId']
    remove_jogador(jogador_id)
    sessao = sessao_db.get(sessao_id)
    sessao['jogadores'] = [j for j in sessao['jogadores'] if j['id'] != jogador_id]
    emit(f'atualizar_jogador_{sessao_id}', {'jogadorId': jogador_id}, broadcast=True)

# Handler para lançamento de dados
@socketio.on('lançar_dado')
def lancar_dado(data):
    resultado = data['resultado']
    jogador_id = data['jogadorId']
    dado = data['dado']
    sessao_id = data['sessaoId']
    
    nome_jogador = data.get('nome')
    if not nome_jogador:
        jogador = get_jogador_por_id(jogador_id)
        nome_jogador = jogador['nome'] if jogador else jogador_id

    emit(f'evento_lancamento_dado_{sessao_id}', {
        'jogadorId': jogador_id,
        'nome': nome_jogador,
        'dado': dado,
        'resultado': resultado
    }, broadcast=True)

# Handler para novo evento de dano
@socketio.on('new_damage')
def new_damage(data):
    jogador_id = data['jogadorId']
    dano = data['dano']
    sessao_id = data['sessaoId']
    
    jogador = get_jogador_por_id(jogador_id)
    nome_jogador = jogador['nome'] if jogador else jogador_id
    mensagem = f"{nome_jogador} levou {dano} pontos de dano!"
    emit(f'evento_hp_atualizado_{sessao_id}', {
        'mensagem': mensagem
    }, broadcast=True)

# Handler para novo evento de cura
@socketio.on('new_heal')
def new_heal(data):
    jogador_id = data['jogadorId']
    heal = data['heal']
    sessao_id = data['sessaoId']
    
    jogador = get_jogador_por_id(jogador_id)
    nome_jogador = jogador['nome'] if jogador else jogador_id
    mensagem = f"{nome_jogador} recuperou {heal} pontos de vida!"
    emit(f'evento_hp_atualizado_{sessao_id}', {
        'mensagem': mensagem
    }, broadcast=True)

@socketio.on('change_location')
def new_heal(data):
    jogador_id = data['jogadorId']
    localizacao = data['novaLocalizacao']
    sessao_id = data['sessaoId']
    
    jogador = get_jogador_por_id(jogador_id)
    nome_jogador = jogador['nome'] if jogador else jogador_id
    mensagem = f"{nome_jogador} chegou em {localizacao}"
    emit(f'evento_localizacao_atualizado_{sessao_id}', {
        'mensagem': mensagem
    }, broadcast=True)
    
if __name__ == '__main__':
    socketio.run(app, debug=True)

