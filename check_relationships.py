#!/usr/bin/env python3

from genealogy_mapper.core.config import Config
from genealogy_mapper.core.neo4j_ops import Neo4jOperations

def check_relationships():
    config = Config()
    neo4j_config = config.get_neo4j_config()
    ops = Neo4jOperations(neo4j_config['uri'], neo4j_config['user'], neo4j_config['password'])
    
    print("Checking individuals...")
    with ops.driver.session() as session:
        result = session.run('MATCH (i:Individual) RETURN i.name as name, i.id as id ORDER BY i.id')
        for record in result:
            print(f"{record['name']}: {record['id']}")
    
    print("\nChecking relationships...")
    with ops.driver.session() as session:
        result = session.run('MATCH (i:Individual)-[r]->(related:Individual) RETURN i.name as from_name, type(r) as rel_type, related.name as to_name')
        for record in result:
            print(f"{record['from_name']} -[{record['rel_type']}]-> {record['to_name']}")

if __name__ == "__main__":
    check_relationships() 