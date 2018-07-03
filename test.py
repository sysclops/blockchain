from flask import Flask, jsonify, request

def numasd():
	if True:
		num = 123
	else:
		num = 44
	print jsonify(num),200