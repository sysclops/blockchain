.PHONY: conda-env clean-pyc clean-txt

HOST='0.0.0.0'
PORT=5000



conda-env:
	conda env create -f jacoin.yml


clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +


clean-txt:
	find . -name '*.txt' -exec rm --force {} +


node:
	python node.py -a $(HOST) -p $(PORT)
