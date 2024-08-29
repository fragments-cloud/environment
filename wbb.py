import time
import hashlib
import zlib
from cryptography.fernet import Fernet
from flask import Flask, request, jsonify

app = Flask(__name__)

class Bloco:
    def __init__(self, transacoes, bloco_anterior_hash):
        self.timestamp = time.time()
        self.transacoes = self.comprimir_e_criptografar(transacoes)
        self.bloco_anterior_hash = bloco_anterior_hash
        self.hash = self.gerar_hash()
        self.chave = Fernet.generate_key()  # Salva a chave para descriptografar mais tarde

    def comprimir_e_criptografar(self, transacoes):
        # Compressão
        dados_comprimidos = zlib.compress(transacoes.encode('utf-8'))
        
        # Criptografia
        fernet = Fernet(self.chave)
        dados_criptografados = fernet.encrypt(dados_comprimidos)
        
        return dados_criptografados

    def gerar_hash(self):
        dados = f"{self.timestamp}{self.transacoes}{self.bloco_anterior_hash}".encode('utf-8')
        return hashlib.sha256(dados).hexdigest()

    def descriptografar_e_descomprimir(self):
        fernet = Fernet(self.chave)
        dados_descriptografados = fernet.decrypt(self.transacoes)
        return zlib.decompress(dados_descriptografados).decode('utf-8')

class Blockchain:
    def __init__(self):
        self.cadeia = []
        self.transacoes_pendentes = []
        self.criar_bloco_genesis()

    def criar_bloco_genesis(self):
        bloco_genesis = Bloco("Bloco Genesis", "0")
        self.cadeia.append(bloco_genesis)

    def adicionar_transacao(self, transacao):
        self.transacoes_pendentes.append(transacao)

    def criar_novo_bloco(self):
        bloco_anterior_hash = self.cadeia[-1].hash
        transacoes_concatenadas = "".join(self.transacoes_pendentes)
        novo_bloco = Bloco(transacoes_concatenadas, bloco_anterior_hash)
        self.cadeia.append(novo_bloco)
        self.distribuir_para_peers(novo_bloco)
        self.transacoes_pendentes = []

    def distribuir_para_peers(self, bloco):
        print(f"Bloco com hash {bloco.hash} distribuído para os peers.")

    def consultar_bloco_por_hash(self, hash_bloco):
        for bloco in self.cadeia:
            if bloco.hash == hash_bloco:
                return bloco
        return None

    def buscar_transacoes(self, termo_busca):
        resultados = []
        for bloco in self.cadeia:
            transacoes = bloco.descriptografar_e_descomprimir()
            if termo_busca in transacoes:
                resultados.append({
                    'hash': bloco.hash,
                    'timestamp': bloco.timestamp,
                    'transacoes': transacoes
                })
        return resultados

blockchain = Blockchain()

@app.route('/transacao', methods=['POST'])
def receber_transacao():
    dados = request.json
    if not dados or 'transacao' not in dados:
        return jsonify({'erro': 'Transação inválida'}), 400

    transacao = dados['transacao']
    blockchain.adicionar_transacao(transacao)
    return jsonify({'mensagem': 'Transação recebida'}), 201

@app.route('/bloco/<hash_bloco>', methods=['GET'])
def consultar_bloco(hash_bloco):
    bloco = blockchain.consultar_bloco_por_hash(hash_bloco)
    if bloco:
        return jsonify({
            'hash': bloco.hash,
            'timestamp': bloco.timestamp,
            'transacoes': bloco.descriptografar_e_descomprimir()
        }), 200
    else:
        return jsonify({'erro': 'Bloco não encontrado'}), 404

@app.route('/buscar_transacoes', methods=['GET'])
def buscar_transacoes():
    termo_busca = request.args.get('termo')
    if not termo_busca:
        return jsonify({'erro': 'Parâmetro de busca ausente'}), 400

    resultados = blockchain.buscar_transacoes(termo_busca)
    return jsonify(resultados), 200

def iniciar_blockchain():
    while True:
        blockchain.criar_novo_bloco()
        time.sleep(1)

if __name__ == '__main__':
    from threading import Thread
    servidor_flask = Thread(target=lambda: app.run(port=5000))
    servidor_flask.start()

    iniciar_blockchain()
