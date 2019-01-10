function main() {
	var mymap = L.map('map').setView([51.89543, -8.56371], 13);
	L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
		attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
		maxZoom: 18,
		id: 'mapbox.streets',
		accessToken: 'pk.eyJ1IjoidW5kZXJncm91bmRxdWl6c2NlbmUiLCJhIjoiY2pxbWlybGN6MjNsOTQzbWI0ODM1cTFvZCJ9.DLuaCQrcPzbAMCqmbeja3Q'
	}).addTo(mymap);
	let index = 0;
	let tripMarkers = drawTrip(mymap, trips[0], "blue");

	function drawNewTrip(index) {
		console.log(`Drawing trip ${index}`);
		tripMarkers.forEach(m => m.remove());
		getPoints(trips[index].id)
		.then(ps => {
			tripMarkers = drawTrip(mymap, ps.sort((p, q) => p.localeCompare(q)), "blue");
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
	return fetch(`http://undergroundquizscene.com/trips/${date}/${route}`, {mode: "no-cors"})
	.then(r => {
		if (r.ok) {
			console.log("Got trips");
			return r.json();
		} else {
			throw new Error({
				message: "Problem with trips response",
				response: r
			});
		}
	})
	.catch(e => console.log(e));
}

function getPoints(trip) {
	return fetch(`http://undergroundquizscene.com/points/${trip}/`, {mode: "no-cors"})
	.then(r => {
		if (r.ok) {
			console.log("Got response");
			return r.json();
		} else {
			throw new Error("Problem with points response", r);
		}
	})
	.catch(e => console.log(e));
}

function drawTrip(map, trip) {
	let red = 99;
	let green = 99;
	let blue = 10;
	let delta = (99 - blue) / trip.points.length;
	return trip.points.map(point => {
		let result = L.circle(
			[point.latitude / 3600000, point.longitude / 3600000],
			{
				radius: 20,
				color: `#${red}${green}${Math.round(blue)}`
			}
		).addTo(map).bindTooltip(point.time);
		blue = blue + delta;
		return result;
	});
}

function rem(x, y) {
	if (x < 0) {
		return rem(x + y, y);
	} else {
		return x % y;
	}
}

let trips = [
	{
		"id": "7338656568260783885",
		"points": [
			{latitude: 186755890, longitude: -31097830, time: "no time"},
			{latitude: 186755890, longitude: -31097830, time: "no time"},
			{latitude: 186803620, longitude: -30868671, time: "no time"} ,
			{latitude: 186811839, longitude: -30813808, time: "no time"} ,
			{latitude: 186806533, longitude: -30853022, time: "no time"} ,
			{latitude: 186802062, longitude: -30737866, time: "no time"} ,
			{latitude: 186802062, longitude: -30737866, time: "no time"} ,
			{latitude: 186799885, longitude: -30707896, time: "no time"} ,
			{latitude: 186799797, longitude: -30690660, time: "no time"} ,
			{latitude: 186799797, longitude: -30690660, time: "no time"} ,
			{latitude: 186800104, longitude: -30627098, time: "no time"} ,
			{latitude: 186511445, longitude: -30207719, time: "no time"} ,
			{latitude: 186514533, longitude: -30214000, time: "no time"} ,
			{latitude: 186518181, longitude: -30213965, time: "no time"} ,
			{latitude: 186525838, longitude: -30213166, time: "no time"} ,
			{latitude: 186652304, longitude: -30225260, time: "no time"} ,
			{latitude: 186604954, longitude: -30220176, time: "no time"} ,
			{latitude: 186643214, longitude: -30221292, time: "no time"} ,
			{latitude: 186652304, longitude: -30225260, time: "no time"} ,
			{latitude: 186659932, longitude: -30236859, time: "no time"} ,
			{latitude: 186760908, longitude: -30372016, time: "no time"},
			{latitude: 186760908, longitude: -30372016, time: "no time"},
			{latitude: 186761798, longitude: -30372492, time: "no time"},
			{latitude: 186764612, longitude: -30378200, time: "no time"},
			{latitude: 186770609, longitude: -30390415, time: "no time"},
			{latitude: 186774549, longitude: -30399514, time: "no time"},
			{latitude: 186778362, longitude: -30407346, time: "no time"},
			{latitude: 186831372, longitude: -30480626, time: "no time"},
			{latitude: 186824011, longitude: -30475484, time: "no time"},
			{latitude: 186823660, longitude: -30475251, time: "no time"},
			{latitude: 186811211, longitude: -30475591, time: "no time"},
			{latitude: 186810853, longitude: -30475148, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 648000002, longitude: 648000002, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
		]
	},
	{
		id: '7338656568260783886',
		points: [
			{latitude: 186802062, longitude: -30737866, time: "no time"},
			{latitude: 186802062, longitude: -30737866, time: "no time"},
			{latitude: 186799885, longitude: -30707896, time: "no time"},
			{latitude: 186799774, longitude: -30693017, time: "no time"},
			{latitude: 186811326, longitude: -30621874, time: "no time"},
			{latitude: 186511445, longitude: -30207719, time: "no time"},
			{latitude: 186518181, longitude: -30213965, time: "no time"},
			{latitude: 186525838, longitude: -30213166, time: "no time"},
			{latitude: 186643214, longitude: -30221292, time: "no time"},
			{latitude: 186669119, longitude: -30249340, time: "no time"},
			{latitude: 186761798, longitude: -30372492, time: "no time"},
			{latitude: 186770609, longitude: -30390415, time: "no time"},
			{latitude: 186831372, longitude: -30480626, time: "no time"},
			{latitude: 186823660, longitude: -30475251, time: "no time"},
			{latitude: 648000002, longitude: 648000002, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
			{latitude: 186804461, longitude: -30463438, time: "no time"},
		]
	},
	{
		id: '7338656568267530242',
		points: [
			{latitude: 648000002, longitude: 648000002, time: "2019-01-06 06:42:26.898"},
			{latitude: 648000002, longitude: 648000002, time: "2019-01-06 06:42:26.914"},
			{latitude: 648000002, longitude: 648000002, time: "2019-01-06 08:13:18.41"},
			{latitude: 186807438, longitude: -30487068, time: "2019-01-06 08:14:30.468"},
			{latitude: 186807438, longitude: -30487068, time: "2019-01-06 08:14:30.484"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:30:25.534"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:30:35.534"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:30:57.561"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:31:28.606"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:31:29.604"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:31:45.626"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:32:00.649"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:32:17.669"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:32:49.712"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:32:49.728"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:33:05.733"},
			{latitude: 186755890, longitude: -31097830, time: "2019-01-06 08:33:22.753"},
			{latitude: 186755982, longitude: -31095140, time: "2019-01-06 08:33:38.775"},
			{latitude: 648000002, longitude: 648000002, time: "2019-01-06 08:34:03.813"},
			{latitude: 648000002, longitude: 648000002, time: "2019-01-06 08:34:03.829"},
			{latitude: 186759494, longitude: -31093690, time: "2019-01-06 08:34:32.846"},
			{latitude: 186764112, longitude: -31091577, time: "2019-01-06 08:34:49.85"},
			{latitude: 186764112, longitude: -31091577, time: "2019-01-06 08:34:49.866"},
			{latitude: 186769253, longitude: -31090368, time: "2019-01-06 08:35:12.892"},
			{latitude: 186770531, longitude: -31079309, time: "2019-01-06 08:35:39.927"},
			{latitude: 186773171, longitude: -31063668, time: "2019-01-06 08:36:10.956"},
			{latitude: 186782659, longitude: -31033542, time: "2019-01-06 08:37:06.009"},
			{latitude: 186785273, longitude: -31029556, time: "2019-01-06 08:37:44.09"},
			{latitude: 186788972, longitude: -31020368, time: "2019-01-06 08:38:02.108"},
			{latitude: 186788638, longitude: -31007451, time: "2019-01-06 08:38:24.136"},
			{latitude: 186789491, longitude: -30995690, time: "2019-01-06 08:38:49.159"},
			{latitude: 186790403, longitude: -30989250, time: "2019-01-06 08:39:23.198"},
			{latitude: 186790575, longitude: -30987966, time: "2019-01-06 08:39:41.217"},
			{latitude: 186792313, longitude: -30975510, time: "2019-01-06 08:40:31.294"},
			{latitude: 186796624, longitude: -30945518, time: "2019-01-06 08:41:21.355"},
			{latitude: 186796856, longitude: -30931756, time: "2019-01-06 08:41:51.386"},
			{latitude: 186796829, longitude: -30926765, time: "2019-01-06 08:42:34.458"},
			{latitude: 186796829, longitude: -30926765, time: "2019-01-06 08:42:50.48"},
			{latitude: 186796829, longitude: -30926765, time: "2019-01-06 08:42:50.495"},
			{latitude: 186796826, longitude: -30925465, time: "2019-01-06 08:43:07.499"},
			{latitude: 186796826, longitude: -30925465, time: "2019-01-06 08:43:07.515"},
			{latitude: 186796946, longitude: -30918715, time: "2019-01-06 08:43:38.544"},
			{latitude: 186799158, longitude: -30900258, time: "2019-01-06 08:44:36.624"},
			{latitude: 186803620, longitude: -30868671, time: "2019-01-06 08:46:01.044"},
			{latitude: 186809458, longitude: -30840995, time: "2019-01-06 08:47:07.12"},
			{latitude: 186811742, longitude: -30826395, time: "2019-01-06 08:47:24.155"},
			{latitude: 186811534, longitude: -30809856, time: "2019-01-06 08:47:53.188"},
			{latitude: 186811534, longitude: -30809856, time: "2019-01-06 08:47:53.203"},
			{latitude: 186811611, longitude: -30807039, time: "2019-01-06 08:47:59.209"},
			{latitude: 186811533, longitude: -30785200, time: "2019-01-06 08:48:30.269"},
			{latitude: 186810764, longitude: -30765728, time: "2019-01-06 08:48:57.289"},
			{latitude: 186810764, longitude: -30765728, time: "2019-01-06 08:48:57.305"},
			{latitude: 186808952, longitude: -30752013, time: "2019-01-06 08:49:22.328"},
			{latitude: 186802680, longitude: -30738539, time: "2019-01-06 08:49:58.38"},
			{latitude: 186799903, longitude: -30709206, time: "2019-01-06 08:51:13.48"},
			{latitude: 186799872, longitude: -30700247, time: "2019-01-06 08:51:33.511"},
			{latitude: 186799873, longitude: -30685949, time: "2019-01-06 08:51:57.551"},
			{latitude: 186799873, longitude: -30685949, time: "2019-01-06 08:51:58.549"},
			{latitude: 186800133, longitude: -30670437, time: "2019-01-06 08:52:17.597"},
			{latitude: 186798337, longitude: -30659404, time: "2019-01-06 08:52:26.598"},
			{latitude: 186798337, longitude: -30659404, time: "2019-01-06 08:52:37.628"},
			{latitude: 186798239, longitude: -30652319, time: "2019-01-06 08:52:56.645"},
			{latitude: 186798239, longitude: -30652319, time: "2019-01-06 08:52:56.645"},
			{latitude: 186798891, longitude: -30642512, time: "2019-01-06 08:53:12.666"},
			{latitude: 186800040, longitude: -30628094, time: "2019-01-06 08:53:35.692"},
			{latitude: 186800301, longitude: -30624107, time: "2019-01-06 08:53:57.751"},
			{latitude: 186804331, longitude: -30624203, time: "2019-01-06 08:54:05.723"},
			{latitude: 186804331, longitude: -30624203, time: "2019-01-06 08:54:12.743"},
			{latitude: 186805167, longitude: -30624133, time: "2019-01-06 08:54:30.761"},
			{latitude: 186811326, longitude: -30621874, time: "2019-01-06 08:54:39.763"},
			{latitude: 186811326, longitude: -30621874, time: "2019-01-06 08:54:55.8"},
			{latitude: 186814157, longitude: -30616642, time: "2019-01-06 08:55:12.82"},
			{latitude: 186816123, longitude: -30606684, time: "2019-01-06 08:55:35.861"},
			{latitude: 186818264, longitude: -30594406, time: "2019-01-06 08:55:49.886"},
			{latitude: 186826886, longitude: -30508269, time: "2019-01-06 09:02:00.611"},
			{latitude: 186830384, longitude: -30487413, time: "2019-01-06 09:03:11.686"},
			{latitude: 186830492, longitude: -30486938, time: "2019-01-06 09:03:27.724"},
			{latitude: 186830492, longitude: -30486938, time: "2019-01-06 09:15:20.813"},
			{latitude: 186830492, longitude: -30486938, time: "2019-01-06 09:15:21.812"},
			{latitude: 186830492, longitude: -30486938, time: "2019-01-06 09:15:37.849"},
			{latitude: 186831369, longitude: -30483348, time: "2019-01-06 09:15:49.861"},
			{latitude: 186831369, longitude: -30483348, time: "2019-01-06 09:15:59.876"},
			{latitude: 186831550, longitude: -30482649, time: "2019-01-06 09:16:21.904"},
			{latitude: 186831550, longitude: -30482649, time: "2019-01-06 09:16:22.902"},
			{latitude: 186829915, longitude: -30479596, time: "2019-01-06 09:16:44.93"},
			{latitude: 186826231, longitude: -30476965, time: "2019-01-06 09:16:57.956"},
			{latitude: 186812552, longitude: -30476730, time: "2019-01-06 09:17:56.036"},
			{latitude: 186807919, longitude: -30470769, time: "2019-01-06 09:18:24.07"},
			{latitude: 186805553, longitude: -30467238, time: "2019-01-06 09:18:42.104"},
			{latitude: 186802702, longitude: -30458813, time: "2019-01-06 09:19:05.177"},
			{latitude: 186799420, longitude: -30450026, time: "2019-01-06 09:19:19.155"},
			{latitude: 186798558, longitude: -30446831, time: "2019-01-06 09:19:32.181"},
			{latitude: 186798335, longitude: -30445990, time: "2019-01-06 09:19:57.235"},
			{latitude: 186798335, longitude: -30445990, time: "2019-01-06 09:19:57.251"},
			{latitude: 186796119, longitude: -30440850, time: "2019-01-06 09:20:23.287"},
			{latitude: 186791557, longitude: -30432789, time: "2019-01-06 09:20:45.315"},
			{latitude: 186788558, longitude: -30426625, time: "2019-01-06 09:20:58.357"},
			{latitude: 186782686, longitude: -30415341, time: "2019-01-06 09:21:22.381"},
			{latitude: 186781623, longitude: -30413134, time: "2019-01-06 09:21:27.389"},
			{latitude: 186772996, longitude: -30395915, time: "2019-01-06 09:22:10.446"},
			{latitude: 186768596, longitude: -30386296, time: "2019-01-06 09:22:34.47"},
			{latitude: 186764581, longitude: -30378128, time: "2019-01-06 09:23:02.629"},
			{latitude: 186764017, longitude: -30376957, time: "2019-01-06 09:23:19.664"},
			{latitude: 186761527, longitude: -30372295, time: "2019-01-06 09:23:44.719"},
			{latitude: 186761484, longitude: -30372287, time: "2019-01-06 09:23:58.743"},
			{latitude: 186757419, longitude: -30368684, time: "2019-01-06 09:24:19.757"},
			{latitude: 186757419, longitude: -30368684, time: "2019-01-06 09:24:19.772"},
			{latitude: 186753484, longitude: -30357500, time: "2019-01-06 09:25:03.828"},
			{latitude: 186752104, longitude: -30346830, time: "2019-01-06 09:25:34.919"},
			{latitude: 186746508, longitude: -30329449, time: "2019-01-06 09:26:24.996"},
			{latitude: 186743185, longitude: -30323513, time: "2019-01-06 09:26:42.016"},
			{latitude: 186736098, longitude: -30309294, time: "2019-01-06 09:27:44.152"},
			{latitude: 186727587, longitude: -30301762, time: "2019-01-06 09:28:07.178"},
			{latitude: 186723369, longitude: -30299195, time: "2019-01-06 09:28:16.195"},
			{latitude: 186718929, longitude: -30295637, time: "2019-01-06 09:28:29.221"},
			{latitude: 186711286, longitude: -30287594, time: "2019-01-06 09:28:51.249"},
			{latitude: 186711286, longitude: -30287594, time: "2019-01-06 09:28:51.264"},
			{latitude: 186697012, longitude: -30273567, time: "2019-01-06 09:30:15.397"},
			{latitude: 186650185, longitude: -30222666, time: "2019-01-06 09:32:57.858"},
			{latitude: 186633987, longitude: -30228145, time: "2019-01-06 09:33:58.971"},
			{latitude: 186625121, longitude: -30224621, time: "2019-01-06 09:34:23.011"},
			{latitude: 186616663, longitude: -30223131, time: "2019-01-06 09:34:38.05"},
			{latitude: 186601534, longitude: -30216940, time: "2019-01-06 09:35:07.082"},
			{latitude: 186593190, longitude: -30217621, time: "2019-01-06 09:35:37.128"},
			{latitude: 186580717, longitude: -30226230, time: "2019-01-06 09:36:08.172"},
			{latitude: 186574368, longitude: -30225941, time: "2019-01-06 09:36:44.24"},
			{latitude: 186566996, longitude: -30219593, time: "2019-01-06 09:37:00.262"},
			{latitude: 186555056, longitude: -30212471, time: "2019-01-06 09:37:53.35"},
			{latitude: 186554245, longitude: -30212288, time: "2019-01-06 09:38:17.405"},
			{latitude: 186545737, longitude: -30209634, time: "2019-01-06 09:38:44.441"},
			{latitude: 186543975, longitude: -30209296, time: "2019-01-06 09:38:53.473"},
			{latitude: 186537370, longitude: -30209252, time: "2019-01-06 09:39:11.492"},
			{latitude: 186537370, longitude: -30209252, time: "2019-01-06 09:39:25.516"},
			{latitude: 186536592, longitude: -30209576, time: "2019-01-06 09:39:42.521"},
			{latitude: 186536592, longitude: -30209576, time: "2019-01-06 09:39:45.531"},
			{latitude: 186532809, longitude: -30211229, time: "2019-01-06 09:40:02.551"},
			{latitude: 186529294, longitude: -30212292, time: "2019-01-06 09:40:20.585"},
			{latitude: 186528679, longitude: -30212471, time: "2019-01-06 09:40:45.639"},
			{latitude: 186528679, longitude: -30212471, time: "2019-01-06 09:41:00.662"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:41:16.684"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:41:43.735"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:42:00.77"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:42:16.792"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:42:48.882"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:43:04.903"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:43:21.939"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:43:37.976"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:44:10.019"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:44:26.04"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:44:42.078"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:44:59.097"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:45:31.156"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:45:48.192"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:46:03.215"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:46:19.243"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:46:51.302"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:47:08.337"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:47:24.359"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:47:40.38"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:48:12.454"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:48:28.476"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:48:45.496"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:49:02.531"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:49:17.554"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:49:51.594"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:50:06.617"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:50:22.639"},
			{latitude: 186528452, longitude: -30212536, time: "2019-01-06 09:50:39.674"},
			{latitude: 186527473, longitude: -30212784, time: "2019-01-06 09:50:55.696"},
			{latitude: 186521701, longitude: -30219654, time: "2019-01-06 09:51:31.764"},
			{latitude: 186519875, longitude: -30245243, time: "2019-01-06 09:52:12.824"},
			{latitude: 186518652, longitude: -30254537, time: "2019-01-06 09:52:21.841"},
			{latitude: 186503552, longitude: -30253597, time: "2019-01-06 09:53:25.942"},
			{latitude: 186508280, longitude: -30243298, time: "2019-01-06 09:53:52.011"},
			{latitude: 186510510, longitude: -30235269, time: "2019-01-06 09:54:09.015"},
			{latitude: 186511666, longitude: -30230618, time: "2019-01-06 09:54:54.084"},
			{latitude: 186511666, longitude: -30230618, time: "2019-01-06 09:55:10.106"},
			{latitude: 186511666, longitude: -30230618, time: "2019-01-06 09:55:26.143"},
			{latitude: 186511666, longitude: -30230618, time: "2019-01-06 09:55:43.147"},
			{latitude: 186511876, longitude: -30229337, time: "2019-01-06 09:55:59.184"},
			{latitude: 186512439, longitude: -30194526, time: "2019-01-06 09:57:32.334"},
			{latitude: 186509744, longitude: -30183136, time: "2019-01-06 09:58:02.38"},
			{latitude: 186517260, longitude: -30187892, time: "2019-01-06 09:58:33.409"},
			{latitude: 186523643, longitude: -30181881, time: "2019-01-06 09:59:02.457"},
			{latitude: 186523642, longitude: -30181786, time: "2019-01-06 09:59:17.48"},
			{latitude: 186523611, longitude: -30169259, time: "2019-01-06 09:59:47.526"},
			{latitude: 186516002, longitude: -30071542, time: "2019-01-06 10:02:12.796"},
			{latitude: 186504058, longitude: -30031377, time: "2019-01-06 10:03:12.966"},
			{latitude: 186495434, longitude: -30017232, time: "2019-01-06 10:03:44.011"},
			{latitude: 186492600, longitude: -30000100, time: "2019-01-06 10:04:14.073"},
			{latitude: 186484441, longitude: -29983866, time: "2019-01-06 10:04:46.131"},
			{latitude: 186491251, longitude: -29966245, time: "2019-01-06 10:05:15.179"},
			{latitude: 186499228, longitude: -29952389, time: "2019-01-06 10:05:45.256"},
			{latitude: 186495500, longitude: -29934228, time: "2019-01-06 10:06:15.318"},
			{latitude: 186491750, longitude: -29915996, time: "2019-01-06 10:06:46.363"},
			{latitude: 186492459, longitude: -29904638, time: "2019-01-06 10:07:04.381"},
			{latitude: 186495577, longitude: -29878316, time: "2019-01-06 10:08:31.524"},
			{latitude: 186494685, longitude: -29869990, time: "2019-01-06 10:08:55.564"},
			{latitude: 186490291, longitude: -29866680, time: "2019-01-06 10:09:13.598"},
			{latitude: 186489511, longitude: -29866162, time: "2019-01-06 10:09:24.612"},
			{latitude: 186488641, longitude: -29865660, time: "2019-01-06 10:09:43.66"},
			{latitude: 186761811, longitude: -30372666, time: "2019-01-06 11:27:26.888"},
			{latitude: 186797284, longitude: -30442507, time: "2019-01-06 11:30:29.926"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 14:24:29.393"},
			{latitude: 186413185, longitude: -29943154, time: "2019-01-06 14:51:35.699"},
			{latitude: 186504755, longitude: -30033183, time: "2019-01-06 14:53:03.732"},
			{latitude: 186746926, longitude: -30364495, time: "2019-01-06 15:26:45.343"},
			{latitude: 186765097, longitude: -30379239, time: "2019-01-06 15:29:47.539"},
			{latitude: 186829557, longitude: -30535803, time: "2019-01-06 15:48:30.917"},
		]
	},
	{
		id: '7338656568267530244',
		points: [
			{latitude: 186811533, longitude: -30785200, time: "2019-01-06 08:48:26.759"},
			{latitude: 186811533, longitude: -30785200, time: "2019-01-06 08:48:26.775"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 10:30:19.937"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 10:30:35.974"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 10:30:35.99"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 10:30:52.011"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 10:30:52.027"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 10:31:08.048"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 10:31:40.743"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 10:31:56.78"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 10:31:56.795"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 10:32:13.815"},
			{latitude: 186392984, longitude: -29921980, time: "2019-01-06 10:32:29.852"},
			{latitude: 186393769, longitude: -29922477, time: "2019-01-06 10:32:46.872"},
			{latitude: 186406533, longitude: -29934190, time: "2019-01-06 10:33:46.986"},
			{latitude: 186409974, longitude: -29940805, time: "2019-01-06 10:34:05.036"},
			{latitude: 186415460, longitude: -29940565, time: "2019-01-06 10:34:28.062"},
			{latitude: 186415460, longitude: -29940565, time: "2019-01-06 10:34:28.077"},
			{latitude: 186422009, longitude: -29937306, time: "2019-01-06 10:34:48.108"},
			{latitude: 186435625, longitude: -29935115, time: "2019-01-06 10:35:17.171"},
			{latitude: 186435625, longitude: -29935115, time: "2019-01-06 10:35:18.154"},
			{latitude: 186444161, longitude: -29936153, time: "2019-01-06 10:35:31.196"},
			{latitude: 186443147, longitude: -29922944, time: "2019-01-06 10:36:30.306"},
			{latitude: 186443147, longitude: -29922944, time: "2019-01-06 10:36:30.321"},
			{latitude: 186443193, longitude: -29910907, time: "2019-01-06 10:36:57.372"},
			{latitude: 186445870, longitude: -29899224, time: "2019-01-06 10:37:17.434"},
			{latitude: 186448605, longitude: -29872943, time: "2019-01-06 10:38:23.564"},
			{latitude: 186468698, longitude: -29874439, time: "2019-01-06 10:39:23.687"},
			{latitude: 186474792, longitude: -29868297, time: "2019-01-06 10:39:54.716"},
			{latitude: 186474792, longitude: -29868297, time: "2019-01-06 10:39:54.732"},
			{latitude: 186471724, longitude: -29862290, time: "2019-01-06 10:40:21.767"},
			{latitude: 186479532, longitude: -29858306, time: "2019-01-06 10:40:48.834"},
			{latitude: 186479896, longitude: -29857399, time: "2019-01-06 10:41:11.907"},
			{latitude: 186481438, longitude: -29856734, time: "2019-01-06 10:41:42.967"},
			{latitude: 186484281, longitude: -29859431, time: "2019-01-06 10:41:53.981"},
			{latitude: 186488924, longitude: -29865798, time: "2019-01-06 10:42:23.091"},
			{latitude: 186488924, longitude: -29865798, time: "2019-01-06 10:42:41.156"},
			{latitude: 186488924, longitude: -29865798, time: "2019-01-06 10:42:59.19"},
			{latitude: 186488924, longitude: -29865798, time: "2019-01-06 10:42:59.205"},
			{latitude: 186488924, longitude: -29865798, time: "2019-01-06 10:43:14.213"},
			{latitude: 186488924, longitude: -29865798, time: "2019-01-06 10:43:30.25"},
			{latitude: 186488924, longitude: -29865798, time: "2019-01-06 10:44:03.307"},
			{latitude: 186488924, longitude: -29865798, time: "2019-01-06 10:44:19.329"},
		]
	},
	{id: '7338656568267530245'},
	{id: '7338656568267530247'},
	{id: '7338656568267530248'},
	{id: '7338656568267530250'},
	{id: '7338656568267530251'},
	{id: '7338656568267530252'},
	{id: '7338656568267530253'},
	{id: '7338656568274099981'},
	{id: '7338656568274099983'},
	{id: '7338656568274099984'},
	{id: '7338656568274185996'},
	{id: '7338656568274185997'},
	{id: '7338656568280801282'},
	{id: '7338656568280801283'},
	{id: '7338656568280801285'},
	{id: '7338656568280801286'},
	{id: '7338656568280801288'}
]

main();
