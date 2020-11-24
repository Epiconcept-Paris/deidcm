package org.kskit.scala 

import demy.mllib.linalg.implicits._
import demy.storage.{Storage, WriteMode, FSNode}
import demy.util.{log => l, util}
import demy.{Application, Configuration}
import org.apache.spark.sql.{SparkSession, Column, Dataset, Row, DataFrame}
import org.apache.spark.sql.types._
import org.apache.spark.sql.functions.{col, udf, input_file_name, explode, coalesce, when, lit, concat, struct, expr}
 
object Pacs {
  val twitterSplitter = "((http|https|HTTP|HTTPS|ftp|FTP)://(\\S)+|[^\\p{L}]|@+|#+|(?<!(^|[A-Z]))(?=[A-Z])|(?<!^)(?=[A-Z][a-z]))+|RT|via|vía"
  def main(args: Array[String]): Unit = {
    val cmd = Map(
      "getScu" -> Set("tweetPath", "geoPath", "pathFilter", "columns", "groupBy", "filterBy", "sortBy", "sourceExpressions", "langCodes", "langNames", "langPaths",  "parallelism")
    )
    if(args == null || args.size < 3 || !cmd.contains(args(0)) || args.size % 2 == 0 ) 
      l.msg(s"first argument must be within ${cmd.keys} and followed by a set of 'key' 'values' parameters, but the command ${args(0)} is followed by ${args.size -1} values")
    else {
      val command = args(0)
      val params = Seq.range(0, (args.size -1)/2).map(i => (args(i*2 + 1), args(i*2 + 2))).toMap
      if(!cmd(command).subsetOf(params.keySet))
        l.msg(s"Cannot run $command, expected named parameters are ${cmd(command)}")
      else if(command == "getScu") {
         //implicit val spark = JavaBridge.getSparkSession(params.get("parallelism").map(_.toInt).getOrElse(0)) 
         org.dcm4che3.tool.getscu.GetSCU.main(Array("-c", "DCM4CHEE@localhost:11112",  "-m", "StudyInstanceUID=1.3.6.1.4.1.9590.100.1.2.409914573611683067919391940392991059926", "--directory", "/tmp"))
      
      }
    }
  }
}

