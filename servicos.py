from flask import Flask, jsonify, request
from models import db, Cliente
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:postgres@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '987654321'

db.init_app(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    hashed_password = generate_password_hash(data['senha'], method='sha256')
    new_cliente = Cliente(
        placa_do_carro=data['placa_do_carro'],
        cpf=data['cpf'],
        email=data['email'],
        senha=hashed_password,
        estado=data['estado'],
        cidade=data['cidade']
    )
    
    try:
        db.session.add(new_cliente)
        db.session.commit()
        return jsonify({'message': 'Cliente registrado com sucesso!'}), 201
    except Exception as e:
        return jsonify({'message': 'Erro ao registrar cliente.', 'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    senha = data['senha']

    cliente = Cliente.query.filter_by(email=email).first()

    if not cliente or not check_password_hash(cliente.senha, senha):
        return jsonify({'message': 'Login ou senha incorretos!'}), 401

    token = jwt.encode({
        'id': cliente.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'])

    return jsonify({'token': token})

@app.route('/clientes', methods=['GET'])
def get_all_clientes():
    clientes = Cliente.query.all()
    output = []
    for cliente in clientes:
        cliente_data = {
            'id': cliente.id,
            'placa_do_carro': cliente.placa_do_carro,
            'cpf': cliente.cpf,
            'email': cliente.email,
            'estado': cliente.estado,
            'cidade': cliente.cidade
        }
        output.append(cliente_data)
    
    return jsonify({'clientes': output})

if __name__ == '__main__':
    app.run(debug=True)
