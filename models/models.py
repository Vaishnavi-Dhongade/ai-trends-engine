from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from config.database import Base

# Tools table
class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(Text)
    website_url = Column(String)
    source_url = Column(String)
    category = Column(String)
    pricing = Column(String)
    tags = Column(String)
    date_found = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Trends table
class Trend(Base):
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    category = Column(String)
    summary = Column(Text)
    growth_score = Column(Float, default=0)
    search_growth = Column(Float, default=0)
    social_growth = Column(Float, default=0)
    product_velocity = Column(Float, default=0)
    status = Column(String, default="new")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Trend Snapshots table
class TrendSnapshot(Base):
    __tablename__ = "trend_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    trend_id = Column(Integer, ForeignKey("trends.id"))
    date = Column(DateTime, default=func.now())
    search_score = Column(Float, default=0)
    social_mentions = Column(Integer, default=0)
    product_votes = Column(Integer, default=0)
    product_comments = Column(Integer, default=0)
    overall_score = Column(Float, default=0)

# Tool Trend Map table
class ToolTrendMap(Base):
    __tablename__ = "tool_trend_map"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id"))
    trend_id = Column(Integer, ForeignKey("trends.id"))