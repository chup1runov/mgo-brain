.PHONY: install-dev test compile check run doctor backup

install-dev:
	python -m pip install -e '.[dev,analytics,hardware]'

compile:
	python -m compileall -q mgo_brain tests

test:
	pytest -q

check: compile test

run:
	mgo-brain

doctor:
	mgo-doctor

backup:
	mgo-backup
