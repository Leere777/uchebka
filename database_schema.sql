CREATE TABLE product_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    coefficient NUMERIC(10, 2) NOT NULL
);

CREATE TABLE material_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    loss_percent NUMERIC(10, 4) NOT NULL
);

CREATE TABLE workshops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    type VARCHAR(100) NOT NULL,
    employees_count INTEGER NOT NULL CHECK (employees_count > 0)
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    article VARCHAR(50) NOT NULL UNIQUE,
    product_type_id INTEGER NOT NULL REFERENCES product_types(id) ON DELETE RESTRICT,
    name VARCHAR(200) NOT NULL,
    min_price NUMERIC(10, 2) NOT NULL CHECK (min_price >= 0),
    main_material_id INTEGER NOT NULL REFERENCES material_types(id) ON DELETE RESTRICT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_workshops (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    workshop_id INTEGER NOT NULL REFERENCES workshops(id) ON DELETE CASCADE,
    hours NUMERIC(10, 1) NOT NULL CHECK (hours >= 0),
    UNIQUE(product_id, workshop_id)
);