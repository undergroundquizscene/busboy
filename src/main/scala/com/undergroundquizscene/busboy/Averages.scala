package com.undergroundquizscene.busboy.averages

object Averages {
        def cumulativeMovingAverage(xs: List[Double]): Option[Double] = {
                xs match {
                        case Nil => None
                        case x :: Nil => Some(x)
                        case x :: t => cumulativeMovingAverage(t).map(x + xs.size * _  / (xs.size + 1))
                }
        }

        def exponentialAverage(xs: List[Double]): Option[Double] = {
                val alpha = 2.0 / (xs.size + 1)
                xs match {
                        case Nil => None
                        case x :: Nil => Some(x)
                        case x :: t => exponentialAverage(t).map { a =>
                                (alpha * x) + (1 - alpha) * a
                        }
                }
        }

}
