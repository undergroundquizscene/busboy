var map;
var directionDisplay;
var directionsService;
var stepDisplay;

var position;
var marker = [];
var polyline = [];
var poly2 = [];
var poly = null;
var startLocation = [];
var endLocation = [];
var timerHandle = [];

var markers = [];

var speed = 0.000005, wait = 1;
var infowindow = null;

var myPano;
var panoClient;
var nextPanoId;

var startLoc;
var endLoc;
var whatstep = 1;

var startLoc = [];

var endLoc = [];

var Colors = ["#FF0000", "#00FF00", "#0000FF"];

	var user_lat;
	var user_lng;
	var bus_stops;
	var bus_stops_detailed;
	var buses;
	var passage_data = [];
	var markers_bus_stop_medium = [];
	var markers_bus_stop_fine = [];
	var bus_stop_markers_displayed = 0;
	var buses_moved_yet = 0;
	var current_center;
	var current_zoom;
	var lastRouteValue = '';
	var intervalId = 0;
	var intervalTripId = 0;
	var searchByRoute_stop = 0;
	var zoom_type = 0;
	var trip_data = [];
	var duplicate_bus_stop = [];

	function getTimestamp() {
		var milliseconds = new Date().getTime(); // works with new and old browsers
		return Math.floor(milliseconds / 1000);
	}

	function secondsToTime(secs) {
		var hours = Math.floor(secs / (60 * 60));

		var divisor_for_minutes = secs % (60 * 60);
		var minutes = Math.floor(divisor_for_minutes / 60);

		var divisor_for_seconds = divisor_for_minutes % 60;
		var seconds = Math.ceil(divisor_for_seconds);

		var obj = {
			"h": hours,
			"m": minutes,
			"s": seconds
		};
		return obj;
	}

	function searchByStopName() {

		if(document.getElementById('map_canvas').style.display == 'block') {
			resetMarkers();
		}

		var stop_name = document.getElementById('form-real-time-information-stop').value;
		stop_name = stop_name.split(' - ['); // strip out bus stop number
		stop_name = stop_name[0];
		var route_element = document.getElementById('form-real-time-information-route');
		if(stop_name == '') {
			$("#error-alert-message").empty();
			document.getElementById('error-alert-message').appendChild(document.createTextNode('You have not entered a Stop Name.'));
			$('#error-alert').foundation('reveal', 'open');
		}
		/*else if(duplicate_bus_stop.length > 1 && stop_name != '' && route_element.disabled == true) {
			$("#did_you_mean").empty();
			var div_element = document.getElementById('did_you_mean');
			for(var i = 0; i < duplicate_bus_stop.length; i++) {
				var input_element = document.createElement('input');
				input_element.setAttribute('class', 'button radius');
				input_element.setAttribute('style', 'margin-top:1em;');
				var onclick = duplicate_bus_stop[i].replace("'", '*');
				onclick = onclick.replace("'", '*');
				input_element.setAttribute('onclick', "viewRealtimeInfo('"+onclick+"');$('#duplicate-rti-alert').foundation('reveal', 'close');");
				input_element.setAttribute('type', 'submit');
				input_element.setAttribute('value', duplicate_bus_stop[i]);
				div_element.appendChild(input_element);
			}
			$('#duplicate-rti-alert').foundation('reveal', 'open');
		}*/
		else if(stop_name != '' && route_element.disabled == true) {
			$("#error-alert-message").empty();
			document.getElementById('error-alert-message').appendChild(document.createTextNode('There are no routes for '+stop_name+'.'));
			$('#error-alert').foundation('reveal', 'open');
		}
		//else if(stop_name != '' && route_element.value == '' && route_element.disabled != true) {
		else if(stop_name != '' && route_element.disabled != true) {
			document.getElementById('real-time-information-intro').style.display = 'none';
			document.getElementById('table_trip_container').style.display = 'none';
			document.getElementById('map_canvas').style.display = 'none';
			document.getElementById('map-legends').style.display = 'none';
			document.getElementById('table_routes_container').style.display = 'block';
			document.getElementById('table_routes_refresh').style.display = 'block';
			//document.getElementById('table_routes_type').style.display = 'block';
			var tbody = document.getElementById('tbody_routes');
			var table_routes = document.getElementById('table_routes');
			var table_routes_title = document.getElementById('table_routes_title');
			$("#tbody_routes").empty();
			$("#table_routes_title").empty();

			var route_element_text_split = '';
			if(route_element.value != '') {
				var route_element_text = $("#form-real-time-information-route option:selected").text();
				route_element_text_split = route_element_text.split(' ');
			}

			function compare(a,b) {
				if (a.due < b.due)
					return -1;
				if (a.due > b.due)
					return 1;
				return 0;
			}

			passage_data.sort(compare);

			var any_data_rows = 0;

			var count = Object.keys(passage_data).length;
			for(var i = 0; i < count; i++) {
				if(passage_data[i]['destination']) {
					var due;
					var due_hide = 0;
					if(passage_data[i]['due'] != '') {
						var timestamp = getTimestamp();
						var time_diff = parseInt(passage_data[i]['due']) - timestamp;
						if(time_diff <= 0) {
							if(passage_data[i]['type'] == 'departures') {
								due = 'Departed';
							}
							else if(passage_data[i]['type'] == 'arrivals') {
								due = 'Arrived';
							}
							if(time_diff < -600) {
								due_hide = 1;
							}
						}
						else {
							if(passage_data[i]['assigned_vehicle'] != '0') {
								var time_convert = secondsToTime(time_diff);
								if(time_diff <= 60) {
									due = 'Due 1 min';
								}
								else if(time_diff < 3600) {
									if(time_convert['m'] == 1) {
										due = 'Due 1 min';
									}
									else {
										due = time_convert['m'] + ' mins';
									}
								}
								else if(time_convert['h'] == 1){
									if(time_convert['m'] == 1) {
										due = time_convert['h'] + ' hour ' + time_convert['m'] + ' min';
									}
									else {
										due = time_convert['h'] + ' hour ' + time_convert['m'] + ' mins';
									}
								}
								else {
									if(time_convert['m'] == 1) {
										due = time_convert['h'] + ' hours ' + time_convert['m'] + ' min';
									}
									else {
										due = time_convert['h'] + ' hours ' + time_convert['m'] + ' mins';
									}
								}
							}
							else {
								due = passage_data[i]['due_time']; // show expected digital time instead
							}
						}
						/*if(passage_data[i]['assigned_vehicle'] != '0') {
							due = due + '*';
						}*/
					}
					if(due_hide == 0) {
						for( var key in obj_routes['routeTdi'] ) {
							if(obj_routes['routeTdi'][key]['duid'] == passage_data[i]['route_duid']) {
								//console.log("'" + route_element_text_split[0] + "' - '" + obj_routes['routeTdi'][key]['short_name'] + "'");
								//if(route_element_text_split == '' || route_element_text_split[0] == obj_routes['routeTdi'][key]['short_name']) {
								var full_route = obj_routes['routeTdi'][key]['short_name'] + ' ' + passage_data[i]['destination'];
								if(route_element_text_split == '' || route_element_text == full_route) {
									any_data_rows = any_data_rows + 1;
									var newRow = tbody.insertRow(-1); //adds a row to the end of the table
									newRow.setAttribute('class', passage_data[i]['type']);
									var newCell = newRow.insertCell(0);
									var route_name = obj_routes['routeTdi'][key]['short_name'];
									newCell.appendChild(document.createTextNode(route_name));
									//newCell.setAttribute('onclick', "showTrip('"+passage_data[i]['trip_duid']+"', '"+route_name+"');loadMapByStopName(\""+stop_name+"\");");
									newCell.setAttribute('onclick', "showTrip('"+passage_data[i]['trip_duid']+"', '"+route_name+"', \""+stop_name+"\", 0);");
									newCell.setAttribute('class', 'text-center');

									var newCell = newRow.insertCell(1);
									newCell.appendChild(document.createTextNode(passage_data[i]['destination']));
									//newCell.setAttribute('onclick', "showTrip('"+passage_data[i]['trip_duid']+"', '"+route_name+"');loadMapByStopName(\""+stop_name+"\");");
									newCell.setAttribute('onclick', "showTrip('"+passage_data[i]['trip_duid']+"', '"+route_name+"', \""+stop_name+"\", 0);");
									newCell.setAttribute('class', 'destination');
									var newCell = newRow.insertCell(2);
									newCell.appendChild(document.createTextNode(due));
									//newCell.setAttribute('onclick', "showTrip('"+passage_data[i]['trip_duid']+"', '"+route_name+"');loadMapByStopName(\""+stop_name+"\");");
									newCell.setAttribute('onclick', "showTrip('"+passage_data[i]['trip_duid']+"', '"+route_name+"', \""+stop_name+"\", 0);");
									newCell.setAttribute('class', 'text-center');
								}
							}
						}
					}
				}
			}

			if(any_data_rows == 0) {
				var newRow = tbody.insertRow(-1); //adds a row to the end of the table
				var newCell = newRow.insertCell(0);
				newCell.setAttribute('class', 'text-center');
				newCell.setAttribute('colspan', '3');
				newCell.appendChild(document.createTextNode("Sorry there are no routes to show. Please press the 'Refresh Results' button to retrieve up-to-date information."));
			}

			$('#table_routes .departures').show();
			$('#table_routes .arrivals').hide();

			document.getElementById('table_routes_type').value = 'departures';

			var onclick = document.getElementById('form-real-time-information-stop').value;
			//var onclick = stop_name.replace("'", '*');
			onclick = onclick.replace("'", '*');
			onclick = onclick.replace("'", '*');
			document.getElementById('table_routes_refresh').setAttribute('onclick', "viewRealtimeInfo('"+onclick+"');return false;");
			table_routes.setAttribute('summary', 'Routes for '+stop_name);
			//table_routes_title.appendChild(document.createTextNode(stop_name));
			//table_routes_title.setAttribute('data-stop', stop_name);

			var table_routes_title_textnode = stop_name + ' - ';

			for(var i = 0; i < duplicate_bus_stop.length; i++) {
				table_routes_title_textnode = table_routes_title_textnode + '[' + duplicate_bus_stop[i] + '] ';
			}

			//table_routes_title.appendChild(document.createTextNode(document.getElementById('form-real-time-information-stop').value));
			table_routes_title.appendChild(document.createTextNode(table_routes_title_textnode));
			table_routes_title.setAttribute('data-stop', document.getElementById('form-real-time-information-stop').value);
			$("html, body").animate({ scrollTop: ($('#table_routes_refresh').offset().top) }, "slow");
		}
		/*else if(stop_name != '' && route_element.value != '' && route_element.disabled != true) {

			var route_name = $("#form-real-time-information-route option:selected").text();
			showTrip(route_element.value, route_name);
			loadMapByStopName(stop_name);
		}*/
	}

	function loadMapByStopName(stop_name, trip_duid, bus_lat, bus_lng) {
		var myOptions = {
			zoom: 7,
			scrollwheel: false,
			center: new google.maps.LatLng(53.398645, -7.711116),
			mapTypeId: google.maps.MapTypeId.ROADMAP
		};

		document.getElementById('real-time-information-intro').style.display = 'none';
		document.getElementById('map_canvas').style.display = 'block';
		document.getElementById('map-legends').style.display = 'block';
		map = new google.maps.Map(document.getElementById('map_canvas'), myOptions);

		google.maps.event.addListenerOnce(map, 'idle', function() {

			var bounds = new google.maps.LatLngBounds();

			var count = Object.keys(trip_data).length;

			for(var i = 0; i < count; i++) {
				var image = {
					url: 'img/bus_stop_icon.png',
					size: new google.maps.Size(24, 34),
					origin: new google.maps.Point(0,0),
					anchor: new google.maps.Point(12, 34)
				};

				var shape = {
					coords: [11, 0, 19, 4, 22, 12, 18, 23, 11, 32, 4, 23, 0, 12, 3, 4],
					type: 'poly'
				};

				var myLatlng = new google.maps.LatLng(trip_data[i]['bus_stop_lat'], trip_data[i]['bus_stop_lng']);

				bounds.extend(myLatlng);

				// create zoomed in marker

				var marker = new google.maps.Marker({
					position: myLatlng,
					map: map,
					icon: image,
					shape: shape,
					visible: false,
					title: trip_data[i]['bus_stop'],
					zIndex: 1
				});

				markers_bus_stop_fine.push(marker);

				google.maps.event.addListener(marker, 'click', function() {

					var onclick = this.title;
					onclick = onclick.replace("'", '*');
					onclick = onclick.replace("'", '*');

					var markerhtml = '<h2>Bus Stop</h2><p>' + this.title + '</p><input type="button" value="View Realtime Info" class="button tiny radius" onclick=\'viewRealtimeInfo("'+onclick+'");return false;\'>';

					if(infowindow) { // close all windows before opening another
						infowindow.close();
					}

					infowindow = new google.maps.InfoWindow({
						content: markerhtml,
						position: this.position,
						//maxWidth: 500,
						pixelOffset: new google.maps.Size(-1, -35)
					});
					infowindow.open(map);
				});

				// create zoomed out marker

				var marker2 = new google.maps.Marker({
					position: myLatlng,
					map: map,
					icon: image,
					shape: shape,
					visible: false,
					title: trip_data[i]['bus_stop'],
					zIndex: 1
				});

				markers_bus_stop_medium.push(marker2);

				google.maps.event.addListener(marker2, 'click', function() {
					map.setCenter(this.position);
					map.setZoom(19);
				});
			}

			map.fitBounds(bounds);

			zoom_type = 2;

			var zoom = map.getZoom();
			hideDisplayBusMarkers(zoom);

			google.maps.event.addListener(map, 'zoom_changed', function() {
				var zoom = map.getZoom();
				hideDisplayBusMarkers(zoom);
			});

			var image = {
				url: 'img/bus_icon.png',
				size: new google.maps.Size(36, 52),
				origin: new google.maps.Point(0,0),
				anchor: new google.maps.Point(18, 52)
			};

			var shape = {
				coords: [18, 1, 30, 6, 35, 19, 28, 36, 17, 50, 6, 36, 0, 19, 5, 6],
				type: 'poly'
			};

			var myLatlng = new google.maps.LatLng(bus_lat, bus_lng);

			var marker = new google.maps.Marker({
				position: myLatlng,
				map: map,
				icon: image,
				shape: shape,
				zIndex: 2
			});

			markers.push(marker);

			startLoc['bus_0'] = bus_lat + ', ' + bus_lng;
			endLoc['bus_0'] = bus_lat + ', ' + bus_lng;

			intervalId = setInterval(function(){ showTripBus(trip_duid); }, 15000);

			current_center = map.getCenter();
			current_zoom = map.getZoom();

			setTimeout(function(){ setRoutes(0, 1); }, 1000);
		});
	}

	function showTripBus(trip_duid) {
		$.ajaxSetup({ cache: false });
		$.getJSON('inc/proto/stopPassageTdi.php', {
			trip: trip_duid
		}, function (passages) {
			var end_loop = 0;
			for( var key in passages['stopPassageTdi'] ) {
				if(end_loop == 0) {
					if(passages['stopPassageTdi'][key]['duid'] && passages['stopPassageTdi'][key]['latitude'] && passages['stopPassageTdi'][key]['longitude']) {
						var bus_lat = passages['stopPassageTdi'][key]['latitude'] / 3600000;
						var bus_lng = passages['stopPassageTdi'][key]['longitude'] / 3600000;
						var bus_duid = passages['stopPassageTdi'][key]['duid'];

						if(startLoc['bus_0']) {
							startLoc['bus_0'] = endLoc['bus_0'];
						}
						else {
							startLoc['bus_0'] = bus_lat + ', ' + bus_lng;
						}
						endLoc['bus_0'] = bus_lat + ', ' + bus_lng;

						end_loop = 1;

						current_center = map.getCenter();
						current_zoom = map.getZoom();

						setTimeout(function(){ setRoutes(0, 1); }, 1000);
					}
				}
			}
		});
	}

	function showTrip(trip_duid, route_name, stop_name, refresh_table) {
		if(refresh_table == 1) {
			var current_trip_type = document.getElementById('table_trip_type').value;
		}
		$.ajaxSetup({ cache: false });
		$.getJSON('inc/proto/stopPassageTdi.php', {
			trip: trip_duid
		}, function (passages) {
			//console.log( Object.keys(passages.stopPassageTdi).length );
			trip_data = [];
			var bus_located = 0;
			var bus_duid;
			var bus_duid_master;
			var bus_lat;
			var bus_lng;
			var previous_utc = 0;
			for( var key in passages['stopPassageTdi'] ) {
				if(passages['stopPassageTdi'][key]['duid']) {
					if(passages['stopPassageTdi'][key]['route_duid']['duid']) {
						var stop_point_duid = passages['stopPassageTdi'][key]['stop_point_duid']['duid'];

						var departure_scheduled_utc;
						var departure_scheduled;
						var departure_actual_utc;
						var departure_actual;
						var arrival_scheduled_utc;
						var arrival_scheduled;
						var arrival_actual_utc;
						var arrival_actual;
						var bus_stop;
						var bus_stop_lat;
						var bus_stop_lng;

						if(passages['stopPassageTdi'][key]['vehicle_duid']) {
							bus_duid = passages['stopPassageTdi'][key]['vehicle_duid']['duid'];
						}
						else {
							bus_duid = 'no_bus'; // if a journey hasn't started sometimes the API won't assign a vehicle
						}

						if(bus_located == 0) {
							if(passages['stopPassageTdi'][key]['latitude'] && passages['stopPassageTdi'][key]['longitude']) {
								bus_lat = passages['stopPassageTdi'][key]['latitude'] / 3600000;
								bus_lng = passages['stopPassageTdi'][key]['longitude'] / 3600000;
								bus_located = 1;
								if(passages['stopPassageTdi'][key]['vehicle_duid']) {
									bus_duid_master = passages['stopPassageTdi'][key]['vehicle_duid']['duid'];
								}
								else {
									bus_duid_master = 'no_bus'; // if a journey hasn't started sometimes the API won't assign a vehicle
								}
								//bus_duid_master = passages['stopPassageTdi'][key]['vehicle_duid']['duid'];
							}
						}

						if(bus_duid_master == bus_duid) { // if a trip has more than one bus then only show the first
							if(passages['stopPassageTdi'][key]['arrival_data'] && passages['stopPassageTdi'][key]['departure_data']) {
								if(passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time_utc']) {
									departure_scheduled_utc = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time_utc'];
									departure_scheduled = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time'];
								}

								if(passages['stopPassageTdi'][key]['departure_data']['actual_passage_time_utc']) {
									departure_actual_utc = passages['stopPassageTdi'][key]['departure_data']['actual_passage_time_utc'];
									departure_actual = passages['stopPassageTdi'][key]['departure_data']['actual_passage_time'];
								}
								else {
									departure_actual_utc = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time_utc'];
									departure_actual = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time'];
								}

								if(passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time_utc']) {
									arrival_scheduled_utc = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time_utc'];
									arrival_scheduled = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time'];
								}

								if(passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time_utc']) {
									arrival_actual_utc = passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time_utc'];
									arrival_actual = passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time'];
								}
								else {
									arrival_actual_utc = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time_utc'];
									arrival_actual = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time'];
								}
							}
							else if(passages['stopPassageTdi'][key]['arrival_data'] && !passages['stopPassageTdi'][key]['departure_data']) {
								if(passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time_utc']) {
									arrival_scheduled_utc = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time_utc'];
									arrival_scheduled = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time'];
									departure_scheduled_utc = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time_utc'];
									departure_scheduled = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time'];
								}

								if(passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time_utc']) {
									arrival_actual_utc = passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time_utc'];
									arrival_actual = passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time'];
									departure_actual_utc = passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time_utc'];
									departure_actual = passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time'];
								}
								else {
									arrival_actual_utc = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time_utc'];
									arrival_actual = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time'];
									departure_actual_utc = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time_utc'];
									departure_actual = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time'];
								}

								/*if(passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time_utc']) {
									scheduled_utc = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time_utc'];
								}
								if(passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time_utc']) {
									expected_utc = passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time_utc'];
								}*/
							}
							else if(!passages['stopPassageTdi'][key]['arrival_data'] && passages['stopPassageTdi'][key]['departure_data']) {
								if(passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time_utc']) {
									departure_scheduled_utc = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time_utc'];
									departure_scheduled = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time'];
									arrival_scheduled_utc = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time_utc'];
									arrival_scheduled = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time'];
								}

								if(passages['stopPassageTdi'][key]['departure_data']['actual_passage_time_utc']) {
									departure_actual_utc = passages['stopPassageTdi'][key]['departure_data']['actual_passage_time_utc'];
									departure_actual = passages['stopPassageTdi'][key]['departure_data']['actual_passage_time'];
									arrival_actual_utc = passages['stopPassageTdi'][key]['departure_data']['actual_passage_time_utc'];
									arrival_actual = passages['stopPassageTdi'][key]['departure_data']['actual_passage_time'];
								}
								else {
									departure_actual_utc = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time_utc'];
									departure_actual = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time'];
									arrival_actual_utc = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time_utc'];
									arrival_actual = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time'];
								}

								/*if(passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time_utc']) {
									scheduled_utc = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time_utc'];
								}
								if(passages['stopPassageTdi'][key]['departure_data']['actual_passage_time_utc']) {
									expected_utc = passages['stopPassageTdi'][key]['departure_data']['actual_passage_time_utc'];
								}*/
							}

							stop_searching = 0;
							for( var key in obj_bus_stop_points['bus_stops'] ) {
								if(obj_bus_stop_points['bus_stops'][key]['duid'] == stop_point_duid && stop_searching == 0) {
									stop_searching = 1;
									bus_stop = obj_bus_stop_points['bus_stops'][key]['name'];
									bus_stop_lat = obj_bus_stop_points['bus_stops'][key]['lat'];
									bus_stop_lng = obj_bus_stop_points['bus_stops'][key]['lng'];
								}
							}

							var vst = bus_stop.substr(0, 2);

							if(vst != 'VS' && vst != 'vs' && vst != 'W9' && vst != 'T9') { // remove stops like 'VST1P1' & 'VST1P2'
								//var parse_utc = parseInt(departure_actual_utc);
								//if(parse_utc >= previous_utc) { // helps remove return journey data (otherwise it duplicates destinations)
									var data = {
										departure_scheduled_utc: departure_scheduled_utc,
										departure_scheduled: departure_scheduled,
										departure_actual_utc: departure_actual_utc,
										departure_actual: departure_actual,
										arrival_scheduled_utc: arrival_scheduled_utc,
										arrival_scheduled: arrival_scheduled,
										arrival_actual_utc: arrival_actual_utc,
										arrival_actual: arrival_actual,
										bus_stop: bus_stop,
										bus_stop_lat: bus_stop_lat,
										bus_stop_lng: bus_stop_lng
									};

									//previous_utc = parse_utc;

									trip_data.push(data);
								//}
							}
						}
					}
				}
			}
			document.getElementById('real-time-information-intro').style.display = 'none';
			document.getElementById('table_routes_container').style.display = 'none';
			document.getElementById('table_routes_refresh').style.display = 'none';
			//document.getElementById('table_routes_type').style.display = 'none';
			document.getElementById('table_trip_container').style.display = 'block';

			var tbody = document.getElementById('tbody_trip');
			var table_trip = document.getElementById('table_trip');
			var table_trip_title = document.getElementById('table_trip_title');
			$("#tbody_trip").empty();
			$("#table_trip_title_type").empty();
			$("#table_trip_title_route").empty();

			function compare(a,b) {
				if (a.departure_scheduled_utc < b.departure_scheduled_utc)
					return -1;
				if (a.departure_scheduled_utc > b.departure_scheduled_utc)
					return 1;
				return 0;
			}

			trip_data.sort(compare);

			var count = Object.keys(trip_data).length;
			for(var i = 0; i < count; i++) {
				var newRow = tbody.insertRow(-1); //adds a row to the end of the table
				var newCell = newRow.insertCell(0);
				if(i == 0) {
					newCell.setAttribute('data-time', trip_data[i]['departure_actual_utc']);
				}
				else {
					newCell.setAttribute('data-time', trip_data[i]['arrival_actual_utc']);
				}
				newCell.appendChild(document.createTextNode('\u00A0'));

				var newCell = newRow.insertCell(1);
				newCell.setAttribute('class', 'departures text-center');
				newCell.appendChild(document.createTextNode(trip_data[i]['departure_scheduled']));
				var newCell = newRow.insertCell(2);
				newCell.setAttribute('class', 'departures text-center');
				newCell.appendChild(document.createTextNode(trip_data[i]['departure_actual']));
				var newCell = newRow.insertCell(3);
				newCell.setAttribute('class', 'arrivals text-center');
				newCell.appendChild(document.createTextNode(trip_data[i]['arrival_scheduled']));
				var newCell = newRow.insertCell(4);
				newCell.setAttribute('class', 'arrivals text-center');
				newCell.appendChild(document.createTextNode(trip_data[i]['arrival_actual']));

				/*var newCell = newRow.insertCell(1);
				var date = new Date(parseInt(trip_data[i]['scheduled'])*1000);
				var hours = date.getHours();
				var minutes = "0" + date.getMinutes();
				newCell.appendChild(document.createTextNode(hours + ':' + minutes.substr(minutes.length-2)));

				var newCell = newRow.insertCell(2);
				if(trip_data[i]['expected']) {
					var date = new Date(parseInt(trip_data[i]['expected'])*1000);
					var hours = date.getHours();
					var minutes = "0" + date.getMinutes();
				}
				newCell.appendChild(document.createTextNode(hours + ':' + minutes.substr(minutes.length-2)));*/

				var newCell = newRow.insertCell(5);
				newCell.setAttribute('colspan', '2');
				newCell.appendChild(document.createTextNode(trip_data[i]['bus_stop']));
			}
			//$('#table_trip tr').find('td:eq(2),th:eq(2)').show();
			//$('#table_trip tr').find('td:eq(3),th:eq(3)').show();
			//$('#table_trip tr').find('td:eq(4),th:eq(4)').hide();
			//$('#table_trip tr').find('td:eq(5),th:eq(5)').hide();

			updateBusLeg();

			document.getElementById('table_trip_title_route').appendChild(document.createTextNode(route_name));

			if(refresh_table == 0) {
				$('#table_trip .departures').show();
				$('#table_trip .arrivals').hide();

				document.getElementById('table_trip_title_type').appendChild(document.createTextNode('Departures'));


				document.getElementById('table_trip_type').value = 'departures';

				$("html, body").animate({ scrollTop: ($('#table_trip_title').offset().top) }, "slow");

				loadMapByStopName(stop_name, trip_duid, bus_lat, bus_lng);
			}
			else if(refresh_table == 1) {
				if(current_trip_type == 'departures') {
					$('#table_trip .departures').show();
					$('#table_trip .arrivals').hide();
					document.getElementById('table_trip_title_type').appendChild(document.createTextNode('Departures'));
					document.getElementById('table_trip_type').value = 'departures';
				}
				else if(current_trip_type == 'arrivals') {
					$('#table_trip .departures').hide();
					$('#table_trip .arrivals').show();
					document.getElementById('table_trip_title_type').appendChild(document.createTextNode('Arrivals'));
					document.getElementById('table_trip_type').value = 'arrivals';
				}
			}

			intervalTripId = setTimeout(function(){ showTrip(trip_duid, route_name, stop_name, 1); }, 60000);
		});
	}

	function updateBusLeg() {
		var timestamp = getTimestamp();

		var table = document.getElementById('table_trip');
		var rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr').length;
		var trip;
		var previous_time;

		for(var i = rows, row; row = table.rows[i]; i--) { // loop through backwards
			if(i > 0) { // skip <thead>
				for(var j = 0, col; col = row.cells[j]; j++) {
					if(j == 0) {
						var scheduled_time = col.getAttribute('data-time');
						if(i == rows) { // last row
							if(timestamp >= scheduled_time) {
								col.setAttribute('class', 'last_now');
							}
							else {
								col.setAttribute('class', 'last_before');
							}
						}
						else if(i == 1) { // first row
							if(timestamp < scheduled_time) {
								col.setAttribute('class', 'first_before');
							}
							else if(timestamp >= scheduled_time && timestamp >= previous_time) {
								col.setAttribute('class', 'first_after');
							}
							else if(timestamp >= scheduled_time && timestamp < previous_time) {
								col.setAttribute('class', 'first_now');
							}
						}
						else { // every other row
							if(timestamp < scheduled_time) {
								col.setAttribute('class', 'middle_before');
							}
							else if(timestamp >= scheduled_time && timestamp >= previous_time) {
								col.setAttribute('class', 'middle_after');
							}
							else if(timestamp >= scheduled_time && timestamp < previous_time) {
								col.setAttribute('class', 'middle_now');
							}
						}
						var previous_time = col.getAttribute('data-time');
					}
				}
			}
		}
		//intervalTripId = setTimeout(function(){ updateBusLeg(); }, 60000);
	}

	function searchByRoute(refresh) {
		var stop_searching = 0;
		var route_list = [];

		//var depot = ['Dublin (Broadstone Depot)'];

		$("#form-real-time-information-route").empty();
		var select_element = document.getElementById('form-real-time-information-route');
		var option_element = document.createElement('option');
		option_element.setAttribute('value', '');
		option_element.setAttribute('selected', 'selected');
		option_element.appendChild(document.createTextNode('Select Route'));
		select_element.appendChild(option_element);
		document.getElementById('form-real-time-information-route').disabled = true;

		var lastRouteValue_stripped = lastRouteValue.split(' - ['); // strip out bus stop number
		var lastRouteValue_name = '';
		var lastRouteValue_num = '';
		if(lastRouteValue_stripped.length == 1) {
			if(isNaN(lastRouteValue_stripped[0]) == false) {
				lastRouteValue_num = lastRouteValue_stripped[0];
			}
			else {
				lastRouteValue_name = lastRouteValue_stripped[0];
			}
		}
		else if(lastRouteValue_stripped.length > 1) {
			lastRouteValue_name = lastRouteValue_stripped[0];
			lastRouteValue_num = lastRouteValue_stripped[1].substring(0, lastRouteValue_stripped[1].length - 1);
		}

		//console.log('Name: ' + lastRouteValue_name);
		//console.log('Num: ' + lastRouteValue_num);

		for( var key in obj_bus_stop_points['bus_stops'] ) {
			if(stop_searching == 0) {
				if(lastRouteValue_num != '') {
					if(obj_bus_stop_points['bus_stops'][key]['num'] == lastRouteValue_num) {
						stop_searching = 1;
					}
				}
				else if(lastRouteValue_num == '' && lastRouteValue_name != '') {
					if(obj_bus_stop_points['bus_stops'][key]['name'] == lastRouteValue_name) {
						stop_searching = 1;
					}
				}
				//if(obj_bus_stop_points['bus_stops'][key]['name'] == lastRouteValue_stripped || obj_bus_stop_points['bus_stops'][key]['num'] == lastRouteValue_stripped) {
				if(stop_searching == 1) {
					//stop_searching = 1;

					document.getElementById('form-real-time-information-submit').disabled = true;
					$('#form-real-time-information-route-loading').show();

					var latitude_north = parseFloat(obj_bus_stop_points['bus_stops'][key]['lat']) + 0.01;
					var latitude_south = parseFloat(obj_bus_stop_points['bus_stops'][key]['lat']) - 0.01;
					var longitude_east = parseFloat(obj_bus_stop_points['bus_stops'][key]['lng']) + 0.01;
					var longitude_west = parseFloat(obj_bus_stop_points['bus_stops'][key]['lng']) - 0.01;

					var latitude_north_milliarcsecond = Math.round(latitude_north * 3600000);
					var latitude_south_milliarcsecond = Math.round(latitude_south * 3600000);
					var longitude_east_milliarcsecond = Math.round(longitude_east * 3600000);
					var longitude_west_milliarcsecond = Math.round(longitude_west * 3600000);

					var bus_stop_identifier_name = obj_bus_stop_points['bus_stops'][key]['name'];
					var bus_stop_identifier_num = obj_bus_stop_points['bus_stops'][key]['num'];

					duplicate_bus_stop = [];

					var stop_searching_bus_stops = 0;

					$.ajaxSetup({ cache: false });
					$.getJSON('inc/proto/stopPointTdi.php', {
						latitude_north: latitude_north_milliarcsecond,
						latitude_south: latitude_south_milliarcsecond,
						longitude_east: longitude_east_milliarcsecond,
						longitude_west: longitude_west_milliarcsecond
					}, function (bus_stops_detailed) {
						//console.log( Object.keys(bus_stops_detailed.stopPointTdi).length );
						for( var key2 in bus_stops_detailed['stopPointTdi'] ) {
							if(bus_stops_detailed['stopPointTdi'][key2]['long_name'] == bus_stop_identifier_name) {
								//duplicate_bus_stop.push(bus_stops_detailed['stopPointTdi'][key2]['long_name'] + ' - [' + bus_stops_detailed['stopPointTdi'][key2]['code'] + ']');
								duplicate_bus_stop.push(bus_stops_detailed['stopPointTdi'][key2]['code']);
							}
						}
						for( var key2 in bus_stops_detailed['stopPointTdi'] ) {
							//if(stop_searching_bus_stops == 0) {
							if(stop_searching_bus_stops < duplicate_bus_stop.length) {
								//if(bus_stops_detailed['stopPointTdi'][key2]['code'] == bus_stop_identifier_num) {
								if(bus_stops_detailed['stopPointTdi'][key2]['long_name'] == bus_stop_identifier_name) {
									//stop_searching_bus_stops = 1;
									stop_searching_bus_stops = stop_searching_bus_stops + 1;

									/*if(lastRouteValue_num != '') {
										duplicate_bus_stop = []; // if the bus stop number is known, then don't show the user a list of bus stops
									}*/

									$.ajaxSetup({ cache: false });
									$.getJSON('inc/proto/stopPassageTdi.php', {
										//stop_point: obj_bus_stop_points['bus_stops'][key]['duid']
										stop_point: bus_stops_detailed['stopPointTdi'][key2]['duid']
									}, function (passages) {
										//console.log( Object.keys(passages.stopPassageTdi).length );
										passage_data = [];
										for( var key in passages['stopPassageTdi'] ) {
											if(passages['stopPassageTdi'][key]['duid']) {
												if(passages['stopPassageTdi'][key]['route_duid']['duid']) {
													if(passages['stopPassageTdi'][key]['departure_data'] || passages['stopPassageTdi'][key]['arrival_data']) {
														var route_duid = passages['stopPassageTdi'][key]['route_duid']['duid'];
														if($.inArray(route_duid.toString(), route_list) == -1) {
															route_list.push(route_duid.toString());
														}

														var due;
														var due_time;
														var destination;
														var assigned_vehicle;

														if(passages['stopPassageTdi'][key]['vehicle_duid']) {
															assigned_vehicle = passages['stopPassageTdi'][key]['vehicle_duid']['duid'].toString();
														}
														else {
															assigned_vehicle = '0'.toString();
														}

														if(passages['stopPassageTdi'][key]['departure_data']) {
															if(passages['stopPassageTdi'][key]['departure_data']['actual_passage_time_utc']) {
																due = passages['stopPassageTdi'][key]['departure_data']['actual_passage_time_utc'];
																due_time = passages['stopPassageTdi'][key]['departure_data']['actual_passage_time'];
															}
															else {
																due = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time_utc'];
																due_time = passages['stopPassageTdi'][key]['departure_data']['scheduled_passage_time'];
															}

															destination = passages['stopPassageTdi'][key]['departure_data']['multilingual_direction_text']['defaultValue'];

															//if(destination.indexOf('Depot') == -1) {
															//if($.inArray(destination, depot) == -1) {
															if(passages['stopPassageTdi'][key]['departure_data']['service_mode'] != '4') {
																var data = {
																	route_duid: passages['stopPassageTdi'][key]['route_duid']['duid'].toString(),
																	trip_duid: passages['stopPassageTdi'][key]['trip_duid']['duid'].toString(),
																	due: due,
																	due_time: due_time,
																	destination: destination,
																	assigned_vehicle: assigned_vehicle,
																	type: 'departures'
																};

																passage_data.push(data);
															}
														}
														if(passages['stopPassageTdi'][key]['arrival_data']) {
															if(passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time_utc']) {
																due = passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time_utc'];
																due_time = passages['stopPassageTdi'][key]['arrival_data']['actual_passage_time'];
															}
															else {
																due = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time_utc'];
																due_time = passages['stopPassageTdi'][key]['arrival_data']['scheduled_passage_time'];
															}

															destination = passages['stopPassageTdi'][key]['arrival_data']['multilingual_direction_text']['defaultValue'];

															//if(destination.indexOf('Depot') == -1) {
															//if($.inArray(destination, depot) == -1) {
															if(passages['stopPassageTdi'][key]['arrival_data']['service_mode'] != '4') {
																var data = {
																	route_duid: passages['stopPassageTdi'][key]['route_duid']['duid'].toString(),
																	trip_duid: passages['stopPassageTdi'][key]['trip_duid']['duid'].toString(),
																	due: due,
																	due_time: due_time,
																	destination: destination,
																	assigned_vehicle: assigned_vehicle,
																	type: 'arrivals'
																};

																passage_data.push(data);
															}
														}
													}
												}
											}
										}
										updateSearchByRoute(passage_data, select_element, refresh);
										document.getElementById('form-real-time-information-submit').disabled = false;
										$('#form-real-time-information-route-loading').hide();
									});
								}
							}
						}
						if(stop_searching_bus_stops == 0) {
							document.getElementById('form-real-time-information-submit').disabled = false;
							$('#form-real-time-information-route-loading').hide();
						}
					});
				}
			}
		}
	}

	function updateSearchByRoute(passage_data, select_element, refresh) {
		var timestamp = getTimestamp();
		var count = Object.keys(passage_data).length;
		if(count > 0) {

			function compare_route(a,b) {
				if (a.route_num < b.route_num)
					return -1;
				if (a.route_num > b.route_num)
					return 1;
				return 0;
			}

			var route_data = [];

			for(var i = 0; i < count; i++) {
				for( var key in obj_routes['routeTdi'] ) {
					if(obj_routes['routeTdi'][key]['duid'] == passage_data[i]['route_duid']) {
						if(passage_data[i]['due'] >= timestamp) { // only show routes that haven't departed
							var route_num = obj_routes['routeTdi'][key]['short_name'];
							if(route_num == 'GoBe') {
								route_num = '9999999'; // make sure GoBe is shown last
							}
							route_num = route_num.replace(/\D/g,"");
							route_num = parseInt(route_num);

							var name = obj_routes['routeTdi'][key]['short_name'] + ' ' + passage_data[i]['destination'];

							var data = {
								route_duid: passage_data[i]['route_duid'],
								trip_duid: passage_data[i]['trip_duid'],
								due: passage_data[i]['due'],
								due_time: passage_data[i]['due_time'],
								destination: passage_data[i]['destination'],
								assigned_vehicle: passage_data[i]['assigned_vehicle'],
								route_num: route_num,
								name: name
							};

							var inside = 0;
							for( var key2 in route_data ) {
								//if(route_data[key2]['route_duid'] == passage_data[i]['route_duid']) {
								if(route_data[key2]['name'] == name) {
									inside = 1;
								}
							}
							if(inside == 0) {
								route_data.push(data);
							}
						}
					}
				}
			}

			route_data.sort(compare_route);

			var count = Object.keys(route_data).length;
			var route_deposit = [];
			var previous_route;

			function create_options() {
				function compare_deposit(a,b) {
					if (a.destination < b.destination)
						return -1;
					if (a.destination > b.destination)
						return 1;
					return 0;
				}
				route_deposit.sort(compare_deposit);

				var route_deposit_count = Object.keys(route_deposit).length;

				for(var n = 0; n < route_deposit_count; n++) {
					var option_element = document.createElement('option');
					option_element.setAttribute('value', route_deposit[n]['trip_duid']);
					option_element.appendChild(document.createTextNode(route_deposit[n]['name']));
					select_element.appendChild(option_element);
				}
			}

			for(var i = 0; i < count; i++) {
				if(i > 0) {
					if(route_data[i]['route_num'] != previous_route) {
						create_options();
						route_deposit = [];
					}
				}
				var data = {
					route_duid: route_data[i]['route_duid'],
					trip_duid: route_data[i]['trip_duid'],
					due: route_data[i]['due'],
					due_time: route_data[i]['due_time'],
					destination: route_data[i]['destination'],
					assigned_vehicle: route_data[i]['assigned_vehicle'],
					route_num: route_data[i]['route_num'],
					name: route_data[i]['name']
				};
				route_deposit.push(data);

				previous_route = route_data[i]['route_num'];

				/*var option_element = document.createElement('option');
				option_element.setAttribute('value', route_data[i]['trip_duid']);
				option_element.appendChild(document.createTextNode(route_data[i]['name']));
				select_element.appendChild(option_element);*/
			}

			create_options();

			document.getElementById('form-real-time-information-route').disabled = false;

			if(refresh == '1') {
				searchByStopName();
			}
		}
		else {
			document.getElementById('form-real-time-information-submit').disabled = false;
			$('#form-real-time-information-route-loading').hide();
		}
	}

	function searchByMap() {

		if(document.getElementById('map_canvas').style.display == 'block') {
			resetMarkers();
		}

		var myOptions = {
			zoom: 7,
			scrollwheel: false,
			center: new google.maps.LatLng(53.398645, -7.711116),
			mapTypeId: google.maps.MapTypeId.ROADMAP
		};

		document.getElementById('real-time-information-intro').style.display = 'none';
		document.getElementById('table_trip_container').style.display = 'none';
		document.getElementById('table_routes_container').style.display = 'none';
		document.getElementById('table_routes_refresh').style.display = 'none';
		//document.getElementById('table_routes_type').style.display = 'none';
		document.getElementById('map_canvas').style.display = 'block';
		document.getElementById('map-legends').style.display = 'block';

		map = new google.maps.Map(document.getElementById('map_canvas'), myOptions);

		if(geo_location == 1) {
			google.maps.event.addListenerOnce(map, 'idle', function() {
				if(navigator.geolocation) {
					navigator.geolocation.getCurrentPosition(function(position) {
						user_lat = position.coords.latitude;
						user_lng = position.coords.longitude;

						//user_lat = 53.349785;
						//user_lng = -6.251856;

						bus_stop_markers_displayed = 1;

						userMarker(user_lat, user_lng);
						loadBusStops();
					}, function() {
						// no data
					});
				}
			});
		}

		google.maps.event.addListener(map, 'zoom_changed', function() {
			if(bus_stop_markers_displayed == 0) {
				var zoom = map.getZoom();
				if(zoom >= 14) {
					loadBusStops();
					bus_stop_markers_displayed = 1;
				}
			}
		});

		$("html, body").animate({ scrollTop: ($('#map_canvas').offset().top) }, "slow");

		if(geo_location == 0) {
			setTimeout(function(){ $('#map-alert').foundation('reveal', 'open'); }, 1000);
		}
	}

	function resetMarkers() {

		buses_moved_yet = 0;
		startLocation = [];
		endLocation = [];
		startLoc = [];
		endLoc = [];
		bus_stop_markers_displayed = 0;

		if(intervalId != 0) {
			clearInterval(intervalId); // stop refreshing buses
			intervalId = 0;
		}

		if(intervalTripId != 0) {
			clearTimeout(intervalTripId); // stop refreshing bus for current trip table
			intervalTripId = 0;
		}

		for(var i = 0; i < markers.length; i++) {
			markers[i].setMap(null);
		}

		for(var i = 0; i < markers_bus_stop_medium.length; i++) {
			markers_bus_stop_medium[i].setMap(null);
		}

		for(var i = 0; i < markers_bus_stop_fine.length; i++) {
			markers_bus_stop_fine[i].setMap(null);
		}

		markers = [];
		markers_bus_stop_medium = [];
		markers_bus_stop_fine = [];
	}

	function userMarker(user_lat, user_lng) {
		var myLatLng = new google.maps.LatLng(user_lat, user_lng);
		map.setCenter(myLatLng);
		map.setZoom(16);

		var image = {
			url: 'img/you_are_here.png',
			size: new google.maps.Size(62, 62),
			origin: new google.maps.Point(0,0),
			anchor: new google.maps.Point(31, 31)
		};

		var shape = {
			coords: [30, 0, 54, 10, 61, 30, 54, 51, 31, 61, 8, 51, 0, 30, 9, 10],
			type: 'poly'
		};

		var myLatlng = new google.maps.LatLng(user_lat, user_lng);

		var marker = new google.maps.Marker({
			position: myLatlng,
			map: map,
			icon: image,
			shape: shape,
			title: 'You are here',
			zIndex: 3
		});
	}

	function viewRealtimeInfo(bus_stop) {
		duplicate_bus_stop = [];
		searchByRoute_stop = 1;
		bus_stop = bus_stop.replace('*', "'");
		bus_stop = bus_stop.replace('*', "'");
		document.getElementById('form-real-time-information-stop').value = bus_stop;
	}

	function loadBusStops() {
		var bounds = map.getBounds();
		var southWest = bounds.getSouthWest();
		var northEast = bounds.getNorthEast();

		// increase boundary box to include surrounding bus stops
		var latitude_north = northEast.lat() + 0.05;
		var latitude_south = southWest.lat() - 0.05;
		var longitude_east = northEast.lng() + 0.05;
		var longitude_west = southWest.lng() - 0.05;

		var latitude_north_milliarcsecond = Math.round(latitude_north * 3600000);
		var latitude_south_milliarcsecond = Math.round(latitude_south * 3600000);
		var longitude_east_milliarcsecond = Math.round(longitude_east * 3600000);
		var longitude_west_milliarcsecond = Math.round(longitude_west * 3600000);

		$.ajaxSetup({ cache: false });
		$.getJSON('inc/proto/stopTdi.php', {
			latitude_north: latitude_north_milliarcsecond,
			latitude_south: latitude_south_milliarcsecond,
			longitude_east: longitude_east_milliarcsecond,
			longitude_west: longitude_west_milliarcsecond
		}, function (bus_stops) {
			//console.log( Object.keys(bus_stops.stopTdi).length );
			for( var key in bus_stops['stopTdi'] ) {
				if(bus_stops['stopTdi'][key]['long_name']) {
					var image = {
						url: 'img/bus_stop_icon.png',
						size: new google.maps.Size(24, 34),
						origin: new google.maps.Point(0,0),
						anchor: new google.maps.Point(12, 34)
					};

					var shape = {
						coords: [11, 0, 19, 4, 22, 12, 18, 23, 11, 32, 4, 23, 0, 12, 3, 4],
						type: 'poly'
					};

					var bus_stop_lat = bus_stops['stopTdi'][key]['latitude'] / 3600000;
					var bus_stop_lng = bus_stops['stopTdi'][key]['longitude'] / 3600000;

					var myLatlng = new google.maps.LatLng(bus_stop_lat, bus_stop_lng);

					var marker = new google.maps.Marker({
						position: myLatlng,
						map: map,
						icon: image,
						shape: shape,
						visible: false,
						title: bus_stops['stopTdi'][key]['long_name'],
						duid: bus_stops['stopTdi'][key]['duid'],
						zIndex: 1
					});

					markers_bus_stop_medium.push(marker);

					google.maps.event.addListener(marker, 'click', function() {

						map.setCenter(this.position);
						map.setZoom(19);
					});
				}
			}
		});

		$.ajaxSetup({ cache: false });
		$.getJSON('inc/proto/stopPointTdi.php', {
			latitude_north: latitude_north_milliarcsecond,
			latitude_south: latitude_south_milliarcsecond,
			longitude_east: longitude_east_milliarcsecond,
			longitude_west: longitude_west_milliarcsecond
		}, function (bus_stops_detailed) {
			//console.log( Object.keys(bus_stops_detailed.stopPointTdi).length );
			for( var key in bus_stops_detailed['stopPointTdi'] ) {
				if(bus_stops_detailed['stopPointTdi'][key]['long_name']) {
					var image = {
						url: 'img/bus_stop_icon.png',
						size: new google.maps.Size(24, 34),
						origin: new google.maps.Point(0,0),
						anchor: new google.maps.Point(12, 34)
					};

					var shape = {
						coords: [11, 0, 19, 4, 22, 12, 18, 23, 11, 32, 4, 23, 0, 12, 3, 4],
						type: 'poly'
					};

					var bus_stop_lat = bus_stops_detailed['stopPointTdi'][key]['latitude'] / 3600000;
					var bus_stop_lng = bus_stops_detailed['stopPointTdi'][key]['longitude'] / 3600000;

					var myLatlng = new google.maps.LatLng(bus_stop_lat, bus_stop_lng);

					var marker = new google.maps.Marker({
						position: myLatlng,
						map: map,
						icon: image,
						shape: shape,
						visible: false,
						title: bus_stops_detailed['stopPointTdi'][key]['long_name'],
						zIndex: 1
					});

					markers_bus_stop_fine.push(marker);

					google.maps.event.addListener(marker, 'click', function() {

						var onclick = this.title;
						onclick = onclick.replace("'", '*');
						onclick = onclick.replace("'", '*');

						var markerhtml = '<h2>Bus Stop</h2><p>' + this.title + '</p><input type="button" value="View Realtime Info" class="button tiny radius" onclick=\'viewRealtimeInfo("'+onclick+'");return false;\'>';

						if(infowindow) { // close all windows before opening another
							infowindow.close();
						}

						infowindow = new google.maps.InfoWindow({
							content: markerhtml,
							position: this.position,
							//maxWidth: 500,
							pixelOffset: new google.maps.Size(-1, -35)
						});
						infowindow.open(map);
					});
				}
			}

			zoom_type = 1;

			var zoom = map.getZoom();
			hideDisplayBusMarkers(zoom);

			google.maps.event.addListener(map, 'zoom_changed', function() {
				var zoom = map.getZoom();
				hideDisplayBusMarkers(zoom);
			});

			loadBuses();
		});
	}

	function loadBuses() {
		current_zoom = map.getZoom();

		if(current_zoom >= 14) { // only retrieve buses if zoomed in
			var bounds = map.getBounds();
			var southWest = bounds.getSouthWest();
			var northEast = bounds.getNorthEast();

			// increase boundary box to include surrounding buses
			var latitude_north = northEast.lat() + 0.05;
			var latitude_south = southWest.lat() - 0.05;
			var longitude_east = northEast.lng() + 0.05;
			var longitude_west = southWest.lng() - 0.05;

			/*var latitude_north = northEast.lat();
			var latitude_south = southWest.lat();
			var longitude_east = northEast.lng();
			var longitude_west = southWest.lng();*/

			var latitude_north_milliarcsecond = Math.round(latitude_north * 3600000);
			var latitude_south_milliarcsecond = Math.round(latitude_south * 3600000);
			var longitude_east_milliarcsecond = Math.round(longitude_east * 3600000);
			var longitude_west_milliarcsecond = Math.round(longitude_west * 3600000);

			$.ajaxSetup({ cache: false });
			$.getJSON('inc/proto/vehicleTdi.php', {
				latitude_north: latitude_north_milliarcsecond,
				latitude_south: latitude_south_milliarcsecond,
				longitude_east: longitude_east_milliarcsecond,
				longitude_west: longitude_west_milliarcsecond
			}, function (buses) {
				//console.log( Object.keys(buses.vehicleTdi).length );
				//startLoc = [];
				//endLoc = [];
				//var i = 0;
				for( var key in buses['vehicleTdi'] ) {
					if(buses['vehicleTdi'][key]['duid']) {
						var bus_stop_lat = buses['vehicleTdi'][key]['latitude'] / 3600000;
						var bus_stop_lng = buses['vehicleTdi'][key]['longitude'] / 3600000;

						var bus_duid = buses['vehicleTdi'][key]['duid'];

						if(buses_moved_yet == 0) {
							var image = {
								url: 'img/bus_icon.png',
								size: new google.maps.Size(36, 52),
								origin: new google.maps.Point(0,0),
								anchor: new google.maps.Point(18, 52)
							};

							var shape = {
								coords: [18, 1, 30, 6, 35, 19, 28, 36, 17, 50, 6, 36, 0, 19, 5, 6],
								type: 'poly'
							};

							var myLatlng = new google.maps.LatLng(bus_stop_lat, bus_stop_lng);

							var marker = new google.maps.Marker({
								position: myLatlng,
								map: map,
								icon: image,
								shape: shape,
								//title: buses['vehicleTdi'][key]['duid'],
								zIndex: 2
							});

							markers.push(marker);
						}

						if(startLoc['bus_'+bus_duid]) {
							startLoc['bus_'+bus_duid] = endLoc['bus_'+bus_duid];
						}
						else {
							startLoc['bus_'+bus_duid] = bus_stop_lat + ', ' + bus_stop_lng;
						}
						endLoc['bus_'+bus_duid] = bus_stop_lat + ', ' + bus_stop_lng;
					}
				}

				if(buses_moved_yet == 0) {
					intervalId = setInterval(function(){ loadBuses(); }, 60000);
				}

				buses_moved_yet = 1;

				current_center = map.getCenter();
				current_zoom = map.getZoom();

				hideDisplayBuses(current_zoom);

				google.maps.event.addListener(map, 'zoom_changed', function() {
					var zoom = map.getZoom(); // re-receive zoom otherwise this listener won't have acces to it
					hideDisplayBuses(zoom);
				});

				setTimeout(function(){ setRoutes(0, 3); }, 5000);
				setTimeout(function(){ setRoutes(3, 6); }, 10000);
				setTimeout(function(){ setRoutes(6, 9); }, 15000);
				setTimeout(function(){ setRoutes(9, 12); }, 20000);
				setTimeout(function(){ setRoutes(12, 15); }, 25000);
				setTimeout(function(){ setRoutes(15, 18); }, 30000);
				setTimeout(function(){ setRoutes(18, 21); }, 35000);
				setTimeout(function(){ setRoutes(21, 24); }, 40000);
				setTimeout(function(){ setRoutes(24, 27); }, 45000);
				setTimeout(function(){ setRoutes(27, 30); }, 50000);
				setTimeout(function(){ setRoutes(30, 33); }, 55000);
			});
		}
	}

	function hideDisplayBusMarkers(zoom) {
		// iterate over markers and call setVisible
		if(zoom < 14 && zoom_type == 1) {
			for(var i = 0; i < markers_bus_stop_medium.length; i++) {
				markers_bus_stop_medium[i].setVisible(false);
			}
			for(var i = 0; i < markers_bus_stop_fine.length; i++) {
				markers_bus_stop_fine[i].setVisible(false);
			}
		}
		else if(zoom < 14 && zoom_type == 2) {
			for(var i = 0; i < markers_bus_stop_medium.length; i++) {
				markers_bus_stop_medium[i].setVisible(true);
			}
			for(var i = 0; i < markers_bus_stop_fine.length; i++) {
				markers_bus_stop_fine[i].setVisible(false);
			}
		}
		else if(zoom >= 14 && zoom <= 18) {
			for(var i = 0; i < markers_bus_stop_fine.length; i++) {
				markers_bus_stop_fine[i].setVisible(false);
			}
			for(var i = 0; i < markers_bus_stop_medium.length; i++) {
				markers_bus_stop_medium[i].setVisible(true);
			}
		}
		else if(zoom > 18) {
			for(var i = 0; i < markers_bus_stop_medium.length; i++) {
				markers_bus_stop_medium[i].setVisible(false);
			}
			for(var i = 0; i < markers_bus_stop_fine.length; i++) {
				markers_bus_stop_fine[i].setVisible(true);
			}
		}
	}

	function hideDisplayBuses(zoom) {
		// iterate over markers and call setVisible
		if(zoom < 14 && zoom_type == 1) {
			for(var i = 0; i < markers.length; i++) {
				markers[i].setVisible(false);
			}
		}
		else if(zoom < 14 && zoom_type == 2) {
			for(var i = 0; i < markers.length; i++) {
				markers[i].setVisible(true);
			}
		}
		else if(zoom >= 14) {
			for(var i = 0; i < markers.length; i++) {
				markers[i].setVisible(true);
			}
		}
	}



function setAllMap(map) {
for (var i = 0; i < markers.length; i++) {
	markers[i].setMap(map);
}
}

function clearMarkers() {
setAllMap(null);
}

function deleteMarkers() {
clearMarkers();
markers = [];
}



function createMarker(latlng, label, html) {

	var image = {
		url: 'img/bus_icon.png',
		size: new google.maps.Size(36, 52),
		origin: new google.maps.Point(0,0),
		anchor: new google.maps.Point(18, 52)
	};

	var shape = {
		coords: [18, 1, 30, 6, 35, 19, 28, 36, 17, 50, 6, 36, 0, 19, 5, 6],
		type: 'poly'
	};

	var marker = new google.maps.Marker({
		position: latlng,
		map: map,
		icon: image,
		shape: shape,
		//title: label,
		zIndex: 2
	});

	markers.push(marker);

	return marker;
}

function setRoutes(skip, stop){

	current_center = map.getCenter();
	current_zoom = map.getZoom();

	var myLatLng = new google.maps.LatLng(current_center.lat(), current_center.lng());
	map.setCenter(myLatLng);
	map.setZoom(current_zoom);

	var directionsDisplay = new Array();

	//for (var i=0; i< startLoc.length; i++){
	var i = 0;
	for( var key in startLoc ) {

		if(i >= skip && i < stop) {
			if(startLoc[key] != endLoc[key]) {
				var rendererOptions = {
					map: map,
					suppressMarkers: true,
					suppressPolylines: true,
					preserveViewport: true
				}
				directionsService = new google.maps.DirectionsService();

				var travelMode = google.maps.DirectionsTravelMode.DRIVING;

				var request = {
					origin: startLoc[key],
					destination: endLoc[key],
					travelMode: travelMode
				};

				directionsService.route(request,makeRouteCallback(i,directionsDisplay[i]));
			}
		}

		i = i + 1;
	}


	function makeRouteCallback(routeNum,disp){
		/*if (polyline[routeNum] && (polyline[routeNum].getMap() != null)) {
		 startAnimation(routeNum);
		 return;
		}*/
		return function(response, status){

		  if (status == google.maps.DirectionsStatus.OK){

			  console.log('routeNum = ' + routeNum);

			var bounds = new google.maps.LatLngBounds();
			var route = response.routes[0];
			startLocation[routeNum] = new Object();
			endLocation[routeNum] = new Object();


			polyline[routeNum] = new google.maps.Polyline({
			path: [],
			strokeColor: '#FFFF00',
			strokeOpacity: 0.00001,
			fillOpacity: 0.00001,
			strokeWeight: 0,
			visible: false
			});

			poly2[routeNum] = new google.maps.Polyline({
			path: [],
			strokeColor: '#FFFF00',
			strokeOpacity: 0.00001,
			fillOpacity: 0.00001,
			strokeWeight: 0,
			visible: false
			});


			// For each route, display summary information.
			var path = response.routes[0].overview_path;
			var legs = response.routes[0].legs;


			disp = new google.maps.DirectionsRenderer(rendererOptions);
			disp.setMap(map);
			disp.setDirections(response);

			//deleteMarkers();


			//Markers
			for (i=0;i<legs.length;i++) {
			  if (i == 0) {
				startLocation[routeNum].latlng = legs[i].start_location;
				startLocation[routeNum].address = legs[i].start_address;
				// marker = google.maps.Marker({map:map,position: startLocation.latlng});
				//marker[routeNum] = createMarker(legs[i].start_location,"start",legs[i].start_address,"green");

				//marker[routeNum] = createMarker(legs[i].start_location,"Bus",legs[i].start_address,"green");
				marker[routeNum] = markers[routeNum];
			  }
			  endLocation[routeNum].latlng = legs[i].end_location;
			  endLocation[routeNum].address = legs[i].end_address;
			  var steps = legs[i].steps;

			  for (j=0;j<steps.length;j++) {
				var nextSegment = steps[j].path;
				var nextSegment = steps[j].path;

				for (k=0;k<nextSegment.length;k++) {
					polyline[routeNum].getPath().push(nextSegment[k]);
					//bounds.extend(nextSegment[k]);
				}

			  }
			}

		 }

		if (typeof polyline[routeNum] != 'undefined') {
			console.log(routeNum + ' = good');
		}
		else {
			console.log(routeNum + ' = bad');
		}

		//if(routeNum != 10) {
		 polyline[routeNum].setMap(map);
		//}
		 //map.fitBounds(bounds);
		 startAnimation(routeNum);

	} // else alert("Directions request failed: "+status);

}

}

	var lastVertex = 1;
	var stepnum=0;
	var step = 50; // 5; // metres
	var tick = 200; // milliseconds
	var eol= [];
//----------------------------------------------------------------------
 function updatePoly(i,d) {
 // Spawn a new polyline every 20 vertices, because updating a 100-vertex poly is too slow
	if (poly2[i].getPath().getLength() > 20) {
		  poly2[i]=new google.maps.Polyline([polyline[i].getPath().getAt(lastVertex-1)]);
		  // map.addOverlay(poly2)
		}

	if (polyline[i].GetIndexAtDistance(d) < lastVertex+2) {
		if (poly2[i].getPath().getLength()>1) {
			poly2[i].getPath().removeAt(poly2[i].getPath().getLength()-1)
		}
			poly2[i].getPath().insertAt(poly2[i].getPath().getLength(),polyline[i].GetPointAtDistance(d));
	} else {
		poly2[i].getPath().insertAt(poly2[i].getPath().getLength(),endLocation[i].latlng);
	}
 }
//----------------------------------------------------------------------------

function animate(index,d) {
 if (d>eol[index]) {

	  marker[index].setPosition(endLocation[index].latlng);
	  return;
 }
	var p = polyline[index].GetPointAtDistance(d);

	//map.panTo(p);
	marker[index].setPosition(p);
	updatePoly(index,d);
	timerHandle[index] = setTimeout("animate("+index+","+(d+step)+")", tick);
}

//-------------------------------------------------------------------------

function startAnimation(index) {
		if (timerHandle[index]) clearTimeout(timerHandle[index]);
		eol[index]=polyline[index].Distance();
		map.setCenter(polyline[index].getPath().getAt(0));

		poly2[index] = new google.maps.Polyline({path: [polyline[index].getPath().getAt(0)], strokeColor:"#FFFF00", strokeWeight:0, strokeOpacity: 0.00001, fillOpacity: 0.00001, visible: false});

		timerHandle[index] = setTimeout("animate("+index+",50)",2000);  // Allow time for the initial map display

		// stop google maps from moving to an animated bus and stay put
		var myLatLng = new google.maps.LatLng(current_center.lat(), current_center.lng());
		map.setCenter(myLatLng);
		map.setZoom(current_zoom);
}

//----------------------------------------------------------------------------
