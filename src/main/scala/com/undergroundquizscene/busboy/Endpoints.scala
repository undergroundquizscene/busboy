package com.undergroundquizscene.busboy.model

import cats.effect.IO
import cats.implicits._
// import cats.syntax.traverse._
import io.circe._
import io.circe.generic.auto._
import java.time.{Instant, LocalDateTime, ZoneId}
import org.http4s.{EntityDecoder, InvalidMessageBodyFailure}
import org.http4s.circe._
import org.http4s.client.Client
import org.http4s.Uri.uri

case class DUID(value: String)
final case class Trip(id: DUID)
final case class Stop(id: DUID)

object StopPassage {
        def get(params: Parameter*)(implicit client: Client[IO]): IO[Response] = {
                val urlWithParams = params.foldRight(url){ (p, u) =>
                        u.withQueryParam(p.name, p.value)
                }
                client.expect[Response](urlWithParams).handleErrorWith { e =>
                        e match {
                                case e: InvalidMessageBodyFailure => IO.raiseError(e.getCause)
                        }
                }
        }

        val url = uri("http://buseireann.ie/inc/proto/stopPassageTdi.php")

        sealed trait Parameter {
                val name: String
                val value: String
        }
        implicit class TripParameter(t: Trip) extends Parameter {
                val name = "trip"
                val value = t.id.value
        }
        implicit class StopParameter(s: Stop) extends Parameter {
                val name = "stop_point"
                val value = s.id.value
        }

        final case class Response(passages: List[Passage])
        final case class Passage(id: DUID, lastModified: LastModified, arrival: Option[ArrivalData], trip: Trip, stop: Stop)
        final case class ArrivalData(scheduledTime: ScheduledTime, actualTime: Option[ActualTime]) {
                def clock(t: LocalDateTime): String = {
                        val h = t.getHour
                        val m = t.getMinute
                        val s = t.getSecond
                        s"$h:$m:$s"
                }
                override val toString: String = s"Scheduled: ${clock(scheduledTime.dateTime)}, Arrived: ${actualTime.map(t => clock(t.dateTime))}"
        }
        final case class ScheduledTime(dateTime: LocalDateTime)
        final case class ActualTime(dateTime: LocalDateTime)
        final case class LastModified(dateTime: LocalDateTime)
        sealed trait EpochUnit {
                val instant: Instant
        }
        final case class EpochSecond(instant: Instant) extends EpochUnit
        final case class EpochMilli(instant: Instant) extends EpochUnit

        implicit lazy val decoder: EntityDecoder[IO, Response] = jsonOf[IO, Response]
        implicit lazy val responseDecoder: Decoder[Response] = Decoder.decodeJson.emap { json =>
                val cursor = json.hcursor.downField("stopPassageTdi")
                cursor.keys.toRight("No keys in object").flatMap { keys =>
                        val passageKeys = keys.toStream.filter(_.startsWith("passage"))
                        val decodedPassages: Either[DecodingFailure, Stream[Passage]] = passageKeys.traverse { k =>
                                cursor.downField(k).as[Passage]
                        }
                        val response: Either[DecodingFailure, Response] = decodedPassages.map(s => Response(s.toList))
                        response.left.map(_.toString)
                }
        }
        implicit lazy val passageDecoder: Decoder[Passage] =
                Decoder.forProduct5(
                        "duid", "last_modification_timestamp", "arrival_data", "trip_duid", "stop_point_duid"
                )((i: DUID, lm: LastModified, ad: Option[ArrivalData], t: Trip, d: Stop) => Passage(i, lm, ad, t, d))
        implicit lazy val duidDecoder: Decoder[DUID] = Decoder.decodeString.map(DUID(_))
        implicit lazy val arrivalDecoder: Decoder[ArrivalData] =
                Decoder.forProduct2("scheduled_passage_time_utc", "actual_passage_time_utc")((st, at) => {
                        ArrivalData(st, at)
                })
        implicit lazy val tripDecoder: Decoder[Trip] = Decoder.forProduct1("duid")(Trip(_))
        implicit lazy val scheduledTimeDecoder: Decoder[ScheduledTime] = epochMilliDecoder.map(ScheduledTime(_))
        implicit lazy val actualTimeDecoder: Decoder[ActualTime] = epochSecondDecoder.map(ActualTime(_))
        implicit lazy val lastModifiedDecoder: Decoder[LastModified] = epochMilliDecoder.map(LastModified(_))
        implicit def dateTime(e: EpochUnit): LocalDateTime = LocalDateTime.ofInstant(e.instant, ZoneId.systemDefault)
        implicit lazy val stopDecoder: Decoder[Stop] = Decoder.forProduct1("duid")(Stop(_))
        implicit lazy val epochSecondDecoder: Decoder[EpochSecond] =
                Decoder.decodeLong.map(l => EpochSecond(Instant.ofEpochSecond(l)))
        implicit lazy val epochMilliDecoder: Decoder[EpochMilli] =
                Decoder.decodeLong.map(l => EpochMilli(Instant.ofEpochMilli(l)))
}
