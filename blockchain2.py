import hashlib
import json
from flask import Flask, jsonify, request
from uuid import uuid4
from urlparse import urlparse
import requests
import time
import urllib


class Blockchain(object):
	def __init__(self):
		self.chain = []
		self.current_transactions = []
		self.nodes = set()
		self.difficulty = 6
		self.blocktime = 10
		self.blockreward = 0.01
		self.last_time = time.time()
		# Creates the genesis block
		self.new_block(previous_hash=1, proof=100)

	def new_block(self, proof, previous_hash=None):
		"""
		Create a new Block in the Blockchain
		:param proof: <int> The proof given by the Proof of Work algorithm
		:param previous_hash: (Optional) <str> Hash of previous Block
		:return: <dict> New Block
		"""

		block = {
			'index': len(self.chain) + 1,
			'timestamp': time.time(),
			'transactions': self.current_transactions,
			'proof': proof,
			'previous_hash': previous_hash or self.hash(self.chain[-1]),
		}

		# Resets current list of transactions
		self.current_transactions = []

		self.chain.append(block)
		return block

	def new_transaction(self, sender, recipient, amount):
		"""
		Creates a new transaction to go into the next mined Block
		:param sender: <str> Address of the Sender
		:param recipient: <str> Address of the Recipient
		:param amount: <int> Amount
		:return: <int> The index of the Block that will hold this transaction
		"""

		self.current_transactions.append({
			'sender': sender,
			'recipient': recipient,
			'amount': amount,
		})

		return self.last_block['index'] + 1	 # Returns the index of the block which the transaction will be added to

	@staticmethod
	def hash(block):
		"""
		Creates a SHA-256 hash of a Block
		:param block: <dict> Block
		:return: <str>
		"""

		# Need make sure that the dict is in order, or we'll have inconsistent hashes :(
		block_string = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(block_string).hexdigest()

	@property
	def last_block(self):
		# Returns the last Block in the chain
		return self.chain[-1]

	def proof_of_work(self, last_block):
		"""
		Simple Proof of Work Algorithm:
		- Find a number p' such that hash(pp') contains leading 4 zeroes
		- Where p is the previous proof, and p' is the new proof

		:param last_block: <dict> last Block
		:return: <int>
		"""

		last_proof = last_block['proof']
		last_hash = self.hash(last_block)

		proof = 0
		while self.valid_proof(last_proof, proof, last_hash) is False:
			proof += 1

		return proof

	@staticmethod
	def valid_proof(last_proof, proof, last_hash):
		"""
		Validates the Proof: Does hash(last_proof, proof) (contains 4 leading zeroes)
		:param last_proof: <int> Previous Proof
		:param proof: <int> Current Proof
		:param last_hash: <str> Hash of previous Block
		:return: <bool> True if correct, False if not.
		"""
		mid_string = str(last_proof) + str(proof) + str(last_hash)
		guess = mid_string.encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		return guess_hash[:4] == "0000"

	def register_node(self, address):
		"""
		Add a new node to the list of nodes
		:param address: Address of node. Eg. 'http://192.168.0.5:5000'
		"""

		parsed_url = urlparse(address) # scheme://netloc/path;parameters?query#fragment00
		if parsed_url.netloc:
			self.nodes.add(parsed_url.netloc)
		elif parsed_url.path:
			# Accepts an URL without scheme like '192.168.0.5:5000'.
			self.nodes.add(parsed_url.path)
		else:
			raise ValueError('Invalid URL')

	def valid_chain(self, chain):
		"""
		Responsible for checking if a chain is valid by looping through each block and verifying both the hash and the proof.

		Determine if a given blockchain is valid
		:param chain: <list> A blockchain
		:return: <bool> True if valid, False if not
		"""

		last_block = chain[0]
		current_index = 1

		while current_index < len(chain):
			block = chain[current_index]
			# Check that the hash of the block is correct
			t = self.hash(last_block)
			if block['previous_hash'] != t:
				print("here " + current_index)
				return False

			x = self.valid_proof(last_block['proof'], block['proof'], block['previous_hash'])

			# Check that the Proof of Work is correct
			if not x:
				print("here2 " + current_index)
				return False

			last_block = block
			current_index += 1

		return True

	def resolve_conflicts(self):
		"""
		Consensus Algorithm, it resolves conflicts by replacing our chain with the longest one in the network.
		Loops through all our neighbouring nodes, downloads their chains and verifies them using the above method.
		If a valid chain is found, whose length is greater than ours, we replace ours.

		:return: <bool> True if our chain was replaced, False if not
		"""

		neighbours = self.nodes
		new_chain = None

		# We're only looking for chains longer than ours
		max_length = len(self.chain)

		# Grab and verify the chains from all the nodes in our network
		for node in neighbours:
			y = urllib.request.urlopen('http://'+node+'/chain').read()
			my_json = y.decode('utf8').replace("'", '"')
			data = json.loads(my_json)
			response = json.dumps(data)
			length = data['length']
			chain = data['chain']

			print str(length) + "  " + str(max_length)

			# Check if the length is longer and the chain is valid
			if length > max_length and self.valid_chain(chain) and length == len(chain):
				max_length = length
				new_chain = chain

			# Replace our chain if we discovered a new, valid chain longer than ours
			if new_chain:
				self.chain = new_chain
				return True

		return False


def getworkt(self):
	last_block = blockchain.last_block
	last_id = len(self.chain)+1
	last_proof = last_block['proof']
	last_hash = self.hash(last_block)
	self.last_time = time.time()
	return last_id, last_hash, last_proof


# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route("/")
def hello():
	return "Blockchaining :)"


@app.route('/mine', methods=['GET'])
def mine():
	# Run the proof of work algorithm to get the next proof...
	last_block = blockchain.last_block
	proof = blockchain.proof_of_work(last_block)

	# Sender is "0" to signify that this node has mined a new coin.
	blockchain.new_transaction(
		sender="0",
		recipient=node_identifier,
		amount=blockchain.blockreward,
	)

	# Forge the new Block by adding it to the chain
	previous_hash = blockchain.hash(last_block)
	block = blockchain.new_block(proof, previous_hash)

	response = {
		'message': "New Block Forged",
		'index': block['index'],
		'transactions': block['transactions'],
		'proof': block['proof'],
		'previous_hash': block['previous_hash'],
	}
	return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
	values = request.get_json()

	# Check that the required fields are in the POST'ed data
	required = ['sender', 'recipient', 'amount']

	if not all(k in values for k in required):
		return 'Missing values', 400

	# Create a new Transaction
	index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

	response = {'message': 'Transaction will be added to Block ' + str(index)}
	return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
	response = {
		'chain': blockchain.chain,
		'length': len(blockchain.chain),
	}
	return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def full_nodes():
	nodes = [item for item in blockchain.nodes]
	response = {
		'nodes': nodes,
		'length': len(nodes),
	}
	return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
	values = request.get_json()

	nodes = values.get('nodes')
	if nodes is None:
		return "Error: Please supply a valid list of nodes", 400

	for node in nodes:
		blockchain.register_node(node)

	response = {
		'message': 'New nodes have been added',
		'total_nodes': list(blockchain.nodes),
	}
	return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
	replaced = blockchain.resolve_conflicts

	if replaced:
		response = {
			'message': 'Our chain was replaced',
			'new_chain': blockchain.chain
		}
	else:
		response = {
			'message': 'Our chain is authoritative',
			'chain': blockchain.chain
		}

	return jsonify(response), 200


@app.route('/getwork', methods=['GET'])
def getwork():
	r = blockchain.getworkt()
	response = {
		'lastindex': r[0],
		'lasthash': r[1],
		'lastproof': r[2]
	}

	return jsonify(response), 200


@app.route('/getwork/difficulty', methods=['GET'])
def getDiff():
	response = {
		'difficulty': blockchain.difficulty,
		'blockTime':blockchain.blocktime
	}
	return jsonify(response), 200


@app.route('/setdiff', methods=['POST'])
def setDiff():
	values = request.get_json()
	required = ['diff']
	if not all(k in values for k in required):
		return 'Missing values', 400
	blockchain.difficulty = values['diff']
	response = {
		'Message': "Difficulty set to " + str(values['diff'])
	}
	return jsonify(response), 200


@app.route('/submitwork', methods=['POST'])
def submit():
	values = request.get_json()
	last_block = blockchain.last_block
	# Checks that the required fields are in the POST'ed data
	required = ['index', 'proof', 'address']
	if not all(k in values for k in required):
		return 'Missing values', 400

	response = {}
	# Forges the new Block by adding it to the chain
	if values['index'] == len(blockchain.chain):
		previous_hash = blockchain.hash(last_block)
		block = blockchain.new_block(values['proof'], previous_hash)
		blockchain.new_transaction(
			sender="0",
			recipient=values['address'],
			amount=blockchain.blockreward,
		)
		response = {
			'message': "New Block Forged",
			'index': block['index'],
			'transactions': block['transactions'],
			'proof': block['proof'],
			'previous_hash': block['previous_hash'],
		}

	return jsonify(response), 200


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5001)