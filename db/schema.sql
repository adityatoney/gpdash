-- GP Event Data — PostgreSQL Schema
-- Normalized schema for multi-year GP event data (2022-2025)
--
-- Table classification:
--   REFERENCE (6): ref_regions, ref_centers, ref_food_preferences, ref_room_types, ref_age_groups, ref_hotels
--   CORE (7):      events, persons, person_contacts, registrations, rooms, room_occupants, meal_scans
--   AUX (8):       registration_youth, registration_lmht, registration_bhakti, special_needs_requests,
--                  translation_requests, registration_exceptions, dashboard_snapshots, meal_aggregates
--   SYSTEM (5):    data_availability, agent_jobs, agent_job_steps, aggregation_cache, user_preferences

BEGIN;

-- ===================== REFERENCE TABLES =====================

CREATE TABLE ref_regions (
    region_id       SERIAL PRIMARY KEY,
    region_code     VARCHAR(10) UNIQUE NOT NULL,
    region_name     VARCHAR(50) NOT NULL,
    legacy_id       INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ref_centers (
    center_id       SERIAL PRIMARY KEY,
    center_name     VARCHAR(200) UNIQUE NOT NULL,
    region_id       INTEGER REFERENCES ref_regions(region_id),
    state           VARCHAR(100),
    country         VARCHAR(100) DEFAULT 'USA',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ref_food_preferences (
    food_pref_id    SERIAL PRIMARY KEY,
    code            VARCHAR(10) UNIQUE NOT NULL,
    label           VARCHAR(100) NOT NULL,
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ref_room_types (
    room_type_id    SERIAL PRIMARY KEY,
    type_code       VARCHAR(50) UNIQUE NOT NULL,
    type_name       VARCHAR(100) NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ref_age_groups (
    age_group_id    SERIAL PRIMARY KEY,
    group_code      VARCHAR(20) UNIQUE NOT NULL,
    min_age         INTEGER,
    max_age         INTEGER,
    label           VARCHAR(50) NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ref_hotels (
    hotel_id        SERIAL PRIMARY KEY,
    hotel_name      VARCHAR(200) UNIQUE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ===================== CORE TABLES =====================

CREATE TABLE events (
    event_id                SERIAL PRIMARY KEY,
    event_year              SMALLINT UNIQUE NOT NULL,
    event_name              VARCHAR(100) NOT NULL,
    start_date              DATE,
    end_date                DATE,
    total_registrations     INTEGER DEFAULT 0,
    total_room_bookings     INTEGER DEFAULT 0,
    total_meal_scans        INTEGER DEFAULT 0,
    has_registration_data   BOOLEAN DEFAULT FALSE,
    has_room_data           BOOLEAN DEFAULT FALSE,
    has_food_data           BOOLEAN DEFAULT FALSE,
    has_dashboard_data      BOOLEAN DEFAULT FALSE,
    notes                   TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE persons (
    person_id       SERIAL PRIMARY KEY,
    mahatma_id      VARCHAR(50) UNIQUE,
    family_id       VARCHAR(50),
    member_id       VARCHAR(50),
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    gender          CHAR(1),
    birth_month     SMALLINT,
    birth_year      SMALLINT,
    city            VARCHAR(100),
    state           VARCHAR(100),
    postal_code     VARCHAR(50),
    country         VARCHAR(100) DEFAULT 'USA',
    address1        VARCHAR(200),
    address2        VARCHAR(200),
    center_id       INTEGER REFERENCES ref_centers(center_id),
    region_id       INTEGER REFERENCES ref_regions(region_id),
    gnan_taken      BOOLEAN,
    gnan_language   VARCHAR(50),
    gnan_date       DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE person_contacts (
    contact_id              SERIAL PRIMARY KEY,
    person_id               INTEGER NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    phone1                  VARCHAR(30),
    phone2                  VARCHAR(30),
    whatsapp_number         VARCHAR(40),
    family_email            VARCHAR(250),
    youth_email             VARCHAR(200),
    youth_cell_phone        VARCHAR(30),
    emergency_contact_name  VARCHAR(200),
    emergency_contact_phone VARCHAR(30),
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE registrations (
    registration_id     SERIAL PRIMARY KEY,
    event_id            INTEGER NOT NULL REFERENCES events(event_id),
    person_id           INTEGER NOT NULL REFERENCES persons(person_id),
    event_year          SMALLINT NOT NULL,
    registration_date   DATE,
    registration_status SMALLINT,
    confirmation_number VARCHAR(50),
    member_event_id     VARCHAR(50),
    household_relation  VARCHAR(50),
    age_at_event        SMALLINT,
    age_group_id        INTEGER REFERENCES ref_age_groups(age_group_id),
    food_pref_id        INTEGER REFERENCES ref_food_preferences(food_pref_id),
    needs_mobility_aid  BOOLEAN DEFAULT FALSE,
    special_assistance  TEXT,
    arrival_date        DATE,
    departure_date      DATE,
    length_of_stay      SMALLINT,
    is_checked_in       BOOLEAN,
    checked_in_time     TIMESTAMPTZ,
    mode_of_transport   VARCHAR(100),
    translation_needed  VARCHAR(100),
    dietary_restrictions TEXT,
    is_returning        BOOLEAN,
    source_file         VARCHAR(200) NOT NULL,
    source_sheet        VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (event_id, person_id)
);

CREATE TABLE rooms (
    room_id                     SERIAL PRIMARY KEY,
    event_id                    INTEGER NOT NULL REFERENCES events(event_id),
    event_year                  SMALLINT NOT NULL,
    family_id                   VARCHAR(50),
    family_event_room_id        VARCHAR(50),
    primary_room_holder_id      INTEGER REFERENCES persons(person_id),
    room_type_requested_id      INTEGER REFERENCES ref_room_types(room_type_id),
    room_type_assigned_id       INTEGER REFERENCES ref_room_types(room_type_id),
    num_rooms                   SMALLINT DEFAULT 1,
    room_occupancy              SMALLINT,
    check_in_date               DATE,
    check_out_date              DATE,
    final_check_in_date         DATE,
    final_check_out_date        DATE,
    night_count                 SMALLINT,
    room_requested_date         DATE,
    hotel_id                    INTEGER REFERENCES ref_hotels(hotel_id),
    room_group_assigned         VARCHAR(100),
    hotel_confirmation_number   VARCHAR(100),
    room_requested              BOOLEAN,
    room_picked_up              BOOLEAN,
    room_status                 VARCHAR(50),
    is_room_booked              BOOLEAN,
    is_accessible               BOOLEAN DEFAULT FALSE,
    is_rolling_shower           BOOLEAN DEFAULT FALSE,
    is_senior_not_sharing_beds  BOOLEAN DEFAULT FALSE,
    special_needs_text          TEXT,
    invoiced_amount             NUMERIC(10,2),
    paid_amount                 NUMERIC(10,2),
    payment_status              VARCHAR(50),
    paid_by                     VARCHAR(200),
    processing_fees             NUMERIC(10,2),
    payment_net_amount          NUMERIC(10,2),
    min_age                     SMALLINT,
    max_age                     SMALLINT,
    occupants_info              TEXT,
    additional_comments         TEXT,
    source_file                 VARCHAR(200) NOT NULL,
    source_sheet                VARCHAR(100),
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE room_occupants (
    room_occupant_id    SERIAL PRIMARY KEY,
    room_id             INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    person_id           INTEGER REFERENCES persons(person_id),
    occupant_name       VARCHAR(200),
    occupant_age        SMALLINT,
    occupant_position   SMALLINT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE meal_scans (
    meal_scan_id        SERIAL PRIMARY KEY,
    event_id            INTEGER NOT NULL REFERENCES events(event_id),
    event_year          SMALLINT NOT NULL,
    person_id           INTEGER REFERENCES persons(person_id),
    session_title       VARCHAR(200),
    session_type        VARCHAR(50),
    session_date        DATE,
    time_slot           VARCHAR(50),
    scanned_time        TIMESTAMPTZ,
    tag                 VARCHAR(50),
    display_order       INTEGER,
    age_group_code      VARCHAR(20),
    gender              CHAR(1),
    food_pref_selected  VARCHAR(50),
    food_consumed       VARCHAR(50),
    is_new_mahatma      BOOLEAN,
    food_count          INTEGER DEFAULT 1,
    center_name         VARCHAR(200),
    state_or_province   VARCHAR(100),
    country             VARCHAR(100),
    mms_member_id       VARCHAR(50),
    source_file         VARCHAR(200) NOT NULL,
    source_sheet        VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ===================== AUX TABLES =====================

CREATE TABLE registration_youth (
    youth_reg_id        SERIAL PRIMARY KEY,
    registration_id     INTEGER NOT NULL REFERENCES registrations(registration_id) ON DELETE CASCADE,
    ymht_activities     TEXT,
    youth_cell_phone    VARCHAR(30),
    youth_email         VARCHAR(200),
    photo_consent       BOOLEAN,
    tshirt_size         VARCHAR(10),
    ymht_outing         BOOLEAN,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE registration_lmht (
    lmht_reg_id         SERIAL PRIMARY KEY,
    registration_id     INTEGER NOT NULL REFERENCES registrations(registration_id) ON DELETE CASCADE,
    seva                TEXT,
    activities          TEXT,
    drop_off_person1_name  VARCHAR(200),
    drop_off_person1_phone VARCHAR(30),
    drop_off_person2_name  VARCHAR(200),
    drop_off_person2_phone VARCHAR(30),
    dietary_restrictions   TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE registration_bhakti (
    bhakti_id               SERIAL PRIMARY KEY,
    registration_id         INTEGER REFERENCES registrations(registration_id) ON DELETE CASCADE,
    person_id               INTEGER REFERENCES persons(person_id),
    event_year              SMALLINT NOT NULL DEFAULT 2025,
    perform_in_bhakti       BOOLEAN,
    previous_bhakti_audition VARCHAR(20),
    other_audition_event    TEXT,
    bhakti_activity         TEXT,
    source_file             VARCHAR(200),
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE special_needs_requests (
    request_id          SERIAL PRIMARY KEY,
    registration_id     INTEGER REFERENCES registrations(registration_id) ON DELETE CASCADE,
    person_id           INTEGER REFERENCES persons(person_id),
    event_year          SMALLINT NOT NULL,
    request_type        VARCHAR(100),
    need_mobility_aid   BOOLEAN,
    bring_own_aid       BOOLEAN,
    accompanying        VARCHAR(200),
    rental_option       VARCHAR(100),
    request_details     TEXT,
    source_file         VARCHAR(200),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE translation_requests (
    translation_id      SERIAL PRIMARY KEY,
    registration_id     INTEGER REFERENCES registrations(registration_id) ON DELETE CASCADE,
    person_id           INTEGER REFERENCES persons(person_id),
    event_year          SMALLINT NOT NULL DEFAULT 2025,
    language_requested  VARCHAR(100),
    mode_of_transport   VARCHAR(100),
    source_file         VARCHAR(200),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE registration_exceptions (
    exception_id        SERIAL PRIMARY KEY,
    person_id           INTEGER REFERENCES persons(person_id),
    event_year          SMALLINT NOT NULL DEFAULT 2025,
    reason_code         VARCHAR(50),
    gp_checkout_date    DATE,
    mahatma_id          VARCHAR(50),
    name_fl             VARCHAR(200),
    email               VARCHAR(200),
    phone               VARCHAR(30),
    center_name         VARCHAR(200),
    state               VARCHAR(100),
    country             VARCHAR(100),
    global_region       VARCHAR(50),
    source_sheet        VARCHAR(100),
    source_file         VARCHAR(200),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE dashboard_snapshots (
    snapshot_id         SERIAL PRIMARY KEY,
    event_year          SMALLINT NOT NULL,
    snapshot_type       VARCHAR(100) NOT NULL,
    snapshot_date       DATE,
    dimension_key       VARCHAR(200),
    dimension_value     VARCHAR(200),
    metric_name         VARCHAR(100) NOT NULL,
    metric_value        NUMERIC(12,2),
    raw_json            JSONB,
    source_file         VARCHAR(200) NOT NULL,
    source_sheet        VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE meal_aggregates (
    aggregate_id        SERIAL PRIMARY KEY,
    event_id            INTEGER NOT NULL REFERENCES events(event_id),
    event_year          SMALLINT NOT NULL,
    meal_date           DATE NOT NULL,
    food_type           VARCHAR(50),
    breakfast_count     INTEGER,
    lunch_count         INTEGER,
    tea_break_count     INTEGER,
    dinner_count        INTEGER,
    total_count         INTEGER,
    meal_conflicts      JSONB,
    source_file         VARCHAR(200) NOT NULL,
    source_sheet        VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ===================== SYSTEM TABLES =====================

CREATE TABLE data_availability (
    availability_id     SERIAL PRIMARY KEY,
    event_year          SMALLINT NOT NULL,
    entity_type         VARCHAR(50) NOT NULL,
    data_level          VARCHAR(20) NOT NULL,
    source_files        TEXT[],
    row_count           INTEGER,
    notes               TEXT,
    UNIQUE (event_year, entity_type)
);

CREATE TABLE agent_jobs (
    job_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status          VARCHAR(20) NOT NULL DEFAULT 'queued',
    phase           VARCHAR(30),
    progress        SMALLINT DEFAULT 0,
    current_step    VARCHAR(500),
    files_processed TEXT[],
    errors          TEXT[],
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    report_path     VARCHAR(500)
);

CREATE TABLE agent_job_steps (
    step_id         SERIAL PRIMARY KEY,
    job_id          UUID NOT NULL REFERENCES agent_jobs(job_id) ON DELETE CASCADE,
    step_number     INTEGER NOT NULL,
    step_name       VARCHAR(200) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    records_processed INTEGER DEFAULT 0,
    records_skipped   INTEGER DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ
);

CREATE TABLE aggregation_cache (
    cache_id        SERIAL PRIMARY KEY,
    cache_key       VARCHAR(200) UNIQUE NOT NULL,
    event_year      SMALLINT,
    data_type       VARCHAR(20) NOT NULL,
    payload         JSONB NOT NULL,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE user_preferences (
    preference_id       SERIAL PRIMARY KEY,
    session_id          VARCHAR(100) UNIQUE NOT NULL,
    selected_years      SMALLINT[],
    selected_regions    TEXT[],
    selected_room_types TEXT[],
    date_range_start    DATE,
    date_range_end      DATE,
    active_tab          VARCHAR(50),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ===================== INDEXES =====================

-- persons
CREATE INDEX idx_persons_mahatma_id ON persons(mahatma_id) WHERE mahatma_id IS NOT NULL;
CREATE INDEX idx_persons_family_id ON persons(family_id);
CREATE INDEX idx_persons_name ON persons(last_name, first_name);
CREATE INDEX idx_persons_center ON persons(center_id);
CREATE INDEX idx_persons_region ON persons(region_id);

-- registrations
CREATE INDEX idx_registrations_event_year ON registrations(event_year);
CREATE INDEX idx_registrations_event_person ON registrations(event_id, person_id);
CREATE INDEX idx_registrations_arrival ON registrations(arrival_date);
CREATE INDEX idx_registrations_age_group ON registrations(age_group_id, event_year);
CREATE INDEX idx_registrations_food_pref ON registrations(food_pref_id, event_year);

-- rooms
CREATE INDEX idx_rooms_event_year ON rooms(event_year);
CREATE INDEX idx_rooms_check_in ON rooms(check_in_date);
CREATE INDEX idx_rooms_hotel ON rooms(hotel_id, event_year);
CREATE INDEX idx_rooms_family ON rooms(family_id, event_year);
CREATE INDEX idx_rooms_type_assigned ON rooms(room_type_assigned_id, event_year);

-- room_occupants
CREATE INDEX idx_room_occupants_room ON room_occupants(room_id);
CREATE INDEX idx_room_occupants_person ON room_occupants(person_id);

-- meal_scans
CREATE INDEX idx_meal_scans_event_year ON meal_scans(event_year);
CREATE INDEX idx_meal_scans_date ON meal_scans(session_date, event_year);
CREATE INDEX idx_meal_scans_person ON meal_scans(person_id) WHERE person_id IS NOT NULL;
CREATE INDEX idx_meal_scans_session ON meal_scans(session_title, event_year);

-- aux/system
CREATE INDEX idx_meal_agg_year_date ON meal_aggregates(event_year, meal_date);
CREATE INDEX idx_dash_snapshot_year_type ON dashboard_snapshots(event_year, snapshot_type);
CREATE INDEX idx_data_avail_year ON data_availability(event_year);
CREATE INDEX idx_agent_jobs_status ON agent_jobs(status);
CREATE INDEX idx_agg_cache_key ON aggregation_cache(cache_key);

COMMIT;
