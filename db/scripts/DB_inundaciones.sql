CREATE DATABASE inundaciones_db;

use inundaciones_db;

create table atlas_inundaciones(
id int AUTO_INCREMENT primary key, 
cvegeo varchar(20),
alcaldia varchar(100),
riesgo varchar (50),
coordenadas varchar (100),
poligono JSON,
area_m2 DECIMAL (15,2),
perimetro_m DECIMAL(15, 2),
descripcion TEXT,
fuente TEXT
);
show tables;

select * from atlas_inundaciones;
drop table clima;
create table clima(
id int AUTO_INCREMENT primary key,
fecha datetime not null,
alcaldia varchar(100) not null,
lluvia_mm DECIMAL (5,2),
prob_lluvia DECIMAL (5,2),
temperatura DECIMAL(5,2),
humedad decimal (5,2),
presion DECIMAL (7,2),
fuente varchar (100)
);

select * from clima;
