from flask import Flask, jsonify, request
from models import db, Cliente, Vaga, Rua, Cidade, Fiscal
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:123@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Para lidar com CORS
from flask_cors import CORS
CORS(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
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
        return jsonify({'message': 'Cliente registrado com sucesso!'}), 201
    except Exception as e:
        return jsonify({'message': 'Erro ao registrar cliente.', 'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    senha = data['senha']
    
    cliente = Cliente.query.filter_by(email=email).first()
    if not cliente:
        return jsonify({'message': 'Email não encontrado no sistema.'}), 401
    
    if cliente.senha != senha:
        return jsonify({'message': 'Senha incorreta.'}), 401
    
    return jsonify({'message': 'Login realizado com sucesso!', 'placaDoCarro': cliente.placadocarro})

@app.route('/login_fiscal', methods=['POST'])
def login_fiscal():
    data = request.get_json()
    cpf = data['cpf']
    senha = data['senha']
    
    fiscal = Fiscal.query.filter_by(cpf=cpf).first()
    if not fiscal:
        return jsonify({'message': 'CPF não encontrado no sistema.'}), 401
    
    if fiscal.senha != senha:
        return jsonify({'message': 'Senha incorreta.'}), 401
    
    return jsonify({'message': 'Login realizado com sucesso!', 'cpf': fiscal.cpf})

@app.route('/active_spot', methods=['POST'])
def get_active_spot():
    data = request.get_json()
    placa_do_carro = data.get('placaDoCarro')
    if not placa_do_carro:
        return jsonify({'message': 'Placa do carro não fornecida.'}), 400

    current_time = datetime.now()

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


@app.route('/add_time_to_spot', methods=['POST'])
def add_time_to_spot():
    data = request.get_json()
    placa_do_carro = data.get('placaDoCarro')
    new_time = data.get('tempo')

    if not placa_do_carro or not new_time:
        return jsonify({'message': 'Dados incompletos fornecidos.'}), 400

    # Consulta a vaga ativa do cliente
    current_time = datetime.now()
    active_spot = Vaga.query.filter(
        Vaga.placadocarro == placa_do_carro,
        Vaga.horasaida > current_time,
        Vaga.expirada == False
    ).first()

    if not active_spot:
        return jsonify({'message': 'Não há vaga ativa para o cliente.'}), 404

    # Adiciona o novo tempo à vaga
    active_spot.horasaida += timedelta(hours=int(new_time))
    db.session.commit()

    response = {'message': 'Tempo adicionado à vaga com sucesso!'}
    return jsonify(response), 200

@app.route('/buy_spot', methods=['POST'])
def buy_spot():
    data = request.get_json()
    placa_do_carro = data.get('placaDoCarro')
    cidade = data.get('cidade')
    rua = data.get('rua')
    tempo = data.get('tempo')

    if not placa_do_carro or not cidade or not rua or not tempo:
        return jsonify({'message': 'Dados incompletos fornecidos.'}), 400

    cidade_obj = Cidade.query.filter_by(nome=cidade).first()
    if not cidade_obj:
        return jsonify({'message': 'Cidade não encontrada.'}), 404

    rua_obj = Rua.query.filter_by(nome=rua, idcidade=cidade_obj.id).first()
    if not rua_obj:
        return jsonify({'message': 'Rua não encontrada.'}), 404

    hora_entrada = datetime.now()
    hora_saida = hora_entrada + timedelta(hours=int(tempo))

    new_spot = Vaga(
        placadocarro=placa_do_carro,
        idrua=rua_obj.id,
        horaentrada=hora_entrada,
        horasaida=hora_saida,
        expirada=False
    )

    try:
        db.session.add(new_spot)
        db.session.commit()
        return jsonify({'message': 'Vaga comprada com sucesso!'}), 201
    except Exception as e:
        return jsonify({'message': 'Erro ao comprar vaga.', 'error': str(e)}), 500

@app.route('/expire_spot', methods=['POST'])
def expire_spot():
    data = request.get_json()
    placa_do_carro = data.get('placaDoCarro')

    if not placa_do_carro:
        return jsonify({'message': 'Dados incompletos fornecidos.'}), 400

    current_time = datetime.now()
    active_spot = Vaga.query.filter(
        Vaga.placadocarro == placa_do_carro,
        Vaga.horasaida > current_time,
        Vaga.expirada == False
    ).first()

    if not active_spot:
        return jsonify({'message': 'Não há vaga ativa para o cliente.'}), 404

    active_spot.expirada = True
    db.session.commit()

    return jsonify({'message': 'Vaga expirada com sucesso!'}), 200

@app.route('/all_cities', methods=['GET'])
def get_all_cities():
    cities = Cidade.query.all()
    cities_list = [city.nome for city in cities]
    return jsonify(cities_list), 200

@app.route('/all_streets', methods=['POST'])
def get_all_streets():
    data = request.get_json()
    city = data.get('cidade')
    if not city:
        return jsonify({'message': 'Cidade não fornecida.'}), 400

    city_obj = Cidade.query.filter_by(nome=city).first()
    if not city_obj:
        return jsonify({'message': 'Cidade não encontrada.'}), 404

    streets = Rua.query.filter_by(idcidade=city_obj.id).all()
    streets_list = [street.nome for street in streets]
    return jsonify(streets_list), 200

@app.route('/all_expired_spots_per_street', methods=['POST'])
def get_all_expired_spots_per_street():
    data = request.get_json()
    city = data.get('cidade')
    street = data.get('rua')
    if not city or not street:
        return jsonify({'message': 'Cidade ou rua não fornecida.'}), 400

    city_obj = Cidade.query.filter_by(nome=city).first()
    if not city_obj:
        return jsonify({'message': 'Cidade não encontrada.'}), 404

    street_obj = Rua.query.filter_by(nome=street, idcidade=city_obj.id).first()
    if not street_obj:
        return jsonify({'message': 'Rua não encontrada.'}), 404

    current_time = datetime.now()

    expired_spots = Vaga.query.filter(
        Vaga.idrua == street_obj.id,
        Vaga.expirada == True
    ).all()

    spots = []
    for spot in expired_spots:
        spot_info = {
            'placaDoCarro': spot.placadocarro,
            'horaEntrada': spot.horaentrada.strftime('%Y-%m-%d %H:%M:%S'),
            'horaSaida': spot.horasaida.strftime('%Y-%m-%d %H:%M:%S')
        }
        spots.append(spot_info)

    return jsonify(spots), 200

@app.route('/all_active_spots_per_street', methods=['POST'])
def get_all_active_spots_per_street():
    data = request.get_json()
    city = data.get('cidade')
    street = data.get('rua')
    if not city or not street:
        return jsonify({'message': 'Cidade ou rua não fornecida.'}), 400

    city_obj = Cidade.query.filter_by(nome=city).first()
    if not city_obj:
        return jsonify({'message': 'Cidade não encontrada.'}), 404

    street_obj = Rua.query.filter_by(nome=street, idcidade=city_obj.id).first()
    if not street_obj:
        return jsonify({'message': 'Rua não encontrada.'}), 404

    current_time = datetime.now()

    active_spots = Vaga.query.filter(
        Vaga.idrua == street_obj.id,
        Vaga.horasaida > current_time,
        Vaga.expirada == False
    ).all()

    spots = []
    for spot in active_spots:
        spot_info = {
            'placaDoCarro': spot.placadocarro,
            'horaEntrada': spot.horaentrada.strftime('%Y-%m-%d %H:%M:%S'),
            'horaSaida': spot.horasaida.strftime('%Y-%m-%d %H:%M:%S')
        }
        spots.append(spot_info)

    return jsonify(spots), 200

@app.route('/fiscal_info', methods=['POST'])
def get_fiscal_info():
    data = request.get_json()
    cpf = data.get('cpf')
    
    if not cpf:
        return jsonify({'message': 'CPF não fornecido.'}), 400
    
    fiscal = Fiscal.query.filter_by(cpf=cpf).first()
    if fiscal:
        fiscal_info = {
            'cpf': fiscal.cpf,
            'email': fiscal.email,
            'cidade': fiscal.cidade,
            'estado': fiscal.estado
        }
        return jsonify(fiscal_info), 200

    return jsonify({'message': 'CPF não encontrado no sistema.'}), 404

@app.route('/cliente_info', methods=['POST'])
def get_cliente_info():
    data = request.get_json()
    placadocarro = data.get('placadocarro')
    
    if not placadocarro:
        return jsonify({'message': 'Placa do carro não fornecida.'}), 400
    
    cliente = Cliente.query.filter_by(placadocarro=placadocarro).first()
    if cliente:
        cliente_info = {
            'cpf': cliente.cpf,
            'placaDoCarro': cliente.placadocarro,
            'email': cliente.email,
            'estado': cliente.estado,
            'cidade': cliente.cidade
        }
        return jsonify(cliente_info), 200

    return jsonify({'message': 'CPF não encontrado no sistema.'}), 404
   
if __name__ == '_main_':
    app.run(debug=True)