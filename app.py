import flask
import instancefunctions as ins
from flask import request,jsonify

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/api/v1/create_instance', methods=['POST'])
def create_instance():
	region = ins.get_variable('Region')
	client_name = request.args['client_name']
	fqdn = request.args['fqdn']
	try:
		return jsonify(ins.launch_instance(region,client_name,fqdn)), 200
	except Exception as e:
		return jsonify("Error has Occured: {}".format(e)), 400

@app.route('/api/v1/create_domain', methods=['POST'])
def create_fqdn():
	fqdn = request.args['fqdn']
	try:
		return jsonify(ins.create_domain(fqdn)), 200
	except Exception as e:
		return jsonify("Error has Occured: {}".format(e)), 400

@app.route('/api/v1/add_record', methods=['POST'])
def record_add():
	fqdn = request.args['fqdn']
	domain = request.args['domain']
	value = request.args['value']
	try:
		return jsonify(ins.add_record(fqdn,domain,value)), 200
	except Exception as e:
		return jsonify("Error has Occured: {}".format(e)), 400

@app.route('/api/v1/public_ipv4', methods=['GET'])
def public_ipv4():
	region = ins.get_variable('Region')
	fqdn = request.args['fqdn']
	try:
		return jsonify(ins.get_public_ip(region,fqdn)), 200
	except Exception as e:
		return jsonify("Error has Occured: {}".format(e)), 400

@app.route('/api/v1/nameservers', methods=['GET'])
def namerserver():
	fqdn = request.args['fqdn']
	try:
		return jsonify(ins.get_nameserver(fqdn)), 200
	except Exception as e:
		return jsonify("Error has Occured: {}".format(e)), 400


app.run('0.0.0.0')
