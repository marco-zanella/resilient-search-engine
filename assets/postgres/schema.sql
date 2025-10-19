CREATE TABLE test_case (
  id SERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  content TEXT NOT NULL,
  context TEXT,
  language TEXT NOT NULL,
  target TEXT NOT NULL,
  tags TEXT[]
);

CREATE TABLE test_collection (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  weights JSONB,
  sources TEXT[],
  books TEXT[]
);

CREATE TABLE test_collection_membership (
  test_case_id INTEGER REFERENCES test_case(id) ON DELETE CASCADE,
  test_collection_id INTEGER REFERENCES test_collection(id) ON DELETE CASCADE,
  PRIMARY KEY (test_case_id, test_collection_id)
);


CREATE TABLE result_collection (
  id SERIAL PRIMARY KEY,
  test_collection_id INTEGER REFERENCES test_collection(id) ON DELETE CASCADE,
  weights JSONB,
  sources TEXT[],
  books TEXT[],
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE result_case (
  id SERIAL PRIMARY KEY,
  test_case_id INTEGER REFERENCES test_case(id) ON DELETE CASCADE,
  result_collection_id INTEGER REFERENCES result_collection(id) ON DELETE CASCADE,
  rank_of_expected INTEGER,
  results JSONB,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE comment (
  id SERIAL PRIMARY KEY,
  result_collection_id INTEGER REFERENCES result_collection(id) ON DELETE CASCADE,
  result_case_id INTEGER REFERENCES result_case(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  author TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);