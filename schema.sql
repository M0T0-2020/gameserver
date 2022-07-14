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
  `member1` bigint DEFAULT NULL,
  `member2` bigint DEFAULT NULL,
  `member3` bigint DEFAULT NULL,
  `member4` bigint DEFAULT NULL,
  `owner` bigint DEFAULT NULL,
  PRIMARY KEY (`room_id`),
  UNIQUE KEY `room_id` (`room_id`)
);

DROP TABLE IF EXISTS `result`;
CREATE TABLE `result` (
  `room_id` bigint NOT NULL,
  `member1` bigint DEFAULT NULL,
  `member2` bigint DEFAULT NULL,
  `member3` bigint DEFAULT NULL,
  `member4` bigint DEFAULT NULL,
  `member_num` int DEFAULT NULL,
  `judge_count_list1` varchar(255) DEFAULT NULL,
  `judge_count_list2` varchar(255) DEFAULT NULL,
  `judge_count_list3` varchar(255) DEFAULT NULL,
  `judge_count_list4` varchar(255) DEFAULT NULL,
  `score1` int DEFAULT NULL,
  `score2` int DEFAULT NULL,
  `score3` int DEFAULT NULL,
  `score4` int DEFAULT NULL,
  PRIMARY KEY (`room_id`),
  UNIQUE KEY `room_id` (`room_id`)

);
