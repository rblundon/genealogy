#!/usr/bin/env python3

from genealogy_mapper.core.obituary_manager import ObituaryManager
from genealogy_mapper.core.config import Config

def list_obituary_ids():
    config = Config()
    neo4j_config = config.get_neo4j_config()
    manager = ObituaryManager(neo4j_config)
    print("Obituary IDs and URLs:")
    with manager.driver.session() as session:
        result = session.run('MATCH (o:Obituary) RETURN o.id as id, o.url as url, o.status as status')
        for record in result:
            print(f"ID: {record['id']} | Status: {record['status']} | URL: {record['url']}")

if __name__ == "__main__":
    list_obituary_ids() 