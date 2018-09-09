package com.undergroundquizscene.clairvoyage

import cats.effect.IO
import io.circe._
import io.circe.generic.auto._
import io.circe.parser._
import io.circe.syntax._
import org.http4s._
import org.http4s.circe._
import org.http4s.client.blaze._
import org.http4s.dsl.io._

import com.undergroundquizscene.clairvoyage.model._

object Main extends App {
        val client = Http1Client[IO]().unsafeRunSync
        val churchCrossWest = DUID("7338653551721429731")
        println("Test data:")
        println(testStopData.unsafeRunSync)

        val data = stopData(churchCrossWest)
        println("Real data:")
        println(data.unsafeRunSync)

        def getStops: IO[Json] = for {
                stops <- client.expect[String]("http://buseireann.ie/inc/proto/bus_stop_points.php")
                json <- IO.fromEither(parse(stripVarDeclaration(stops)))
        } yield json

        def stopData(stop: DUID): IO[StopPassage.Response] = for {
                uri <- IO.fromEither(Uri.fromString("http://buseireann.ie/inc/proto/stopPassageTdi.php"))
                json <- client.expect[StopPassage.Response](uri.withQueryParam("stop_point", stop.value))
        } yield json

        def testStopData: IO[StopPassage.Response] = IO.fromEither(for {
                testJson <- parse(scala.io.Source.fromFile("src/main/resources/example-responses/stopPassage.json").mkString)
                testResponse <- testJson.as[StopPassage.Response]
        } yield testResponse)

        def stripVarDeclaration(javascript: String): String = javascript.dropWhile(_ != '{').dropRight(1)
}
