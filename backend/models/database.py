"""
Database models and initialization for Amazon Product Analysis System

This module contains SQLAlchemy models for storing analysis results
and database initialization functions.
"""

import os
from typing import Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean, Float, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./amazon_analyzer.db"
)

# Create engine and session
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class AnalysisSession(Base):
    """
    Model for storing analysis session information
    """
    __tablename__ = "analysis_sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    amazon_url = Column(String, nullable=False)
    status = Column(String, nullable=False, default="started")  # started, running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Analysis results (stored as JSON)
    main_product_data = Column(JSON, nullable=True)
    competitor_data = Column(JSON, nullable=True)
    product_analysis = Column(Text, nullable=True)
    competitor_analysis = Column(Text, nullable=True)
    market_positioning = Column(Text, nullable=True)
    optimization_strategy = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProductData(Base):
    """
    Model for storing scraped product data
    """
    __tablename__ = "product_data"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    asin = Column(String, index=True)
    url = Column(String, nullable=False)
    
    # Product information
    title = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)
    specifications = Column(Text, nullable=True)
    
    # Reviews and ratings
    reviews = Column(JSON, nullable=True)  # Array of review texts
    rating = Column(Float, nullable=True)
    review_count = Column(String, nullable=True)
    
    # Processing metadata
    is_main_product = Column(Boolean, default=False)
    is_competitor = Column(Boolean, default=False)
    scrape_success = Column(Boolean, default=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentProgress(Base):
    """
    Model for storing agent progress updates
    """
    __tablename__ = "agent_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    agent_name = Column(String, nullable=False)  # data_collector, market_analyzer, optimization_advisor
    status = Column(String, nullable=False)  # working, completed, error
    progress = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    current_task = Column(String, nullable=False)
    thinking_step = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    result_data = Column(JSON, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)


# Database dependency
def get_db():
    """
    Dependency function for getting database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """
    Initialize database tables
    """
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Test connection
        db = SessionLocal()
        try:
            # Simple query to test connection
            db.execute("SELECT 1")
            print("✅ Database connection test successful")
        except Exception as e:
            print(f"⚠️  Database connection test failed: {e}")
            print("   Using in-memory storage as fallback")
        finally:
            db.close()
            
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        print("   Using in-memory storage as fallback")


# Database utility functions
class DatabaseManager:
    """
    Utility class for database operations
    """
    
    @staticmethod
    def save_analysis_session(session_id: str, amazon_url: str, status: str = "started"):
        """Save a new analysis session"""
        try:
            db = SessionLocal()
            session = AnalysisSession(
                session_id=session_id,
                amazon_url=amazon_url,
                status=status
            )
            db.add(session)
            db.commit()
            db.close()
            return True
        except Exception as e:
            print(f"Error saving analysis session: {e}")
            return False
    
    @staticmethod
    def update_analysis_session(session_id: str, **updates):
        """Update analysis session with new data"""
        try:
            db = SessionLocal()
            session = db.query(AnalysisSession).filter(
                AnalysisSession.session_id == session_id
            ).first()
            
            if session:
                for key, value in updates.items():
                    if hasattr(session, key):
                        setattr(session, key, value)
                
                session.updated_at = datetime.utcnow()
                db.commit()
                db.close()
                return True
            
            db.close()
            return False
        except Exception as e:
            print(f"Error updating analysis session: {e}")
            return False
    
    @staticmethod
    def save_product_data(session_id: str, product_data: dict, is_main: bool = False):
        """Save scraped product data"""
        try:
            db = SessionLocal()
            product = ProductData(
                session_id=session_id,
                asin=product_data.get("asin"),
                url=product_data.get("url", ""),
                title=product_data.get("title"),
                brand=product_data.get("brand"),
                price=product_data.get("price"),
                currency=product_data.get("currency"),
                description=product_data.get("description"),
                color=product_data.get("color"),
                specifications=product_data.get("spec"),
                reviews=product_data.get("reviews", []),
                is_main_product=is_main,
                is_competitor=not is_main,
                scrape_success=product_data.get("success", True)
            )
            db.add(product)
            db.commit()
            db.close()
            return True
        except Exception as e:
            print(f"Error saving product data: {e}")
            return False
    
    @staticmethod
    def save_agent_progress(session_id: str, agent_name: str, status: str, 
                          progress: float, current_task: str, **kwargs):
        """Save agent progress update"""
        try:
            db = SessionLocal()
            progress_record = AgentProgress(
                session_id=session_id,
                agent_name=agent_name,
                status=status,
                progress=progress,
                current_task=current_task,
                thinking_step=kwargs.get("thinking_step"),
                error_message=kwargs.get("error_message"),
                result_data=kwargs.get("result_data")
            )
            db.add(progress_record)
            db.commit()
            db.close()
            return True
        except Exception as e:
            print(f"Error saving agent progress: {e}")
            return False
    
    @staticmethod
    def get_analysis_session(session_id: str):
        """Get analysis session by ID"""
        try:
            db = SessionLocal()
            session = db.query(AnalysisSession).filter(
                AnalysisSession.session_id == session_id
            ).first()
            db.close()
            return session
        except Exception as e:
            print(f"Error getting analysis session: {e}")
            return None
    
    @staticmethod
    def get_session_products(session_id: str):
        """Get all products for a session"""
        try:
            db = SessionLocal()
            products = db.query(ProductData).filter(
                ProductData.session_id == session_id
            ).all()
            db.close()
            return products
        except Exception as e:
            print(f"Error getting session products: {e}")
            return []


# Initialize database manager instance
db_manager = DatabaseManager()