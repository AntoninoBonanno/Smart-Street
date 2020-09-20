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

INSERT INTO `streets` (`name`, `ip_address`, `length`) VALUES ('Strada1', '127.0.0.1:8001', '100');
INSERT INTO `streets` (`name`, `ip_address`, `length`) VALUES ('Strada2', '127.0.0.1:8002', '100');
INSERT INTO `streets` (`name`, `ip_address`, `length`) VALUES ('Strada3', '127.0.0.1:8003', '100');
INSERT INTO `streets` (`name`, `ip_address`, `length`) VALUES ('Strada4', '127.0.0.1:8004', '100');
INSERT INTO `streets` (`name`, `ip_address`, `length`) VALUES ('Strada5', '127.0.0.1:8005', '100');
INSERT INTO `streets` (`name`, `ip_address`, `length`) VALUES ('Strada6', '127.0.0.1:8006', '100');