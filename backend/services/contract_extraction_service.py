from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from .neo4j_service import Neo4jService
from .gemini_service import GeminiService

# Pydantic models for contract extraction
class Location(BaseModel):
    address: Optional[str] = Field(None, description="The street address of the location.")
    city: Optional[str] = Field(None, description="The city of the location.")
    state: Optional[str] = Field(None, description="The state or region of the location.")
    country: str = Field(..., description="The country of the location. Use the two-letter ISO standard.")

class Organization(BaseModel):
    name: str = Field(..., description="The name of the organization.")
    location: Location = Field(..., description="The primary location of the organization.")
    role: str = Field(..., description="The role of the organization in the contract, such as 'provider', 'client', 'supplier', etc.")

class Contract(BaseModel):
    contract_type: str = Field(..., description="The type of contract being entered into.")
    parties: List[Organization] = Field(..., description="List of parties involved in the contract, with details of each party's role.")
    effective_date: str = Field(..., description="The date when the contract becomes effective. Use yyyy-MM-dd format.")
    term: str = Field(..., description="The duration of the agreement, including provisions for renewal or termination.")
    contract_scope: str = Field(..., description="Description of the scope of the contract, including rights, duties, and any limitations.")
    end_date: Optional[str] = Field(None, description="The date when the contract expires. Use yyyy-MM-dd format.")
    total_amount: Optional[float] = Field(None, description="Total value of the contract.")
    governing_law: Optional[Location] = Field(None, description="The jurisdiction's laws governing the contract.")

class ContractExtractionService:
    def __init__(self, neo4j_service: Neo4jService, gemini_service: GeminiService):
        """
        Initialize Contract Extraction service
        
        Args:
            neo4j_service: Service for Neo4j operations
            gemini_service: Service for LLM operations
        """
        self.neo4j_service = neo4j_service
        self.gemini_service = gemini_service
        
        # Contract types
        self.contract_types = [
            "Service Agreement",
            "Licensing Agreement", 
            "Non-Disclosure Agreement (NDA)",
            "Partnership Agreement",
            "Lease Agreement",
            "Employment Agreement",
            "Purchase Agreement",
            "Consulting Agreement"
        ]
    
    def extract_contract_info(self, contract_text: str) -> Dict[str, Any]:
        """
        Extract structured information from contract text
        
        Args:
            contract_text: Raw contract text
            
        Returns:
            Dictionary with extracted contract information
        """
        try:
            # Create contract schema for structured extraction
            contract_schema = {
                "type": "object",
                "properties": {
                    "contract_type": {
                        "type": "string",
                        "description": "The type of contract",
                        "enum": self.contract_types
                    },
                    "parties": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Organization name"},
                                "role": {"type": "string", "description": "Role in contract"},
                                "location": {
                                    "type": "object",
                                    "properties": {
                                        "address": {"type": "string"},
                                        "city": {"type": "string"},
                                        "state": {"type": "string"},
                                        "country": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "effective_date": {"type": "string", "description": "Contract effective date (yyyy-MM-dd)"},
                    "end_date": {"type": "string", "description": "Contract end date (yyyy-MM-dd)"},
                    "term": {"type": "string", "description": "Contract duration and terms"},
                    "contract_scope": {"type": "string", "description": "Scope and description of the contract"},
                    "total_amount": {"type": "number", "description": "Total contract value"},
                    "governing_law": {
                        "type": "object",
                        "properties": {
                            "state": {"type": "string"},
                            "country": {"type": "string"}
                        }
                    }
                }
            }
            
            # Use Gemini's structured extraction
            extracted_data = self.gemini_service.extract_structured_data(
                contract_text, 
                contract_schema,
                model="gemini-1.5-pro"
            )
            
            # Add metadata
            extracted_data["extraction_timestamp"] = self._get_current_timestamp()
            extracted_data["text_length"] = len(contract_text)
            
            return extracted_data
            
        except Exception as e:
            return {"error": f"Error extracting contract information: {str(e)}"}
    
    def store_contract_info(self, contract_info: Dict[str, Any]) -> str:
        """
        Store contract information in Neo4j
        
        Args:
            contract_info: Extracted contract information
            
        Returns:
            Contract ID
        """
        try:
            if "error" in contract_info:
                raise Exception(contract_info["error"])
            
            # Generate contract ID
            import uuid
            contract_id = str(uuid.uuid4())
            
            # Store contract and related entities
            import_query = """
            // Create Contract node
            MERGE (contract:Contract {id: $contract_id})
            SET contract += {
                contract_type: $contract_data.contract_type,
                effective_date: $contract_data.effective_date,
                term: $contract_data.term,
                contract_scope: $contract_data.contract_scope,
                end_date: $contract_data.end_date,
                total_amount: $contract_data.total_amount,
                extraction_timestamp: $contract_data.extraction_timestamp,
                text_length: $contract_data.text_length
            }
            
            // Set governing law if available
            WITH contract, $contract_data
            FOREACH (gov IN CASE WHEN $contract_data.governing_law IS NOT NULL THEN [1] ELSE [] END |
                SET contract.governing_law = $contract_data.governing_law.state + ' ' + $contract_data.governing_law.country
            )
            
            WITH contract, $contract_data
            // Create Party nodes and their locations
            UNWIND $contract_data.parties AS party
            MERGE (p:Organization {name: party.name})
            
            // Create location if available
            FOREACH (loc IN CASE WHEN party.location IS NOT NULL THEN [party.location] ELSE [] END |
                MERGE (location:Location {
                    fullAddress: coalesce(loc.address, '') + ' ' + 
                                coalesce(loc.city, '') + ' ' + 
                                coalesce(loc.state, '') + ' ' + 
                                coalesce(loc.country, '')
                })
                SET location += {
                    address: loc.address,
                    city: loc.city,
                    state: loc.state,
                    country: loc.country
                }
                MERGE (p)-[:LOCATED_AT]->(location)
            )
            
            // Link parties to the contract
            MERGE (p)-[r:PARTY_TO]->(contract)
            SET r.role = party.role
            """
            
            self.neo4j_service.execute_query(import_query, {
                "contract_id": contract_id,
                "contract_data": contract_info
            })
            
            return contract_id
            
        except Exception as e:
            print(f"Error storing contract information: {e}")
            return ""
    
    def get_all_contracts(self) -> List[Dict[str, Any]]:
        """
        Get all stored contracts
        
        Returns:
            List of contract information
        """
        try:
            query = """
            MATCH (c:Contract)
            OPTIONAL MATCH (c)<-[:PARTY_TO]-(org:Organization)
            OPTIONAL MATCH (org)-[:LOCATED_AT]->(loc:Location)
            RETURN c AS contract,
                   collect({
                       name: org.name,
                       role: [(c)<-[r:PARTY_TO]-(org) | r.role][0],
                       location: {
                           address: loc.address,
                           city: loc.city,
                           state: loc.state,
                           country: loc.country
                       }
                   }) AS parties
            ORDER BY c.extraction_timestamp DESC
            """
            
            results = self.neo4j_service.execute_query(query)
            
            contracts = []
            for result in results:
                contract_data = dict(result["contract"])
                contract_data["parties"] = [p for p in result["parties"] if p["name"]]
                contracts.append(contract_data)
            
            return contracts
            
        except Exception as e:
            return [{"error": f"Error retrieving contracts: {str(e)}"}]
    
    def get_contract_by_id(self, contract_id: str) -> Dict[str, Any]:
        """
        Get contract by ID
        
        Args:
            contract_id: Contract identifier
            
        Returns:
            Contract information
        """
        try:
            query = """
            MATCH (c:Contract {id: $contract_id})
            OPTIONAL MATCH (c)<-[:PARTY_TO]-(org:Organization)
            OPTIONAL MATCH (org)-[:LOCATED_AT]->(loc:Location)
            RETURN c AS contract,
                   collect({
                       name: org.name,
                       role: [(c)<-[r:PARTY_TO]-(org) | r.role][0],
                       location: {
                           address: loc.address,
                           city: loc.city,
                           state: loc.state,
                           country: loc.country
                       }
                   }) AS parties
            """
            
            results = self.neo4j_service.execute_query(query, {"contract_id": contract_id})
            
            if results:
                contract_data = dict(results[0]["contract"])
                contract_data["parties"] = [p for p in results[0]["parties"] if p["name"]]
                return contract_data
            else:
                return {"error": "Contract not found"}
                
        except Exception as e:
            return {"error": f"Error retrieving contract: {str(e)}"}
    
    def analyze_contract_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns in stored contracts
        
        Returns:
            Analysis results
        """
        try:
            analysis = {}
            
            # Contract types distribution
            type_query = """
            MATCH (c:Contract)
            RETURN c.contract_type AS type, count(c) AS count
            ORDER BY count DESC
            """
            type_results = self.neo4j_service.execute_query(type_query)
            analysis["contract_types"] = {item["type"]: item["count"] for item in type_results}
            
            # Organizations by contract count
            org_query = """
            MATCH (org:Organization)-[:PARTY_TO]->(c:Contract)
            RETURN org.name AS organization, count(c) AS contract_count
            ORDER BY contract_count DESC
            LIMIT 10
            """
            org_results = self.neo4j_service.execute_query(org_query)
            analysis["top_organizations"] = org_results
            
            # Average contract values
            value_query = """
            MATCH (c:Contract)
            WHERE c.total_amount IS NOT NULL
            RETURN avg(c.total_amount) AS avg_value, 
                   min(c.total_amount) AS min_value,
                   max(c.total_amount) AS max_value,
                   count(c) AS contracts_with_value
            """
            value_results = self.neo4j_service.execute_query(value_query)
            if value_results:
                analysis["contract_values"] = value_results[0]
            
            # Geographic distribution
            geo_query = """
            MATCH (loc:Location)<-[:LOCATED_AT]-(org:Organization)-[:PARTY_TO]->(c:Contract)
            RETURN loc.country AS country, count(DISTINCT c) AS contract_count
            ORDER BY contract_count DESC
            """
            geo_results = self.neo4j_service.execute_query(geo_query)
            analysis["geographic_distribution"] = geo_results
            
            return analysis
            
        except Exception as e:
            return {"error": f"Error analyzing contract patterns: {str(e)}"}
    
    def search_contracts(self, search_term: str, search_type: str = "all") -> List[Dict[str, Any]]:
        """
        Search contracts by various criteria
        
        Args:
            search_term: Term to search for
            search_type: Type of search (all, organization, type, scope)
            
        Returns:
            List of matching contracts
        """
        try:
            if search_type == "organization":
                query = """
                MATCH (org:Organization)-[:PARTY_TO]->(c:Contract)
                WHERE toLower(org.name) CONTAINS toLower($search_term)
                RETURN c AS contract, org.name AS matched_organization
                ORDER BY c.extraction_timestamp DESC
                """
            elif search_type == "type":
                query = """
                MATCH (c:Contract)
                WHERE toLower(c.contract_type) CONTAINS toLower($search_term)
                RETURN c AS contract, c.contract_type AS matched_type
                ORDER BY c.extraction_timestamp DESC
                """
            elif search_type == "scope":
                query = """
                MATCH (c:Contract)
                WHERE toLower(c.contract_scope) CONTAINS toLower($search_term)
                RETURN c AS contract, c.contract_scope AS matched_scope
                ORDER BY c.extraction_timestamp DESC
                """
            else:  # search all fields
                query = """
                MATCH (c:Contract)
                OPTIONAL MATCH (c)<-[:PARTY_TO]-(org:Organization)
                WHERE toLower(c.contract_type) CONTAINS toLower($search_term)
                   OR toLower(c.contract_scope) CONTAINS toLower($search_term)
                   OR toLower(org.name) CONTAINS toLower($search_term)
                RETURN DISTINCT c AS contract
                ORDER BY c.extraction_timestamp DESC
                """
            
            results = self.neo4j_service.execute_query(query, {"search_term": search_term})
            
            contracts = []
            for result in results:
                contract_data = dict(result["contract"])
                contracts.append(contract_data)
            
            return contracts
            
        except Exception as e:
            return [{"error": f"Error searching contracts: {str(e)}"}]
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def validate_contract_data(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted contract data
        
        Args:
            contract_data: Contract data to validate
            
        Returns:
            Validation results
        """
        try:
            validation_results = {
                "is_valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Required fields validation
            required_fields = ["contract_type", "parties", "effective_date", "contract_scope"]
            for field in required_fields:
                if field not in contract_data or not contract_data[field]:
                    validation_results["errors"].append(f"Missing required field: {field}")
                    validation_results["is_valid"] = False
            
            # Date format validation
            if "effective_date" in contract_data:
                try:
                    from datetime import datetime
                    datetime.strptime(contract_data["effective_date"], "%Y-%m-%d")
                except ValueError:
                    validation_results["warnings"].append("Effective date format should be YYYY-MM-DD")
            
            # Parties validation
            if "parties" in contract_data and isinstance(contract_data["parties"], list):
                if len(contract_data["parties"]) < 2:
                    validation_results["warnings"].append("Contract should have at least 2 parties")
                
                for i, party in enumerate(contract_data["parties"]):
                    if not isinstance(party, dict) or "name" not in party:
                        validation_results["errors"].append(f"Party {i+1} missing name")
                        validation_results["is_valid"] = False
            
            return validation_results
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
