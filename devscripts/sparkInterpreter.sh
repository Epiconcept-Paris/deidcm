#!/bin/bash
export SPARK_VERSION=3.0.0
export SBT_OPTS="-Xmx16G -XX:+UseConcMarkSweepGC -XX:+CMSClassUnloadingEnabled -Xss2M  -Duser.timezone=GMT"
cd scala
expect -c '
spawn sbt console
expect "scala>"
send "import org.apache.spark.sql.SparkSession\r"
send "import org.apache.spark.sql.functions._\r"
send "implicit val spark = SparkSession.builder().master(\"local\[*\]\").appName(\"test\").config(\"spark.sql.legacy.timeParserPolicy\",\"LEGACY\").getOrCreate()\r"
send "import spark.implicits._\r"
send "import demy.util.util\r"
send "spark.sparkContext.setLogLevel(\"WARN\")\r"
send "import org.ecdc.twitter._\r"
send "implicit val storage = demy.storage.Storage.getSparkStorage\r"
send "import demy.Configuration\r"
send "import demy.storage.Storage\r"
send "implicit val s = Storage.getLocalStorage\r"
interact'

cd ..
