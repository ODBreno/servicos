from flask import Flask, jsonify, request
from models import db, Cliente, Vaga
from werkzeug.security import check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:brenodias@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '987654321'

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
    placa_do_carro = data.get('placaDoCarro')  # Pegando a placa do carro do corpo da requisição
    
    print('Login Email:', email, 'Senha:', senha)
    
    cliente = Cliente.query.filter_by(email=email).first()
    if not cliente:
        return jsonify({'message': 'Email não encontrado no sistema.'}), 401
    
    if cliente.senha!=senha:
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

    # Consulta a vaga ativa do cliente
    active_spot = Vaga.query.filter(
        Vaga.placadocarro == placa_do_carro,
        Vaga.horasaida > current_time,
        Vaga.expirada == False
    ).first()

    if active_spot:
        response = {
            'IDVaga': active_spot.idvaga,
            'horaEntrada': active_spot.horaentrada.strftime('%Y-%m-%d %H:%M:%S'),
            'horaSaida': active_spot.horasaida.strftime('%Y-%m-%d %H:%M:%S')
        }
        return jsonify(response), 200
    else:
        return jsonify({'message': 'Não há vaga ativa para o cliente'}), 404

if __name__ == '__main__':
    app.run(debug=True)