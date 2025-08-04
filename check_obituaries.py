#!/usr/bin/env python3

from genealogy_mapper.core.config import Config
from genealogy_mapper.core.neo4j_ops import Neo4jOperations

def check_obituaries():
    config = Config()
    neo4j_config = config.get_neo4j_config()
    ops = Neo4jOperations(neo4j_config['uri'], neo4j_config['user'], neo4j_config['password'])
    
    print("Checking obituaries...")
    with ops.driver.session() as session:
        result = session.run('MATCH (o:Obituary) RETURN o.id as id, o.url as url, o.status as status')
        for record in result:
            print(f"ID: {record['id']}, URL: {record['url']}, Status: {record['status']}")

if __name__ == "__main__":
    check_obituaries() 