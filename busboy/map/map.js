function main() {
	var mymap = L.map('map').setView([51.89543, -8.56371], 13);
	L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
		attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
		maxZoom: 18,
		id: 'mapbox.streets',
		accessToken: 'pk.eyJ1IjoidW5kZXJncm91bmRxdWl6c2NlbmUiLCJhIjoiY2pxbWlybGN6MjNsOTQzbWI0ODM1cTFvZCJ9.DLuaCQrcPzbAMCqmbeja3Q'
	}).addTo(mymap);
	let index = 0;
	let tripMarkers = [];

	function drawNewTrip(index) {
		console.log(`Drawing trip ${index}`);
		tripMarkers.forEach(m => m.remove());
		getPoints(trips[index].id)
		.then(ps => {
			console.log(`Trip has ${ps.points.length} points`);
			return ps;
		})
		.then(tps => {
			tps.points.sort((p, q) => p.time.localeCompare(q.time));
			tripMarkers = drawTrip(mymap, tps, "blue");
		});
	}

	function receiveTrips(ts) {
		trips = ts.map(t => {
			return {id: t}
		});
		index = 0;
		drawNewTrip(0);
	}

	document.querySelector("#next").addEventListener(
		"click",
		e => {
			index = rem(index + 1, trips.length);
			drawNewTrip(index);
		}
	);
	document.querySelector("#previous").addEventListener(
		"click",
		e => {
			index = rem(index - 1, trips.length);
			drawNewTrip(index);
		}
	);
	document.querySelector("#getTrips").addEventListener(
		"click",
		e => {
			let date = document.querySelector("#date").value;
			let route = document.querySelector("#route").value;
			fetchTrips(date, route).then(ts => receiveTrips(ts));
		}
	);
}

function fetchTrips(date, route) {
	console.log(`Fetching trips for date ${date} and route ${route}`);
	return fetch(`/trips/${date}/${route}`, {mode: "no-cors"})
	.then(r => {
		if (r.ok) {
			console.log("Got trips");
			return r.json();
		} else {
			throw new ResponseError(
				"Problem with trips response",
				r
			);
		}
	})
	.then(ts => {
		console.log(`There are ${ts.length} trips`);
		return ts;
	})
	.catch(e => console.log(e.toString()));
}

function getPoints(trip) {
	return fetch(`/points/${trip}/`, {mode: "no-cors"})
	.then(r => {
		if (r.ok) {
			return r.json();
		} else {
			throw new ReponseError("Problem with points response", r);
		}
	})
	.catch(e => console.log(e.toString()));
}

function drawTrip(map, trip) {
	delta = 1 / (trip.points.length - 1);
	return trip.points.map((point, index) => {
		const rgb = hslToRgb((0 + (index * delta)) % 1, 1, 0.4);
		return L.circle(
			[point.latitude / 3600000, point.longitude / 3600000],
			{
				radius: 20,
				color: `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`
			}
		).addTo(map).bindTooltip(point.time);
	});
}

function rem(x, y) {
	if (x < 0) {
		return rem(x + y, y);
	} else {
		return x % y;
	}
}

let trips = [];

class ResponseError extends Error {
	constructor(message, response, ...params) {
		super(...params);
		if (Error.captureStackTrace) {
			Error.captureStackTrace(this, CustomError);
		}
		this.message = message;
		this.response = response;
	}
	toString() {
		const responseText = `Response(status="${this.r.status} ${this.r.statusText})`;
		return `ResponseError(message=${this.message}, response=${responseText})`;
	}
}

/**
 * Converts an RGB color value to HSL. Conversion formula
 * adapted from http://en.wikipedia.org/wiki/HSL_color_space.
 * Assumes r, g, and b are contained in the set [0, 255] and
 * returns h, s, and l in the set [0, 1].
 *
 * @param   Number  r       The red color value
 * @param   Number  g       The green color value
 * @param   Number  b       The blue color value
 * @return  Array           The HSL representation
 */
function rgbToHsl(r, g, b) {
  r /= 255, g /= 255, b /= 255;

  var max = Math.max(r, g, b), min = Math.min(r, g, b);
  var h, s, l = (max + min) / 2;

  if (max == min) {
    h = s = 0; // achromatic
  } else {
    var d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }

    h /= 6;
  }

  return [ h, s, l ];
}

/**
 * Converts an HSL color value to RGB. Conversion formula
 * adapted from http://en.wikipedia.org/wiki/HSL_color_space.
 * Assumes h, s, and l are contained in the set [0, 1] and
 * returns r, g, and b in the set [0, 255].
 *
 * @param   Number  h       The hue
 * @param   Number  s       The saturation
 * @param   Number  l       The lightness
 * @return  Array           The RGB representation
 */
function hslToRgb(h, s, l) {
  var r, g, b;

  if (s == 0) {
    r = g = b = l; // achromatic
  } else {
    function hue2rgb(p, q, t) {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1/6) return p + (q - p) * 6 * t;
      if (t < 1/2) return q;
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
      return p;
    }

    var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    var p = 2 * l - q;

    r = hue2rgb(p, q, h + 1/3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1/3);
  }

  return [ r * 255, g * 255, b * 255 ];
}

main();
