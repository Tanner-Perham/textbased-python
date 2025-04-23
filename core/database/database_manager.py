"""
Database manager for handling SQLite operations.
"""

import os
import sqlite3
import json
from typing import Any, Dict, List, Optional
from .schema import CREATE_TABLES

class DatabaseManager:
    """Manages database operations for the game."""
    
    def __init__(self, db_path: str = "game_data.db"):
        """Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self) -> None:
        """Connect to the database and initialize the cursor."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            
    def initialize_database(self) -> None:
        """Initialize the database by creating all necessary tables."""
        self.connect()
        try:
            for create_table in CREATE_TABLES:
                self.cursor.execute(create_table)
            self.conn.commit()
        finally:
            self.close()
            
    def clear_all_tables(self) -> None:
        """Clear all data from all tables."""
        self.connect()
        try:
            # Get all table names
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in self.cursor.fetchall()]
            
            # Disable foreign key constraints temporarily
            self.cursor.execute("PRAGMA foreign_keys=OFF")
            
            # Clear each table
            for table in tables:
                self.cursor.execute(f"DELETE FROM {table}")
                
            # Re-enable foreign key constraints
            self.cursor.execute("PRAGMA foreign_keys=ON")
            
            self.conn.commit()
        finally:
            self.close()
            
    def drop_all_tables(self) -> None:
        """Drop all tables from the database."""
        self.connect()
        try:
            # Get all table names, excluding system tables
            self.cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
                AND name NOT LIKE 'android_%'
            """)
            tables = [row[0] for row in self.cursor.fetchall()]
            
            # Disable foreign key constraints temporarily
            self.cursor.execute("PRAGMA foreign_keys=OFF")
            
            # Drop each table
            for table in tables:
                self.cursor.execute(f"DROP TABLE IF EXISTS {table}")
                
            # Re-enable foreign key constraints
            self.cursor.execute("PRAGMA foreign_keys=ON")
            
            self.conn.commit()
        finally:
            self.close()
            
    def create_tables(self) -> None:
        """Create all tables using the schema."""
        self.connect()
        try:
            for create_table in CREATE_TABLES:
                self.cursor.execute(create_table)
            self.conn.commit()
        finally:
            self.close()
            
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return the results as a list of dictionaries.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            List of dictionaries containing the query results
        """
        self.connect()
        try:
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
        finally:
            self.close()
            
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
        """
        self.connect()
        try:
            self.cursor.executemany(query, params_list)
            self.conn.commit()
        finally:
            self.close()
            
    def insert_data(self, table: str, data: Dict[str, Any]) -> int:
        """Insert a single row of data into a table.
        
        Args:
            table: Name of the table to insert into
            data: Dictionary of column names and values
            
        Returns:
            ID of the inserted row
        """
        self.connect()
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join("?" * len(data))
            query = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, tuple(data.values()))
            self.conn.commit()
            return self.cursor.lastrowid
        finally:
            self.close()
            
    def update_data(self, table: str, id_value: int, data: Dict[str, Any]) -> None:
        """Update data in a table.
        
        Args:
            table: Name of the table to update
            id_value: ID of the row to update
            data: Dictionary of column names and new values
        """
        self.connect()
        try:
            set_clause = ", ".join(f"{k} = ?" for k in data.keys())
            query = f"UPDATE {table} SET {set_clause} WHERE id = ?"
            params = tuple(data.values()) + (id_value,)
            self.cursor.execute(query, params)
            self.conn.commit()
        finally:
            self.close()
            
    def delete_data(self, table: str, where: str, where_params: tuple = ()) -> None:
        """Delete data from a table.
        
        Args:
            table: Name of the table to delete from
            where: WHERE clause for the delete
            where_params: Parameters for the WHERE clause
        """
        self.connect()
        try:
            query = f"DELETE FROM {table} WHERE {where}"
            self.cursor.execute(query, where_params)
            self.conn.commit()
        finally:
            self.close()
            
    def get_by_id(self, table: str, id_value: Any) -> Optional[Dict[str, Any]]:
        """Get a single row by its ID.
        
        Args:
            table: Name of the table to query
            id_value: ID value to search for
            
        Returns:
            Dictionary containing the row data, or None if not found
        """
        self.connect()
        try:
            query = f"SELECT * FROM {table} WHERE id = ?"
            self.cursor.execute(query, (id_value,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        finally:
            self.close()
            
    def get_all(self, table: str) -> List[Dict[str, Any]]:
        """Get all rows from a table.
        
        Args:
            table: Name of the table to query
            
        Returns:
            List of dictionaries containing the row data
        """
        self.connect()
        try:
            query = f"SELECT * FROM {table}"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
        finally:
            self.close()
            
    def get_related(self, table: str, foreign_key: str, foreign_id: Any) -> List[Dict[str, Any]]:
        """Get all rows from a table that are related to a foreign key.
        
        Args:
            table: Name of the table to query
            foreign_key: Name of the foreign key column
            foreign_id: ID value to search for
            
        Returns:
            List of dictionaries containing the row data
        """
        self.connect()
        try:
            query = f"SELECT * FROM {table} WHERE {foreign_key} = ?"
            self.cursor.execute(query, (foreign_id,))
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
        finally:
            self.close() 