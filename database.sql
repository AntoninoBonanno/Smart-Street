CREATE DATABASE street_smart;
use street_smart;

CREATE TABLE `street_smart`.`streets` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `ip_address` VARCHAR(45) NOT NULL,
  `length` INT(10) UNSIGNED NOT NULL DEFAULT 100,
  `available` TINYINT NULL DEFAULT 1,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  
  PRIMARY KEY (`id`)) ENGINE=INNODB;

CREATE TABLE `street_smart`.`routes` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `car_id` VARCHAR(45) NOT NULL,
  `car_ip` VARCHAR(45) NOT NULL,
  `route_list` VARCHAR(255) NOT NULL,   /*JSON*/
  `current_index` INT UNSIGNED NOT NULL DEFAULT 0,
  `current_street_position` INT UNSIGNED NULL DEFAULT NULL,
  `destination` INT UNSIGNED, 
  `finished_at` DATETIME NULL DEFAULT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
    CONSTRAINT `destination_street_fk`
    FOREIGN KEY (`destination`)
    REFERENCES `street_smart`.`streets` (`id`)
) ENGINE=INNODB;

