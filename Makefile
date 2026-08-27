.PHONY: install test benchmark web

install:
	python -m pip install -e '.[spreadsheets,web]'

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

benchmark:
	PYTHONPATH=src python tools/run_benchmark.py

web:
	bidcore-web --root .cortex --host 127.0.0.1 --port 7860
