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
  `room_id` bigint NOT NULL AUTO_INCREMENT,
  `live_id` int DEFAULT NULL,
  `status` int DEFAULT NULL,
  `owner` bigint DEFAULT NULL,
  PRIMARY KEY (`room_id`)
);

DROP TABLE IF EXISTS `member`;
CREATE TABLE `member` (
  `room_id` bigint NOT NULL,
  `member_id` bigint NOT NULL,
  `difficulty` int DEFAULT NULL,
  `judge_count` varchar(255) DEFAULT NULL,
  `score` int DEFAULT NULL,
  PRIMARY KEY (`room_id`, `member_id`)

);
