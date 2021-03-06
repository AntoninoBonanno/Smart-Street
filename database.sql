CREATE DATABASE street_smart;
use street_smart;

CREATE TABLE `street_smart`.`streets` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `ip_address` VARCHAR(45) NOT NULL UNIQUE,
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
  `current_index` INT NOT NULL DEFAULT -1,
  `current_speed` INT NOT NULL DEFAULT 0,
  `current_street_position` FLOAT UNSIGNED NULL DEFAULT 0.0,
  `destination` INT UNSIGNED, 
  `connected` TINYINT NOT NULL DEFAULT 0,
  `finished_at` DATETIME NULL DEFAULT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
    CONSTRAINT `destination_street_fk`
    FOREIGN KEY (`destination`)
    REFERENCES `street_smart`.`streets` (`id`)
) ENGINE=INNODB;

CREATE TABLE `street_smart`.`signals` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `street_id` INT UNSIGNED NOT NULL,
  `name` VARCHAR(45) NOT NULL,
  `position` FLOAT UNSIGNED NOT NULL DEFAULT 0.0,
  `action` VARCHAR(45) NULL DEFAULT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `signal_street_fk`
    FOREIGN KEY (`street_id`)
    REFERENCES `street_smart`.`streets` (`id`)
)ENGINE=INNODB;