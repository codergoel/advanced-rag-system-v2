from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from .neo4j_service import Neo4jService
from .gemini_service import GeminiService
import json
import uuid

class Location(BaseModel):
    """Represents a physical location including address, city, state, and country."""
    address: Optional[str] = Field(
        ..., description="The street address of the location."
    )
    city: Optional[str] = Field(..., description="The city of the location.")
    state: Optional[str] = Field(
        ..., description="The state or region of the location."
    )
    country: str = Field(
        ...,
        description="The country of the location. Use the two-letter ISO standard.",
    )

class Organization(BaseModel):
    """Represents an organization, including its name and location."""
    name: str = Field(..., description="The name of the organization.")
    location: Location = Field(
        ..., description="The primary location of the organization."
    )
    role: str = Field(
        ...,
        description="The role of the organization in the contract, such as 'provider', 'client', 'supplier', etc.",
    )

class Contract(BaseModel):
    """Represents the key details of the contract."""
    contract_type: str = Field(
        ...,
        description="The type of contract being entered into.",
    )
    parties: List[Organization] = Field(
        ...,
        description="List of parties involved in the contract, with details of each party's role.",
    )
    effective_date: str = Field(
        ...,
        description="The date when the contract becomes effective. Use yyyy-MM-dd format.",
    )
    term: str = Field(
        ...,
        description="The duration of the agreement, including provisions for renewal or termination.",
    )
    contract_scope: str = Field(
        ...,
        description="Description of the scope of the contract, including rights, duties, and any limitations.",
    )
    end_date: Optional[str] = Field(
        ...,
        description="The date when the contract becomes expires. Use yyyy-MM-dd format.",
    )
    total_amount: Optional[float] = Field(
        ..., description="Total value of the contract."
    )
    governing_law: Optional[Location] = Field(
        ..., description="The jurisdiction's laws governing the contract."
    )

class KnowledgeGraphConstructionService:
    def __init__(self, neo4j_service: Neo4jService, gemini_service: GeminiService):
        """
        Initialize Knowledge Graph Construction service
        
        Args:
            neo4j_service: Service for Neo4j operations
            gemini_service: Service for LLM operations
        """
        self.neo4j_service = neo4j_service
        self.gemini_service = gemini_service
        
        # Contract types enum
        self.contract_types = [
            "Service Agreement",
            "Licensing Agreement", 
            "Non-Disclosure Agreement (NDA)",
            "Partnership Agreement",
            "Lease Agreement"
        ]
        
        # System message for contract extraction
        self.system_message = """
You are an expert in extracting structured information from legal documents and contracts.
Identify key details such as parties involved, dates, terms, obligations, and legal definitions.
Present the extracted information in a clear, structured format. Be concise, focusing on essential
legal content and ignoring unnecessary boilerplate language. The extracted data will be used to address
any questions that may arise regarding the contracts.
"""
        
        # Sample contract text for demonstration
        self.sample_contract = """
LICENSE AGREEMENT

This License Agreement ("Agreement") is entered into on February 26, 1999, between Mortgage Logic.com, Inc., a California corporation with its principal place of business at Two Venture Plaza, 2 Venture, Irvine, California ("Client"), and TrueLink, Inc., a California corporation with its principal place of business at 3026 South Higuera, San Luis Obispo, California ("Provider").

1. LICENSE GRANT
TrueLink hereby grants to Mortgage Logic.com a nonexclusive license to use the Interface for origination, underwriting, processing, and funding of consumer finance receivables.

2. TERM
This Agreement shall commence on February 26, 1999, and shall continue for a period of one (1) year, with automatic renewal for successive one-year periods unless terminated with thirty (30) days' notice prior to the end of the term.

3. SERVICES
TrueLink will provide hosting services, including storage, response time management, bandwidth, availability, access to usage statistics, backups, internet connection, and domain name assistance. TrueLink will also provide support services and transmit credit data as permitted under applicable agreements and laws.

4. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with the laws of the State of California.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.
"""

    def extract_contract_info(self, document: str) -> Dict[str, Any]:
        """
        Extract structured contract information from text using LLM
        
        Args:
            document: Contract text to extract information from
            
        Returns:
            Dictionary containing extracted contract information
        """
        try:
            # Create the prompt for contract extraction
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": document}
            ]
            
            # Use Gemini to extract structured information
            response = self.gemini_service.chat(messages)
            
            # Try to parse the response as JSON
            try:
                # Clean the response to extract JSON
                response_text = response.strip()
                if response_text.startswith("```json"):
                    response_text = response_text.replace("```json", "").replace("```", "").strip()
                elif response_text.startswith("```"):
                    response_text = response_text.replace("```", "").strip()
                
                # Parse as JSON
                contract_data = json.loads(response_text)
                
                # Validate and structure the data
                structured_data = self._structure_contract_data(contract_data)
                return structured_data
                
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract information using a more structured approach
                return self._extract_with_structured_prompt(document)
                
        except Exception as e:
            return {"error": f"Error extracting contract information: {str(e)}"}

    def _extract_with_structured_prompt(self, document: str) -> Dict[str, Any]:
        """
        Extract contract information using a more structured prompt approach
        
        Args:
            document: Contract text
            
        Returns:
            Structured contract data
        """
        try:
            # Create a more specific prompt for extraction
            extraction_prompt = f"""
Extract the following information from this contract document and return it as a JSON object:

{{
    "contract_type": "Type of contract (Service Agreement, Licensing Agreement, NDA, Partnership Agreement, or Lease Agreement)",
    "parties": [
        {{
            "name": "Organization name",
            "location": {{
                "address": "Street address",
                "city": "City",
                "state": "State",
                "country": "Two-letter country code (e.g., US)"
            }},
            "role": "Role in contract (client, provider, supplier, etc.)"
        }}
    ],
    "effective_date": "Start date in yyyy-MM-dd format",
    "term": "Duration and renewal terms",
    "contract_scope": "Description of what the contract covers",
    "end_date": "End date in yyyy-MM-dd format (if specified)",
    "total_amount": "Total contract value (if specified)",
    "governing_law": {{
        "address": "Address of governing jurisdiction",
        "city": "City of governing jurisdiction", 
        "state": "State of governing jurisdiction",
        "country": "Country of governing jurisdiction"
    }}
}}

Contract document:
{document}

Return only the JSON object, no additional text.
"""
            
            messages = [{"role": "user", "content": extraction_prompt}]
            response = self.gemini_service.chat(messages)
            
            # Clean and parse the response
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            contract_data = json.loads(response_text)
            return self._structure_contract_data(contract_data)
            
        except Exception as e:
            return {"error": f"Error in structured extraction: {str(e)}"}

    def _structure_contract_data(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure and validate contract data
        
        Args:
            contract_data: Raw contract data from LLM
            
        Returns:
            Structured and validated contract data
        """
        try:
            # Ensure required fields exist
            structured_data = {
                "contract_type": contract_data.get("contract_type", "Service Agreement"),
                "parties": contract_data.get("parties", []),
                "effective_date": contract_data.get("effective_date", ""),
                "term": contract_data.get("term", ""),
                "contract_scope": contract_data.get("contract_scope", ""),
                "end_date": contract_data.get("end_date"),
                "total_amount": contract_data.get("total_amount"),
                "governing_law": contract_data.get("governing_law")
            }
            
            # Validate contract type
            if structured_data["contract_type"] not in self.contract_types:
                structured_data["contract_type"] = "Service Agreement"
            
            # Ensure parties is a list
            if not isinstance(structured_data["parties"], list):
                structured_data["parties"] = []
            
            # Validate and structure each party
            validated_parties = []
            for party in structured_data["parties"]:
                if isinstance(party, dict):
                    validated_party = {
                        "name": party.get("name", ""),
                        "location": {
                            "address": party.get("location", {}).get("address"),
                            "city": party.get("location", {}).get("city"),
                            "state": party.get("location", {}).get("state"),
                            "country": party.get("location", {}).get("country", "US")
                        },
                        "role": party.get("role", "party")
                    }
                    validated_parties.append(validated_party)
            
            structured_data["parties"] = validated_parties
            
            return structured_data
            
        except Exception as e:
            return {"error": f"Error structuring contract data: {str(e)}"}

    def create_graph_constraints(self) -> Dict[str, Any]:
        """
        Create unique constraints and indexes for the knowledge graph
        
        Returns:
            Result of constraint creation operations
        """
        try:
            constraints = []
            
            # Create constraints
            constraint_queries = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Contract) REQUIRE c.id IS UNIQUE;",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE;",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.fullAddress IS UNIQUE;"
            ]
            
            for query in constraint_queries:
                try:
                    self.neo4j_service.execute_query(query)
                    constraints.append({"query": query, "status": "success"})
                except Exception as e:
                    constraints.append({"query": query, "status": "error", "error": str(e)})
            
            return {
                "message": "Constraints creation completed",
                "constraints": constraints
            }
            
        except Exception as e:
            return {"error": f"Error creating constraints: {str(e)}"}

    def import_contract_to_graph(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import contract data into Neo4j knowledge graph
        
        Args:
            contract_data: Structured contract data
            
        Returns:
            Result of the import operation
        """
        try:
            if "error" in contract_data:
                return contract_data
            
            # Create the import query
            import_query = """
WITH $data AS contract_data
MERGE (contract:Contract {id: randomUUID()})
SET contract += {
    contract_type: contract_data.contract_type,
    effective_date: contract_data.effective_date,
    term: contract_data.term,
    contract_scope: contract_data.contract_scope,
    end_date: contract_data.end_date,
    total_amount: contract_data.total_amount,
    governing_law: contract_data.governing_law.state + ' ' + contract_data.governing_law.country
}
WITH contract, contract_data
UNWIND contract_data.parties AS party
MERGE (p:Organization {name: party.name})
MERGE (loc:Location {
    fullAddress: party.location.address + ' ' + 
    party.location.city + ' ' + 
    party.location.state + ' ' + 
    party.location.country
})
SET loc += {
    address: party.location.address,
    city: party.location.city,
    state: party.location.state,
    country: party.location.country
}
MERGE (p)-[:LOCATED_AT]->(loc)
MERGE (p)-[r:HAS_PARTY]->(contract)
SET r.role = party.role
"""
            
            # Execute the import
            result = self.neo4j_service.execute_query(import_query, parameters={"data": contract_data})
            
            return {
                "message": "Contract imported successfully",
                "contract_type": contract_data.get("contract_type"),
                "parties_count": len(contract_data.get("parties", [])),
                "result": result
            }
            
        except Exception as e:
            return {"error": f"Error importing contract: {str(e)}"}

    def get_contract_graph_data(self) -> Dict[str, Any]:
        """
        Get contract graph data for visualization
        
        Returns:
            Graph data including nodes and relationships
        """
        try:
            # Get all contracts
            contracts_query = """
            MATCH (c:Contract)
            RETURN c.id as id, c.contract_type as type, c.effective_date as effective_date, 
                   c.term as term, c.contract_scope as scope, c.end_date as end_date, 
                   c.total_amount as total_amount, c.governing_law as governing_law
            """
            contracts = self.neo4j_service.execute_query(contracts_query)
            
            # Get all organizations
            organizations_query = """
            MATCH (o:Organization)
            RETURN o.name as name, o.role as role
            """
            organizations = self.neo4j_service.execute_query(organizations_query)
            
            # Get all locations
            locations_query = """
            MATCH (l:Location)
            RETURN l.fullAddress as fullAddress, l.address as address, l.city as city, 
                   l.state as state, l.country as country
            """
            locations = self.neo4j_service.execute_query(locations_query)
            
            # Get relationships
            relationships_query = """
            MATCH (o:Organization)-[r:HAS_PARTY]->(c:Contract)
            RETURN o.name as organization, c.id as contract, r.role as role
            """
            party_relationships = self.neo4j_service.execute_query(relationships_query)
            
            location_relationships_query = """
            MATCH (o:Organization)-[:LOCATED_AT]->(l:Location)
            RETURN o.name as organization, l.fullAddress as location
            """
            location_relationships = self.neo4j_service.execute_query(location_relationships_query)
            
            return {
                "contracts": contracts,
                "organizations": organizations,
                "locations": locations,
                "party_relationships": party_relationships,
                "location_relationships": location_relationships,
                "total_contracts": len(contracts),
                "total_organizations": len(organizations),
                "total_locations": len(locations)
            }
            
        except Exception as e:
            return {"error": f"Error getting graph data: {str(e)}"}

    def query_contracts(self, question: str) -> Dict[str, Any]:
        """
        Query the contract knowledge graph using natural language
        
        Args:
            question: Natural language question about contracts
            
        Returns:
            Query results and generated Cypher
        """
        try:
            # Generate Cypher query from natural language
            cypher_prompt = f"""
Generate a Cypher query to answer this question about contracts: "{question}"

Available schema:
- Contract nodes with properties: id, contract_type, effective_date, term, contract_scope, end_date, total_amount, governing_law
- Organization nodes with properties: name, role
- Location nodes with properties: fullAddress, address, city, state, country
- Relationships: (Organization)-[:HAS_PARTY]->(Contract), (Organization)-[:LOCATED_AT]->(Location)

Return only the Cypher query, no explanations.
"""
            
            messages = [{"role": "user", "content": cypher_prompt}]
            cypher_query = self.gemini_service.chat(messages)
            
            # Clean the Cypher query
            cypher_query = cypher_query.strip()
            if cypher_query.startswith("```cypher"):
                cypher_query = cypher_query.replace("```cypher", "").replace("```", "").strip()
            elif cypher_query.startswith("```"):
                cypher_query = cypher_query.replace("```", "").strip()
            
            # Execute the query
            results = self.neo4j_service.execute_query(cypher_query)
            
            # Generate a natural language answer
            answer_prompt = f"""
Based on the following query results, provide a clear answer to the question: "{question}"

Query results: {json.dumps(results, indent=2)}

Provide a concise, natural language answer.
"""
            
            answer_messages = [{"role": "user", "content": answer_prompt}]
            answer = self.gemini_service.chat(answer_messages)
            
            return {
                "question": question,
                "cypher_query": cypher_query,
                "results": results,
                "answer": answer.strip()
            }
            
        except Exception as e:
            return {"error": f"Error querying contracts: {str(e)}"}

    def get_sample_contract(self) -> str:
        """
        Get the sample contract text for demonstration
        
        Returns:
            Sample contract text
        """
        return self.sample_contract

    def clear_contract_data(self) -> Dict[str, Any]:
        """
        Clear all contract-related data from the graph
        
        Returns:
            Result of the clear operation
        """
        try:
            # Clear all contract-related nodes and relationships
            clear_query = """
            MATCH (c:Contract)
            DETACH DELETE c
            
            MATCH (o:Organization)
            DETACH DELETE o
            
            MATCH (l:Location)
            DETACH DELETE l
            """
            
            self.neo4j_service.execute_query(clear_query)
            
            return {
                "message": "Contract data cleared successfully",
                "status": "success"
            }
            
        except Exception as e:
            return {"error": f"Error clearing contract data: {str(e)}"}

    def get_contract_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the contract knowledge graph
        
        Returns:
            Statistics about contracts, organizations, and locations
        """
        try:
            # Get basic counts
            stats_query = """
            MATCH (c:Contract)
            WITH count(c) as contract_count
            
            MATCH (o:Organization)
            WITH contract_count, count(o) as org_count
            
            MATCH (l:Location)
            WITH contract_count, org_count, count(l) as location_count
            
            MATCH (o:Organization)-[:HAS_PARTY]->(c:Contract)
            WITH contract_count, org_count, location_count, count(*) as party_relationships
            
            MATCH (o:Organization)-[:LOCATED_AT]->(l:Location)
            WITH contract_count, org_count, location_count, party_relationships, count(*) as location_relationships
            
            RETURN contract_count, org_count, location_count, party_relationships, location_relationships
            """
            
            result = self.neo4j_service.execute_query(stats_query)
            
            if result:
                stats = result[0]
                return {
                    "contracts": stats.get("contract_count", 0),
                    "organizations": stats.get("org_count", 0),
                    "locations": stats.get("location_count", 0),
                    "party_relationships": stats.get("party_relationships", 0),
                    "location_relationships": stats.get("location_relationships", 0)
                }
            else:
                return {
                    "contracts": 0,
                    "organizations": 0,
                    "locations": 0,
                    "party_relationships": 0,
                    "location_relationships": 0
                }
                
        except Exception as e:
            return {"error": f"Error getting statistics: {str(e)}"}
