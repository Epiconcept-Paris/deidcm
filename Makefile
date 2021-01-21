.EXPORT_ALL_VARIABLES:
SHELL = bash
SPARK_VERSION=3.0.0
SBT_OPTS=-Xmx16G -XX:+UseConcMarkSweepGC -XX:+CMSClassUnloadingEnabled -Xss2M -Duser.timezone=GMT

init:
	python -m venv env;\
	source env/bin/activate;\
	pip install --upgrade pip;\
	pip install --upgrade setuptools wheel twine

install:
	source env/bin/activate;\
	pip install -e .;\

package:
	source env/bin/activate;\
	rm dist/*;\
	python setup.py sdist bdist_wheel

release-test:
	source env/bin/activate;\
	rm dist/*;\
	python setup.py sdist bdist_wheel;\
	python -m twine upload --repository testpypi dist/*

release:
	source env/bin/activate;\
	rm dist/*;\
	python setup.py sdist bdist_wheel;\
	python -m twine upload dist/*

check:
	source env/bin/activate;\
	rm dist/*;\
	python setup.py sdist bdist_wheel;\
	python -m twine check/*

test:
	nosetests tests
