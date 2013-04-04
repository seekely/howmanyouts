
CREATE TABLE game (
	
	data			BLOB		DEFAULT NULL,
	completed		INTEGER		DEFAULT 0 NOT NULL,
	score			INTEGER		DEFAULT 0 NOT NULL,
	name			TEXT		DEFAULT 'Anon' NOT NULL,
	time_start		INTEGER		NOT NULL,
	time_completed	INTEGER		DEFAULT NULL
);

CREATE INDEX idx_score ON game(time_completed, score);


CREATE TABLE hiscores (
	
	game_id			INTEGER		NOT NULL,
	period			INTEGER		NOT NULL DEFAULT 0,

	PRIMARY KEY(game_id, period)
);
