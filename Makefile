deps:
	pip-compile --output-file requirements.txt requirements.in
	pip-compile --output-file requirements-dev.txt requirements-dev.in
	pip-sync requirements.txt requirements-dev.txt

format:
	black tests setup.py tg2fibery.py
	isort tests setup.py tg2fibery.py
