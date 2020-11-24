.EXPORT_ALL_VARIABLES:
SPARK_VERSION=3.0.0
SBT_OPTS=-Xmx16G -XX:+UseConcMarkSweepGC -XX:+CMSClassUnloadingEnabled -Xss2M -Duser.timezone=GMT

init:
	pip install -r requirements.txt

spark-interpreter:
	devscripts/sparkInterpreter.sh

spark-compile:
	cd scala;\
  sbt compile 

test:
	nosetests tests
