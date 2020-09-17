CREATE DATABASE street_smart;
use street_smart;

CREATE TABLE `street_smart`.`streets` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `ip_address` VARCHAR(45) NOT NULL,
  `length` INT(10) UNSIGNED NOT NULL DEFAULT 100,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  
  PRIMARY KEY (`id`)) ENGINE=INNODB;

CREATE TABLE `street_smart`.`routes` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `car_id` VARCHAR(45) NOT NULL,
  `car_ip` VARCHAR(45) NOT NULL,
  `current_street` INT UNSIGNED NULL DEFAULT NULL,
  `current_street_position` INT UNSIGNED NULL DEFAULT NULL,
  `route_list` JSON NOT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `current_street_fk`
    FOREIGN KEY (`current_street`)
    REFERENCES `street_smart`.`streets` (`id`)
) ENGINE=INNODB;

