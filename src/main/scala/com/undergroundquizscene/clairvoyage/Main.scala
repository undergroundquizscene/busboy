package com.undergroundquizscene.clairvoyage

import cats.effect.IO
import cats.implicits._
import io.circe._
import io.circe.generic.auto._
import io.circe.parser._
import org.http4s._
import org.http4s.client.blaze._
import org.http4s.dsl.io._

import com.undergroundquizscene.clairvoyage.model._

object Main extends App {
        val client = Http1Client[IO]().unsafeRunSync
        val churchCrossWest = DUID("7338653551721429731")
        println("Test data:")
        println(testStopData.unsafeRunSync)

        val realStopData = fetchStopData(churchCrossWest)
        println("Real data:")
        println(realStopData.unsafeRunSync)

        val getTripData = for {
                response <- realStopData
                trip <- response.passages.traverse(p => fetchTripData(p.trip.id))
        } yield trip
        println("Trip data:")
        println(getTripData.unsafeRunSync)

        def getStops: IO[Json] = for {
                stops <- client.expect[String]("http://buseireann.ie/inc/proto/bus_stop_points.php")
                json <- IO.fromEither(parse(stripVarDeclaration(stops)))
        } yield json

        def fetchStopData(stop: DUID): IO[StopPassage.Response] = callStopPassageTdi[StopPassage.Response](stop = Some(stop))

        def fetchTripData(trip: DUID): IO[StopPassage.Response] =  callStopPassageTdi[StopPassage.Response](trip = Some(trip))

        def callStopPassageTdi[A](stop: Option[DUID] = None, trip: Option[DUID] = None)(implicit decoder: EntityDecoder[IO, A]): IO[A] = for {
                uri <- IO.fromEither(Uri.fromString("http://buseireann.ie/inc/proto/stopPassageTdi.php"))
                uriWithParams = uri.withOptionQueryParam("stop_point", stop.map(_.value)).withOptionQueryParam("trip", trip.map(_.value))
                response <- client.expect[A](uriWithParams).handleErrorWith { e =>
                        e match {
                                case e: InvalidMessageBodyFailure => IO.raiseError(e.getCause)
                        }
                }
        } yield response

        def testStopData: IO[StopPassage.Response] = IO.fromEither(for {
                testJson <- parse(scala.io.Source.fromFile("src/main/resources/example-responses/stopPassage.json").mkString)
                testResponse <- testJson.as[StopPassage.Response]
        } yield testResponse)

        def stripVarDeclaration(javascript: String): String = javascript.dropWhile(_ != '{').dropRight(1)
}
