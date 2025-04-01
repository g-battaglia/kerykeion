drop table if exists geoname;
create table geoname (
    geonameid integer primary key,
    name varchar(200),
    asciiname varchar(200),
    alternatenames varchar(10000),
    latitude varchar(200),
    longitude varchar(200),
    feature_class char(1),
    feature_code varchar(10),
    country_code char(2),
    cc2 varchar(200),
    admin1_code varchar(20),
    admin2_code varchar(80),
    admin3_code varchar(20),
    admin4_code varchar(20),
    population integer,
    elevation integer,
    dem integer,
    timezone varchar(40),
    modification_date date
);

create index idx_country_code ON geoname (country_code);

.mode tabs
.import allCountries.txt geoname
