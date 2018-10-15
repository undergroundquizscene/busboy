package com.undergroundquizscene.busboy

import cats.effect.IO
import cats.implicits._
import io.circe._
import io.circe.generic.auto._
import io.circe.parser._
import org.http4s._
import org.http4s.dsl.io._
import org.http4s.client.blaze._
import org.http4s.dsl.io._
import org.http4s.server.blaze._

import com.undergroundquizscene.busboy.endpoints._

object Main extends App {
        implicit val client = Http1Client[IO]().unsafeRunSync

        val locationService = HttpService[IO] {
                case GET -> Root / stop / "next" => {
                        val trips = getTripsForStop(Stop(DUID(stop)))
                        Ok(trips.map(_.toString))
                }
        }

        val builder = BlazeBuilder[IO].bindHttp(8080, "localhost").mountService(locationService, "/").start
        val server = builder.unsafeRunSync()

        def predict(): Unit = {
                val lastThreeStops = Set("7338653551721429601", "7338653551721429591", "7338653551721429581").map(DUID andThen Stop)
                val churchCrossEast = Stop(DUID("7338653551721429731"))
                val realStopData = fetchStopData(churchCrossEast)
                val testStopData = fetchTestStopData
                val getTripData = for {
                        response <- realStopData
                        trip <- choosePassage(response.passages).traverse(p => fetchTripData(p.trip))
                } yield trip.map(t => t.copy(
                        passages = t.passages.filter(p => lastThreeStops.contains(p.stop)).sortBy(_.stop.id.value)
                ))

                pprint.pprintln("Trip data:")
                pprint.pprintln(getTripData.unsafeRunSync, height=100000000)

        }

        def choosePassage(passages: List[StopPassage.Passage]): Option[StopPassage.Passage] = passages.headOption

        def getTripsForStop(s: Stop): IO[List[StopPassage.Response]] = for {
                response <- fetchStopData(s)
                trips <- response.passages.traverse(p => fetchTripData(p.trip))
        } yield trips

        def getStops: IO[Json] = for {
                stops <- client.expect[String]("http://buseireann.ie/inc/proto/bus_stop_points.php")
                json <- IO.fromEither(parse(stripVarDeclaration(stops)))
        } yield json

        def fetchStopData(s: Stop): IO[StopPassage.Response] = StopPassage.get(s)
        def fetchTripData(t: Trip): IO[StopPassage.Response] =  StopPassage.get(t)

        def fetchTestStopData: IO[StopPassage.Response] = readTestData[StopPassage.Response]("src/main/resources/example-responses/stopPassages.json")

        def fetchTestTripData: IO[StopPassage.Response] = readTestData[StopPassage.Response]("src/main/resources/example-responses/tripPassages.json")

        def readTestData[A](filePath: String)(implicit decoder: Decoder[A]): IO[A] = IO.fromEither(for {
                testJson <- parse(scala.io.Source.fromFile(filePath).mkString)
                testResponse <- testJson.as[A]
        } yield testResponse)

        def stripVarDeclaration(javascript: String): String = javascript.dropWhile(_ != '{').dropRight(1)
}
