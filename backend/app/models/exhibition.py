from sqlalchemy import Column, Integer, String, Text, Float
from app.db.session import Base

class Exhibition(Base):
    __tablename__ = "exhibitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    location_x = Column(Float)
    location_y = Column(Float)
    category = Column(String)
    location_name = Column(String)
    duration_minutes = Column(Integer, default=15)
    recommended_for = Column(String)
    cautions = Column(Text)
    stage_start_time = Column(String)
    ticket_status = Column(String)
    capacity_status = Column(String)
