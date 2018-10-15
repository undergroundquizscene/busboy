create database busboy
        encoding = 'utf8';

create table passage_responses (
        response jsonb,
        last_modified timestamp,
        passage_id varchar(30),
        primary key (passage_id, last_modified)
);
