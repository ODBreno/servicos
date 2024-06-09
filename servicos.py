from flask import Flask, jsonify, request
from models import db, Cliente, Vaga
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime

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
    print('Login Email:', email, 'Senha:', senha)
    
    cliente = Cliente.query.filter_by(email=email).first()
    print(cliente.email, cliente.senha)
    if not cliente:
        response = {'message': 'Email não encontrado no sistema.'}
        print('Login Response:', response)
        return jsonify(response), 401
    if senha != cliente.senha:
        response = {'message': 'Senha incorreta.'} 
        return jsonify(response), 401
    response = {'message': 'Login realizado com sucesso!', 'placaDoCarro': cliente.placadocarro}
    return jsonify(response)

@app.route('/active_spot', methods=['GET'])
def get_active_spot():
    try:
        placa_do_carro = request.args.get('placaDoCarro')  # Obtém a placa do carro do cliente do parâmetro da URL
        current_time = datetime.datetime.now()
        print('Placa do Carro:', placa_do_carro, 'Current Time:', current_time)
        # Consulta a vaga ativa do cliente
        active_spot = Vaga.query.filter(
            Vaga.PlacaDoCarro == placa_do_carro,
            Vaga.horaSaida > current_time,
            Vaga.Expirada == False
        ).first()

        if active_spot:
            # Se encontrou uma vaga ativa, retorna seus detalhes
            response = {
                'IDVaga': active_spot.IDVaga,
                'horaEntrada': active_spot.horaEntrada.strftime('%Y-%m-%d %H:%M:%S'),
                'horaSaida': active_spot.horaSaida.strftime('%Y-%m-%d %H:%M:%S')
            }
            return jsonify(response), 200
        else:
            # Se não encontrou uma vaga ativa, retorna uma mensagem indicando isso
            response = {'message': 'Não há vaga ativa para o cliente'}
            return jsonify(response), 404
    except Exception as e:
        # Em caso de erro, retorna uma mensagem de erro
        error_response = {'message': 'Erro ao buscar vaga ativa.', 'error': str(e)}
        return jsonify(error_response), 500

@app.route('/clientes', methods=['GET'])
def get_all_clientes():
    clientes = Cliente.query.all()
    output = []
    for cliente in clientes:
        cliente_data = {
            'id': cliente.id,
            'placadocarro': cliente.placadocarro,
            'cpf': cliente.cpf,
            'email': cliente.email,
            'estado': cliente.estado,
            'cidade': cliente.cidade
        }
        output.append(cliente_data)
    
    response = {'clientes': output}
    print('Clientes Response:', response)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
