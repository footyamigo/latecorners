#!/usr/bin/env python3
"""
Alert Tracking Database - PostgreSQL for Railway
================================================
Persistent storage for elite corner alerts and their results.
Now using PostgreSQL for guaranteed data persistence on Railway.
"""

# Import PostgreSQL database implementation
from database_postgres import get_database

# Export the get_database function for backward compatibility
__all__ = ['get_database'] 