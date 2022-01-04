.EXPORT_ALL_VARIABLES:
SHELL = bash
SPARK_VERSION=3.0.0
SBT_OPTS=-Xmx16G -XX:+UseConcMarkSweepGC -XX:+CMSClassUnloadingEnabled -Xss2M -Duser.timezone=GMT

init:
	if [ -f env ]; then\
	  rm -r env;\
	fi 
	python3 -m venv env;
	source env/bin/activate;
	python3 -m pip install --upgrade pip;
	python3 -m pip install --upgrade setuptools wheel twine

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
