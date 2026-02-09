-- skyhook-backend/schema.sql
-- Ja, chatgpt hat das generiert. Aber es ist eine solide Basis, die man natürlich an Bedürfnisse anpassen kann.

-- =========================
-- Auth: Users / Roles
-- =========================

CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL,

  -- optional, aber in der Praxis fast immer sinnvoll:
  email VARCHAR(255) NULL,
  password_hash VARCHAR(255) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,

  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uq_users_username (username),
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS roles (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(64) NOT NULL,
  description VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uq_roles_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS user_roles (
  user_id BIGINT UNSIGNED NOT NULL,
  role_id BIGINT UNSIGNED NOT NULL,
  assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (user_id, role_id),
  KEY idx_user_roles_user_id (user_id),
  KEY idx_user_roles_role_id (role_id),

  CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =========================
-- Telemetry: Sensors / Variables / Measurements
-- =========================

CREATE TABLE IF NOT EXISTS sensors (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(128) NOT NULL,
  description VARCHAR(255) NULL,

  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uq_sensors_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS variables (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- technischer Schlüssel, gut für API/Frontend: "altitude_m", "gps_fix", ...
  `key` VARCHAR(64) NOT NULL,
  name VARCHAR(128) NOT NULL,
  unit VARCHAR(32) NULL,

  -- Erwarteter Datentyp der Variable (passt zu measurements.value_type)
  data_type ENUM('num','int','bool','text','json','blob') NOT NULL DEFAULT 'num',

  description VARCHAR(255) NULL,

  PRIMARY KEY (id),
  UNIQUE KEY uq_variables_key (`key`),
  KEY idx_variables_data_type (data_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS measurements (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- historischer Messzeitpunkt (Unix ms)
  ts BIGINT UNSIGNED NOT NULL,

  sensor_id BIGINT UNSIGNED NOT NULL,
  variable_id BIGINT UNSIGNED NOT NULL,

  -- welches value_* Feld ist gültig?
  value_type ENUM('num','int','bool','text','json','blob') NOT NULL,

  -- typisierte Value-Spalten (genau 1 davon sollte gesetzt sein)
  value_num DOUBLE NULL,
  value_int BIGINT NULL,
  value_bool TINYINT(1) NULL,
  value_text TEXT NULL,
  value_json JSON NULL,
  value_blob LONGBLOB NULL,

  PRIMARY KEY (id),

  -- typische Zeitreihen-Indizes
  KEY idx_measurements_ts (ts),
  KEY idx_measurements_sensor_var_ts (sensor_id, variable_id, ts),
  KEY idx_measurements_var_ts (variable_id, ts),

  CONSTRAINT fk_measurements_sensor FOREIGN KEY (sensor_id) REFERENCES sensors(id)
    -- lieber RESTRICT, damit Historie nicht “aus Versehen” wegcascadet
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_measurements_variable FOREIGN KEY (variable_id) REFERENCES variables(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ensure ts column type is Unix ms even on existing DBs
ALTER TABLE measurements MODIFY COLUMN ts BIGINT UNSIGNED NOT NULL;

-- =========================
-- Triggers (NO DELIMITER!)
-- =========================

DROP TRIGGER IF EXISTS trg_measurements_bi;
DROP TRIGGER IF EXISTS trg_measurements_bu;

CREATE TRIGGER trg_measurements_bi
BEFORE INSERT ON measurements
FOR EACH ROW
BEGIN
  IF NEW.value_type = 'num' THEN
    IF NEW.value_num IS NULL OR NEW.value_int IS NOT NULL OR NEW.value_bool IS NOT NULL OR NEW.value_text IS NOT NULL OR NEW.value_json IS NOT NULL OR NEW.value_blob IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=num requires only value_num';
    END IF;

  ELSEIF NEW.value_type = 'int' THEN
    IF NEW.value_int IS NULL OR NEW.value_num IS NOT NULL OR NEW.value_bool IS NOT NULL OR NEW.value_text IS NOT NULL OR NEW.value_json IS NOT NULL OR NEW.value_blob IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=int requires only value_int';
    END IF;

  ELSEIF NEW.value_type = 'bool' THEN
    IF NEW.value_bool IS NULL OR NEW.value_num IS NOT NULL OR NEW.value_int IS NOT NULL OR NEW.value_text IS NOT NULL OR NEW.value_json IS NOT NULL OR NEW.value_blob IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=bool requires only value_bool';
    END IF;

  ELSEIF NEW.value_type = 'text' THEN
    IF NEW.value_text IS NULL OR NEW.value_num IS NOT NULL OR NEW.value_int IS NOT NULL OR NEW.value_bool IS NOT NULL OR NEW.value_json IS NOT NULL OR NEW.value_blob IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=text requires only value_text';
    END IF;

  ELSEIF NEW.value_type = 'json' THEN
    IF NEW.value_json IS NULL OR NEW.value_num IS NOT NULL OR NEW.value_int IS NOT NULL OR NEW.value_bool IS NOT NULL OR NEW.value_text IS NOT NULL OR NEW.value_blob IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=json requires only value_json';
    END IF;

  ELSEIF NEW.value_type = 'blob' THEN
    IF NEW.value_blob IS NULL OR NEW.value_num IS NOT NULL OR NEW.value_int IS NOT NULL OR NEW.value_bool IS NOT NULL OR NEW.value_text IS NOT NULL OR NEW.value_json IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=blob requires only value_blob';
    END IF;

  ELSE
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: invalid value_type';
  END IF;
END;

CREATE TRIGGER trg_measurements_bu
BEFORE UPDATE ON measurements
FOR EACH ROW
BEGIN
  IF NEW.value_type = 'num' THEN
    IF NEW.value_num IS NULL OR NEW.value_int IS NOT NULL OR NEW.value_bool IS NOT NULL OR NEW.value_text IS NOT NULL OR NEW.value_json IS NOT NULL OR NEW.value_blob IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=num requires only value_num';
    END IF;

  ELSEIF NEW.value_type = 'int' THEN
    IF NEW.value_int IS NULL OR NEW.value_num IS NOT NULL OR NEW.value_bool IS NOT NULL OR NEW.value_text IS NOT NULL OR NEW.value_json IS NOT NULL OR NEW.value_blob IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=int requires only value_int';
    END IF;

  ELSEIF NEW.value_type = 'bool' THEN
    IF NEW.value_bool IS NULL OR NEW.value_num IS NOT NULL OR NEW.value_int IS NOT NULL OR NEW.value_text IS NOT NULL OR NEW.value_json IS NOT NULL OR NEW.value_blob IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=bool requires only value_bool';
    END IF;

  ELSEIF NEW.value_type = 'text' THEN
    IF NEW.value_text IS NULL OR NEW.value_num IS NOT NULL OR NEW.value_int IS NOT NULL OR NEW.value_bool IS NOT NULL OR NEW.value_json IS NOT NULL OR NEW.value_blob IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=text requires only value_text';
    END IF;

  ELSEIF NEW.value_type = 'json' THEN
    IF NEW.value_json IS NULL OR NEW.value_num IS NOT NULL OR NEW.value_int IS NOT NULL OR NEW.value_bool IS NOT NULL OR NEW.value_text IS NOT NULL OR NEW.value_blob IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=json requires only value_json';
    END IF;

  ELSEIF NEW.value_type = 'blob' THEN
    IF NEW.value_blob IS NULL OR NEW.value_num IS NOT NULL OR NEW.value_int IS NOT NULL OR NEW.value_bool IS NOT NULL OR NEW.value_text IS NOT NULL OR NEW.value_json IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: value_type=blob requires only value_blob';
    END IF;

  ELSE
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='measurements: invalid value_type';
  END IF;
END;
