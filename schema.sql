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
  `select_difficulty` int DEFAULT NULL,
  `status` int DEFAULT NULL,
  `owner` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`room_id`),
  UNIQUE KEY `room_id` (`room_id`)

);

DROP TABLE IF EXISTS `room_member`;
CREATE TABLE `room_member` (
  `room_id` bigint NOT NULL,
  `user_id` bigint NOT NULL AUTO_INCREMENT,
  `judge_count_list` varchar(255) DEFAULT NULL,
  `score` int DEFAULT NULL,
  PRIMARY KEY (`room_id`, `user_id`),
  UNIQUE KEY `room_id` (`room_id`),
  UNIQUE KEY `user_id` (`user_id`)
);
