from flask import Flask, jsonify, request
from models import db, Cliente, Vaga, Rua, Cidade
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:brenodias@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Para lidar com CORS
from flask_cors import CORS
CORS(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print('Register Request JSON:', data)
    new_cliente = Cliente(
        placadocarro=data['placadocarro'],
        cpf=data['cpf'],
        email=data['email'],
        senha=data['senha'],
        estado=data['estado'],
        cidade=data['cidade']
    )
    
    try:
        db.session.add(new_cliente)
        db.session.commit()
        response = {'message': 'Cliente registrado com sucesso!'}
        print('Register Response:', response)
        return jsonify(response), 201
    except Exception as e:
        error_response = {'message': 'Erro ao registrar cliente.', 'error': str(e)}
        print('Register Error:', error_response)
        return jsonify(error_response), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print('Login Request JSON:', data)
    
    email = data['email']
    senha = data['senha']
    
    print('Login Email:', email, 'Senha:', senha)
    
    cliente = Cliente.query.filter_by(email=email).first()
    if not cliente:
        return jsonify({'message': 'Email não encontrado no sistema.'}), 401
    
    if cliente.senha != senha:
        return jsonify({'message': 'Senha incorreta.'}), 401
    
    response = {'message': 'Login realizado com sucesso!', 'placaDoCarro': cliente.placadocarro}
    return jsonify(response)

@app.route('/active_spot', methods=['POST'])
def get_active_spot():
    data = request.get_json()
    placa_do_carro = data.get('placaDoCarro')
    if not placa_do_carro:
        return jsonify({'message': 'Placa do carro não fornecida.'}), 400

    current_time = datetime.now()

    # Consulta a vaga ativa do cliente com JOIN nas tabelas de Rua e Cidade
    active_spot = db.session.query(Vaga, Rua, Cidade).join(Rua, Vaga.idrua == Rua.id).join(Cidade, Rua.idcidade == Cidade.id).filter(
        Vaga.placadocarro == placa_do_carro,
        Vaga.horasaida > current_time,
        Vaga.expirada == False
    ).first()

    if active_spot:
        vaga, rua, cidade = active_spot
        response = {
            'horaEntrada': vaga.horaentrada.strftime('%Y-%m-%d %H:%M:%S'),
            'horaSaida': vaga.horasaida.strftime('%Y-%m-%d %H:%M:%S'),
            'cidade': cidade.nome,
            'rua': rua.nome
        }
        return jsonify(response), 200
    else:
        return jsonify({'message': 'Não há vaga ativa para o cliente'}), 404

@app.route('/all_spots', methods=['POST'])
def get_all_spots():
    data = request.get_json()
    placa_do_carro = data.get('placaDoCarro')
    if not placa_do_carro:
        return jsonify({'message': 'Placa do carro não fornecida.'}), 400

    # Consulta todas as vagas do cliente com JOIN nas tabelas de Rua e Cidade
    all_spots = db.session.query(Vaga, Rua, Cidade).join(Rua, Vaga.idrua == Rua.id).join(Cidade, Rua.idcidade == Cidade.id).filter(
        Vaga.placadocarro == placa_do_carro
    ).all()

    spots = []
    for vaga, rua, cidade in all_spots:
        spot_info = {
            'horaEntrada': vaga.horaentrada.strftime('%Y-%m-%d %H:%M:%S'),
            'horaSaida': vaga.horasaida.strftime('%Y-%m-%d %H:%M:%S'),
            'cidade': cidade.nome,
            'rua': rua.nome,
            'expirada': vaga.expirada
        }
        spots.append(spot_info)

    return jsonify(spots), 200

if __name__ == '__main__':
    app.run(debug=True)
