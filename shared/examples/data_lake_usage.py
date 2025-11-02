"""
Data Lake Usage Example

This example demonstrates how to use the data lake module to store,
retrieve, and manage various types of enterprise data artifacts.
"""

import asyncio
import tempfile
from pathlib import Path

from shared import DiskDataLake, DataType


async def main():
    """Demonstrate data lake usage."""
    
    # Create a temporary data lake for this example
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Creating data lake in: {temp_dir}")
        data_lake = DiskDataLake(temp_dir)
        
        print("\n=== Storing Database Schemas ===")
        
        # Store database schema
        schema_entry = await data_lake.store(
            name="user_schema.sql",
            content="""
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    term_sheet_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_term_sheet ON users(term_sheet_id);
            """.strip(),
            data_type=DataType.SCHEMA,
            metadata={
                "version": "2.1",
                "database": "production",
                "description": "User accounts table with term sheet reference"
            }
        )
        
        print(f"+ Stored schema: {schema_entry.name} (ID: {schema_entry.id[:8]}...)")
        
        print("\n=== Storing Excel Macros ===")
        
        # Store Excel macro with subpath
        macro_entry = await data_lake.store(
            name="term_sheet_generator.vba",
            content='''Sub GenerateTermSheet()
    Dim termSheetId As String
    Dim clientName As String
    
    ' Get data from user input
    termSheetId = InputBox("Enter Term Sheet ID:")
    clientName = InputBox("Enter Client Name:")
    
    ' Generate new term sheet
    Sheets("TermSheet").Range("A1").Value = termSheetId
    Sheets("TermSheet").Range("B1").Value = clientName
    Sheets("TermSheet").Range("C1").Value = Now()
    
    MsgBox "Term Sheet generated successfully!", vbInformation
End Sub

Function ValidateTermSheet(id As String) As Boolean
    ' Validate term sheet format
    If Len(id) <> 10 Then
        ValidateTermSheet = False
        Exit Function
    End If
    
    ValidateTermSheet = True
End Function''',
            data_type=DataType.MACRO,
            subpath="finance/2023-10-27",
            metadata={
                "author": "finance_team",
                "purpose": "Generate and validate term sheets",
                "excel_version": "2016+"
            }
        )
        
        print(f"+ Stored macro: {macro_entry.name} (ID: {macro_entry.id[:8]}...)")
        print(f"  Path: {macro_entry.file_path}")
        
        print("\n=== Storing Configuration ===")
        
        # Store configuration file
        config_entry = await data_lake.store(
            name="payment_service_config.json",
            content="""{
    "service_name": "payment-service",
    "version": "1.2.3",
    "database": {
        "host": "prod-db.company.com",
        "port": 5432,
        "name": "payments",
        "ssl_mode": "require"
    },
    "api_endpoints": {
        "create_payment": "/api/v1/payments",
        "get_payment": "/api/v1/payments/{id}",
        "refund_payment": "/api/v1/payments/{id}/refund"
    },
    "features": {
        "term_sheet_validation": true,
        "client_verification": true,
        "automatic_refunds": false
    }
}""",
            data_type=DataType.CONFIGURATION,
            metadata={
                "environment": "production",
                "last_reviewed": "2023-10-15",
                "reviewed_by": "devops_team"
            }
        )
        
        print(f"+ Stored config: {config_entry.name} (ID: {config_entry.id[:8]}...)")
        
        print("\n=== Searching for Data ===")
        
        # Search for term sheet related data
        term_sheet_results = await data_lake.search("term sheet")
        print(f"Found {len(term_sheet_results)} entries containing 'term sheet':")
        for result in term_sheet_results:
            print(f"  - {result.name} ({result.data_type.value})")
        
        # Search for user-related schemas
        user_schema_results = await data_lake.search("CREATE TABLE users", DataType.SCHEMA)
        print(f"\nFound {len(user_schema_results)} user schemas:")
        for result in user_schema_results:
            print(f"  - {result.name}: {result.metadata.get('description', 'No description')}")
        
        print("\n=== Listing by Data Type ===")
        
        # List all schemas
        schemas = await data_lake.list(data_type=DataType.SCHEMA)
        print(f"All schemas ({len(schemas)}):")
        for schema in schemas:
            print(f"  - {schema.name} (v{schema.metadata.get('version', 'unknown')})")
        
        # List all macros
        macros = await data_lake.list(data_type=DataType.MACRO)
        print(f"\nAll macros ({len(macros)}):")
        for macro in macros:
            print(f"  - {macro.name} ({macro.metadata.get('author', 'unknown author')})")
        
        print("\n=== Retrieving Specific Data ===")
        
        # Retrieve the macro by path
        retrieved_macro = await data_lake.retrieve_by_path(macro_entry.file_path)
        print(f"Retrieved macro: {retrieved_macro.name}")
        print(f"Content preview: {retrieved_macro.content[:100]}...")
        print(f"Author: {retrieved_macro.metadata.get('author', 'unknown')}")
        
        print("\n=== Updating Data ===")
        
        # Update the macro with new version
        updated_macro = await data_lake.update(
            retrieved_macro.id,
            content=retrieved_macro.content + "\n\n' Added new validation function\nSub NewValidation()\n    ' New functionality\nEnd Sub",
            metadata={"version": "2.0", "last_updated": "2023-10-27"}
        )
        
        print(f"+ Updated macro: {updated_macro.name}")
        print(f"  Version: {updated_macro.metadata.get('version', 'unknown')}")
        print(f"  Updated at: {updated_macro.updated_at}")
        
        print("\n=== Data Lake Statistics ===")
        
        # Get data lake statistics
        stats = await data_lake.get_stats()
        print(f"Total entries: {stats['total_entries']}")
        print(f"Total size: {stats['total_size_mb']} MB")
        print("Entries by type:")
        for data_type, count in stats['entries_by_type'].items():
            print(f"  - {data_type}: {count}")
        
        print(f"Created entries: {stats['created_entries']}")
        print(f"Updated entries: {stats['updated_entries']}")
        
        print("\n=== Example Complete ===")
        print("Data lake operations demonstrated successfully!")


if __name__ == "__main__":
    asyncio.run(main())