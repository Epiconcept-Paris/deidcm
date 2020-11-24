lazy val sparkVersion = if(System.getenv("SPARK_VERSION")==null) "2.3.2" else System.getenv("SPARK_VERSION")
lazy val root = (project in file("."))
  .settings(
    name := "ecdc-twitter-bundle",
    scalaVersion := "2.12.12",
    retrieveManaged := true,
    version := "1.0",
    libraryDependencies += "org.apache.spark" %% "spark-core" % sparkVersion,
    libraryDependencies += "org.apache.spark" %% "spark-sql" % sparkVersion, 
    libraryDependencies += "org.apache.spark" %% "spark-mllib" % sparkVersion,
    libraryDependencies += "org.scalactic" %% "scalactic" % "3.0.5",
    libraryDependencies += "org.scalatest" %% "scalatest" % "3.0.5" % "test",
    libraryDependencies += "com.github.fommil.netlib" % "all" % "1.1.2" pomOnly(),
    libraryDependencies += "org.apache.httpcomponents" % "httpmime" % "4.5.6" ,
    libraryDependencies += "org.dcm4che.tool" % "dcm4che-tool-getscu" % "5.22.6",
    scalacOptions ++= Seq("-deprecation", "-feature"),
    assemblyMergeStrategy in assembly := {
      case PathList("org","aopalliance", xs @ _*) => MergeStrategy.last
      case PathList("javax", "inject", xs @ _*) => MergeStrategy.last
      case PathList("javax", "servlet", xs @ _*) => MergeStrategy.last
      case PathList("javax", "activation", xs @ _*) => MergeStrategy.last
      case PathList("javax", "xml", xs @ _*) => MergeStrategy.last
      case PathList("javax", "ws", xs @ _*) => MergeStrategy.last
      case PathList("org", "zuinnote", xs @ _*) => MergeStrategy.last
      case PathList("schemaorg_apache_xmlbeans", "system", xs @ _*) => MergeStrategy.last
      case PathList("org", "apache", xs @ _*) => MergeStrategy.last
      case PathList("com", "google", xs @ _*) => MergeStrategy.last
      case PathList("com", "esotericsoftware", xs @ _*) => MergeStrategy.last
      case PathList("com", "codahale", xs @ _*) => MergeStrategy.last
      case PathList("com", "yammer", xs @ _*) => MergeStrategy.last
      case PathList("org", "w3c", xs @ _*) => MergeStrategy.last
      case PathList("org", "w3", xs @ _*) => MergeStrategy.last
      case PathList("org", "slf4j", xs @ _*) => MergeStrategy.last
      case PathList("org", "openxmlformats", xs @ _*) => MergeStrategy.last
      case PathList("org", "etsi", xs @ _*) => MergeStrategy.last
      case PathList("org", "codehaus", xs @ _*) => MergeStrategy.last
      case PathList("org", "bouncycastle", xs @ _*) => MergeStrategy.last
      case PathList("com", "microsoft", xs @ _*) => MergeStrategy.last
      case PathList("com", "sun", xs @ _*) => MergeStrategy.last
      case PathList("com", "ctc", xs @ _*) => MergeStrategy.last
      case PathList("com", "graphbuilder", xs @ _*) => MergeStrategy.last
      case "about.html" => MergeStrategy.rename
      case "overview.html" => MergeStrategy.rename
      case "META-INF/ECLIPSEF.RSA" => MergeStrategy.last
      case "META-INF/mailcap" => MergeStrategy.last
      case "META-INF/mimetypes.default" => MergeStrategy.last
      case "plugin.properties" => MergeStrategy.last
      case "log4j.properties" => MergeStrategy.last
      case "git.properties" => MergeStrategy.last
      case x =>
        val oldStrategy = (assemblyMergeStrategy in assembly).value
        oldStrategy(x)
    }
  )
