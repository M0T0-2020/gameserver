DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `token` varchar(255) DEFAULT NULL,
  `leader_card_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`)
);

DROP TABLE IF EXISTS `room`;
CREATE TABLE `room` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `room_id` varchar(255) DEFAULT NULL,
  `live_id` int DEFAULT NULL,
  `select_difficulity` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `room_id` (`room_id`)
);

DROP TABLE IF EXISTS `room_member`;
CREATE TABLE `room_member` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `room_id` varchar(255) DEFAULT NULL,
  `member1` varchar(255) DEFAULT NULL,
  `member2` varchar(255) DEFAULT NULL,
  `member3` varchar(255) DEFAULT NULL,
  `member4` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `room_id` (`room_id`),
  UNIQUE KEY `member1` (`member1`),
  UNIQUE KEY `member2` (`member2`),
  UNIQUE KEY `member3` (`member3`),
  UNIQUE KEY `member4` (`member4`)
);
