create database busboy
        encoding = 'utf8';

create table passage_responses (
        response jsonb,
        route_id varchar(30),
        direction smallint,
        vehicle_id varchar(30),
        last_modified timestamp,
        trip_id varchar(30),
        congestion_level smallint,
        accuracy_level smallint,
        status smallint,
        is_accessible boolean,
        latitude integer,
        longitude integer,
        bearing smallint,
        pattern_id varchar(30),
        has_bike_rack boolean,
        category smallint,
        primary key (trip_id, last_modified)
);
