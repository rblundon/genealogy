# Call Graph: Complete Obituary Processing Workflow

## 📊 Complete Call Graph

```
process_obituary(url, dry_run, force)  # Main orchestration command
├── Step 1: add_obituary(url, dry_run, force)
│   ├── urlparse(url).netloc.lower()  # Extract domain
│   ├── ObituaryManager()
│   │   ├── __init__()
│   │   │   ├── Config().get_neo4j_config()
│   │   │   ├── GraphDatabase.driver()
│   │   │   └── requests.Session()
│   │   └── add_obituary_url(url, source, dry_run, force_rescrape)
│   │       ├── _normalize_url(url)
│   │       ├── validate_url(url)
│   │       │   ├── validators.url(url)
│   │       │   └── self.session.get(url, timeout=self.timeout)
│   │       ├── extract_metadata(url)
│   │       │   └── urlparse(url)
│   │       └── session.run()  # Create obituary node in Neo4j
│   │           └── RETURN obituary_id
│   └── Return obituary_id to main workflow
│
├── Step 2: extract_text(obituary_id)
│   ├── ObituaryProcessor()
│   │   ├── __init__()
│   │   │   ├── Config().get_neo4j_config()
│   │   │   ├── GraphDatabase.driver()
│   │   │   ├── requests.Session()
│   │   │   └── ObituaryNERProcessor()
│   │   │       └── spacy.load("en_core_web_sm")
│   │   └── extract_and_store_text(obituary_id)
│   │       ├── get_obituary_url(obituary_id)
│   │       │   └── session.run("MATCH (o:Obituary) WHERE o.id = $id RETURN o.url")
│   │       ├── extract_text(url)
│   │       │   ├── self.session.get(url)
│   │       │   ├── BeautifulSoup(response.text, 'html.parser')
│   │       │   └── soup.get_text()  # Clean and extract text
│   │       └── session.run()  # Store extracted text in Neo4j
│   └── Return success/failure to main workflow
│
├── Step 3: create_individual(obituary_id)
│   ├── ObituaryProcessor()
│   │   ├── __init__()  # Same as Step 2
│   │   └── process_obituary(obituary_id)
│   │       ├── get_obituary_url(obituary_id)
│   │       ├── extract_text(url)  # Re-extract if needed
│   │       ├── store_extracted_text(obituary_id, text)
│   │       │   └── session.run()  # Update obituary with text and status
│   │       ├── extract_person_info(text)
│   │       │   └── self.ner_processor.extract_person_info(text)
│   │       │       ├── self.nlp(text)  # spaCy NLP processing
│   │       │       ├── _extract_name_and_gender(text)
│   │       │       │   ├── doc.ents  # Named Entity Recognition
│   │       │       │   ├── NAME_PATTERNS  # Regex patterns
│   │       │       │   └── GENDER_PATTERNS  # Gender detection
│   │       │       ├── _extract_age(text)
│   │       │       │   └── AGE_PATTERNS  # Age regex patterns
│   │       │       ├── _extract_dates(doc)
│   │       │       │   ├── DEATH_DATE_PATTERNS
│   │       │       │   └── DATE_RANGE_PATTERNS
│   │       │       └── PersonInfo()  # Create data class
│   │       ├── create_or_update_person(person_info_dict)
│   │       │   └── session.run("MERGE (i:Individual {name: $name})")
│   │       └── return individual_id
│   └── Return individual_id to main workflow
│
└── Step 4: process_relationships(individual_id)  # Future
    ├── [TODO: Implement relationship processing]
    ├── RelationshipProcessor()
    │   ├── __init__()
    │   ├── process_analysis(individual_id)
    │   └── import_relationships(analysis)
    └── Display workflow completion
```

Step 2: extract_text(obituary_id, dry_run)
├── ObituaryProcessor()
│   ├── __init__()
│   │   ├── Config().get_neo4j_config()
│   │   ├── GraphDatabase.driver()
│   │   ├── requests.Session()
│   │   └── ObituaryNERProcessor()
│   │       └── spacy.load("en_core_web_sm")
│   │
│   └── extract_and_store_text(obituary_id)
│       ├── get_obituary_url(obituary_id)
│       │   └── session.run("MATCH (o:Obituary) WHERE o.id = $id RETURN o.url")
│       ├── extract_text(url)
│       │   ├── self.session.get(url)
│       │   ├── BeautifulSoup(response.text, 'html.parser')
│       │   └── soup.get_text()  # Clean and extract text
│       └── session.run()  # Store extracted text in Neo4j
└── Display next step to user
    └── create-individual <obituary_id>

Step 3: create_individual(obituary_id, dry_run)
├── ObituaryProcessor()
│   ├── __init__()  # Same as Step 2
│   └── process_obituary(obituary_id)
│       ├── get_obituary_url(obituary_id)
│       ├── extract_text(url)  # Re-extract if needed
│       ├── store_extracted_text(obituary_id, text)
│       │   └── session.run()  # Update obituary with text and status
│       ├── extract_person_info(text)
│       │   └── self.ner_processor.extract_person_info(text)
│       │       ├── self.nlp(text)  # spaCy NLP processing
│       │       ├── _extract_name_and_gender(text)
│       │       │   ├── doc.ents  # Named Entity Recognition
│       │       │   ├── NAME_PATTERNS  # Regex patterns
│       │       │   └── GENDER_PATTERNS  # Gender detection
│       │       ├── _extract_age(text)
│       │       │   └── AGE_PATTERNS  # Age regex patterns
│       │       ├── _extract_dates(doc)
│       │       │   ├── DEATH_DATE_PATTERNS
│       │       │   └── DATE_RANGE_PATTERNS
│       │       └── PersonInfo()  # Create data class
│       ├── create_or_update_person(person_info_dict)
│       │   └── session.run("MERGE (i:Individual {name: $name})")
│       └── return individual_id
└── Display next step to user
    └── process-relationships <individual_id>

Step 4: process_relationships(individual_id, dry_run)
├── [TODO: Implement relationship processing]
├── RelationshipProcessor()
│   ├── __init__()
│   ├── process_analysis(individual_id)
│   └── import_relationships(analysis)
└── Display workflow completion
```

## 🔄 Data Flow Between Steps

```
process_obituary()  # Main orchestration
├── Input: URL string
├── Output: individual_id (Neo4j internal ID)
└── Database: Creates Obituary + Individual nodes

Step 1: add_obituary()
├── Input: URL string
├── Output: obituary_id (UUID)
└── Database: Creates Obituary node

Step 2: extract_text()
├── Input: obituary_id
├── Output: Success/failure status
└── Database: Updates Obituary.extracted_text

Step 3: create_individual()
├── Input: obituary_id
├── Output: individual_id (Neo4j internal ID)
└── Database: Creates Individual node

Step 4: process_relationships()  # Future
├── Input: individual_id
├── Output: Success/failure status
└── Database: Creates relationship nodes
```

## 🎯 Key Components

| Component | Purpose | Input | Output | Database Impact |
|-----------|---------|-------|--------|-----------------|
| `add_obituary()` | Add URL to database | URL string | obituary_id | Creates Obituary node |
| `extract_text()` | Extract text from URL | obituary_id | Success status | Updates Obituary.extracted_text |
| `create_individual()` | Create Individual record | obituary_id | individual_id | Creates Individual node |
| `process_relationships()` | Process relationships | individual_id | Success status | Creates relationship nodes |

## ⚡ Performance Characteristics

- **Step 1**: Fast (URL validation + database write)
- **Step 2**: Medium (web scraping + text processing)
- **Step 3**: Medium (NLP processing + database write)
- **Step 4**: Slow (OpenAI API calls + relationship processing)

## 🛡️ Error Handling

- **Step 1**: URL validation, duplicate checking
- **Step 2**: Web scraping errors, text extraction failures
- **Step 3**: NLP processing errors, database constraint violations
- **Step 4**: OpenAI API errors, relationship validation

## 🔧 Validation Points

- **Step 1**: URL format, accessibility, duplicate prevention
- **Step 2**: Text extraction success, content quality
- **Step 3**: Individual data accuracy, database constraints
- **Step 4**: Relationship validity, data consistency

## 📈 Benefits of Separated Workflow

1. **Step-by-step validation**: Each step can be tested independently
2. **Error isolation**: Issues can be pinpointed to specific steps
3. **Re-run capability**: Individual steps can be re-executed
4. **Progress tracking**: Clear indication of workflow progress
5. **Flexibility**: Steps can be executed in different orders if needed
6. **Debugging**: Detailed logging at each step
7. **ID passing**: Clear data flow between steps 