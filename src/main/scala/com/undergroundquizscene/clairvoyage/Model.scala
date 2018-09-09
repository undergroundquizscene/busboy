package com.undergroundquizscene.clairvoyage.model

import cats.effect.IO
import cats.instances.stream._
import cats.instances.either._
import cats.syntax.traverse._
import io.circe._
import io.circe.generic.auto._
import io.circe.parser._
import io.circe.syntax._
import org.http4s.circe._

case class DUID(value: String)

object StopPassage {
        case class Response(passages: List[Passage])
        case class Passage(id: DUID, lastModified: BigInt, arrival: ArrivalData)
        case class ArrivalData(scheduledTime: Int, actualTime: Int)

        implicit lazy val decoder = jsonOf[IO, Response]
        implicit lazy val responseDecoder: Decoder[Response] = Decoder.decodeJson.emap { json =>
                val cursor = json.hcursor.downField("stopPassageTdi")
                cursor.keys.toRight("No keys in object").flatMap { keys =>
                        val passageKeys = keys.toStream.filter(_.startsWith("passage")).sorted
                        val decodedPassages: Either[DecodingFailure, Stream[Passage]] = passageKeys.traverse { k =>
                                cursor.downField(k).as[Passage]
                        }
                        val response: Either[DecodingFailure, Response] = decodedPassages.map(s => Response(s.toList))
                        response.left.map(_.toString)
                }
        }
        implicit lazy val passageDecoder: Decoder[Passage] =
                Decoder.forProduct3("duid", "last_modification_timestamp", "arrival_data")(Passage(_, _, _))
        implicit lazy val duidDecoder: Decoder[DUID] = Decoder.decodeString.map(DUID(_))
        implicit lazy val arrivalDecoder: Decoder[ArrivalData] =
                Decoder.forProduct2("scheduled_passage_time_utc", "actual_passage_time_utc")(ArrivalData(_, _))
}
