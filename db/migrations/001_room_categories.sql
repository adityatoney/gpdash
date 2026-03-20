-- Migration 001: Room Type Normalization
-- Normalizes 40 raw room types into 6 canonical categories.
-- "105.0" (data error) is folded into KING.

BEGIN;

-- 1. Create ref_room_categories table
CREATE TABLE ref_room_categories (
    category_id   SERIAL PRIMARY KEY,
    category_code VARCHAR(20) UNIQUE NOT NULL,
    category_name VARCHAR(80) NOT NULL,
    display_order SMALLINT NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Insert 6 categories
INSERT INTO ref_room_categories (category_code, category_name, display_order) VALUES
  ('KING',          'King (1 bed)',         1),
  ('DOUBLE',        'Double / Queen (2 beds)', 2),
  ('SUITE_1BR',     'Suite (1 bedroom)',    3),
  ('SUITE_2BR',     'Suite (2 bedroom)',    4),
  ('PARLOR',        'Parlor Room',          5),
  ('PRESIDENTIAL',  'Presidential Suite',   6);

-- 3. Add category_id column (nullable first for UPDATE)
ALTER TABLE ref_room_types
  ADD COLUMN category_id INTEGER REFERENCES ref_room_categories(category_id);

-- 4. Map all 40 type_codes to categories
UPDATE ref_room_types
SET category_id = (
  SELECT category_id FROM ref_room_categories WHERE category_code = (
    CASE type_code
      -- KING (17 types, including 105.0)
      WHEN 'King'                                      THEN 'KING'
      WHEN '1 King Bed'                                THEN 'KING'
      WHEN 'One King Bed'                              THEN 'KING'
      WHEN 'Single King Bed'                           THEN 'KING'
      WHEN '1 King Accessible with Roll-in Shower'     THEN 'KING'
      WHEN '1 King Bed Accessible with Bathtub'        THEN 'KING'
      WHEN 'Atrium 1 King Bed'                         THEN 'KING'
      WHEN 'Atrium Corner 1 King Bed'                  THEN 'KING'
      WHEN 'Tower 1 King Bed'                          THEN 'KING'
      WHEN 'Deluxe Room, 1 King'                       THEN 'KING'
      WHEN 'Traditional Room, 1 King'                  THEN 'KING'
      WHEN 'Non-Smoking 1 King Bed'                    THEN 'KING'
      WHEN 'Single King Bed - ADA with Shower'         THEN 'KING'
      WHEN 'Single King Bed - ADA with Tub'            THEN 'KING'
      WHEN 'One King Bed - Studio'                     THEN 'KING'
      WHEN 'Tower King Bed with Sleeper Sofa'          THEN 'KING'
      WHEN '105.0'                                     THEN 'KING'
      -- DOUBLE (16 types)
      WHEN 'Double Beds'                               THEN 'DOUBLE'
      WHEN 'Two Double Beds'                           THEN 'DOUBLE'
      WHEN 'Non-Smoking 2 Double Beds'                 THEN 'DOUBLE'
      WHEN '2 Double Accessible with Bathtub'          THEN 'DOUBLE'
      WHEN '2 Double Beds Accessible with Bathtub'     THEN 'DOUBLE'
      WHEN '2 Double Beds Accessible with Roll-in Shower' THEN 'DOUBLE'
      WHEN 'Two Full Beds'                             THEN 'DOUBLE'
      WHEN 'Two Queen Beds'                            THEN 'DOUBLE'
      WHEN 'Two Queen Beds - ADA with Shower'          THEN 'DOUBLE'
      WHEN 'Two Queen Beds - ADA with Tub'             THEN 'DOUBLE'
      WHEN 'Deluxe Room, 2 Doubles'                    THEN 'DOUBLE'
      WHEN 'Traditional Room, 2 Doubles'               THEN 'DOUBLE'
      WHEN 'Tower Standard 2 Beds'                     THEN 'DOUBLE'
      WHEN 'Atrium 2 Beds'                             THEN 'DOUBLE'
      WHEN 'Atrium Corner 2 Beds'                      THEN 'DOUBLE'
      WHEN 'Two Queen Beds - Studio'                   THEN 'DOUBLE'
      -- SUITE_1BR (1 type)
      WHEN 'Executive Suite - 1 Bedroom'               THEN 'SUITE_1BR'
      -- SUITE_2BR (3 types)
      WHEN 'Junior Suite - 2 Bedrooms'                 THEN 'SUITE_2BR'
      WHEN 'VIP Suite A - 2 Bedrooms'                  THEN 'SUITE_2BR'
      WHEN 'VIP Suite B - 2 Bedrooms'                  THEN 'SUITE_2BR'
      -- PARLOR (2 types)
      WHEN 'Deluxe Parlor Room'                        THEN 'PARLOR'
      WHEN 'Standard Parlor Room'                      THEN 'PARLOR'
      -- PRESIDENTIAL (1 type)
      WHEN 'Presidential Suite'                        THEN 'PRESIDENTIAL'
    END
  )
);

-- 5. Verify no NULLs before constraining
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM ref_room_types WHERE category_id IS NULL) THEN
    RAISE EXCEPTION 'Not all room types were mapped to a category!';
  END IF;
END $$;

-- 6. Add NOT NULL constraint and index
ALTER TABLE ref_room_types
  ALTER COLUMN category_id SET NOT NULL;

CREATE INDEX idx_room_types_category ON ref_room_types(category_id);

COMMIT;
