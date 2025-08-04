#!/usr/bin/env python3

from genealogy_mapper.core.obituary_manager import ObituaryManager
from genealogy_mapper.core.config import Config

def get_obituary_id():
    config = Config()
    neo4j_config = config.get_neo4j_config()
    manager = ObituaryManager(neo4j_config)
    
    print("Finding obituary ID...")
    with manager.driver.session() as session:
        result = session.run('MATCH (o:Obituary) RETURN o.id as id, o.url as url LIMIT 1')
        record = result.single()
        if record:
            print(f"ID: {record['id']}")
            print(f"URL: {record['url']}")
            return record['id']
        else:
            print("No obituaries found")
            return None

if __name__ == "__main__":
    get_obituary_id() 