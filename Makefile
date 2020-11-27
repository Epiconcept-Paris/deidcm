.EXPORT_ALL_VARIABLES:
SHELL = bash
SPARK_VERSION=3.0.0
SBT_OPTS=-Xmx16G -XX:+UseConcMarkSweepGC -XX:+CMSClassUnloadingEnabled -Xss2M -Duser.timezone=GMT

init:
	python3 -m venv env;\
	source env/bin/activate;\
	pip3 install --upgrade pip;\
	pip3 install --upgrade setuptools wheel twine

package:
	source env/bin/activate;\
	python3 setup.py sdist bdist_wheel

upload-test:
	source env/bin/activate;\
	python3 setup.py sdist bdist_wheel;\
	python3 -m twine upload --repository testpypi dist/*


spark-interpreter:
	devscripts/sparkInterpreter.sh

spark-compile:
	cd scala;\
  sbt compile 

test:
	nosetests tests
