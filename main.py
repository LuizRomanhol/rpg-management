from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import uuid

app = Flask(__name__, template_folder="templates")
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurações do broker MQTT
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883

# Cliente MQTT
mqtt_client = mqtt.Client()

# Dicionário para armazenar sessões ativas
sessoes = {}

# Conectar ao broker
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/criar_sessao", methods=["POST"])
def criar_sessao():
    nome = request.form.get("nome")

    if not nome:
        return jsonify({"erro": "Nome da sessão obrigatório"}), 400

    sessao_id = str(uuid.uuid4())[:8]  # Gera um ID curto
    topico = f"rpg/{sessao_id}"

    sessoes[sessao_id] = {"nome": nome, "topico": topico, "mestre": None, "jogadores": []}

    return redirect(url_for("painel_mestre", sessao_id=sessao_id))


@app.route("/room/<sessao_id>")
def visualizar_room(sessao_id):
    if sessao_id not in sessoes:
        return "Sessão não encontrada", 404

    return render_template("room.html", sessao_id=sessao_id, topico=sessoes[sessao_id]["topico"])


@app.route("/panel/<sessao_id>")
def painel_mestre(sessao_id):
    if sessao_id not in sessoes:
        return "Sessão não encontrada", 404

    link_jogadores = f"{request.host_url}room/{sessao_id}"
    return render_template("panel.html", sessao_id=sessao_id, topico=sessoes[sessao_id]["topico"], link_jogadores=link_jogadores)


@app.route("/atualizar_status/<sessao_id>", methods=["POST"])
def atualizar_status(sessao_id):
    if sessao_id not in sessoes:
        return jsonify({"erro": "Sessão não encontrada"}), 404

    dados = request.json
    topico = sessoes[sessao_id]["topico"]

    # Envia os dados para o tópico MQTT
    mqtt_client.publish(topico, str(dados))

    # Atualiza os clientes com a nova informação
    socketio.emit(f"update_status_{sessao_id}", dados)

    return jsonify({"mensagem": "Status atualizado"})


if __name__ == "__main__":
    socketio.run(app, debug=True)

