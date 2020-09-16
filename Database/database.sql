CREATE DATABASE street_smart;
use street_smart;

CREATE TABLE `street_smart`.`streets` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `ip_address` VARCHAR(45) NOT NULL,
  `length` INT(10) UNSIGNED NOT NULL DEFAULT 100,
  PRIMARY KEY (`id`));

