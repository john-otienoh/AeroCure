from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Airstrip(Base):
    __tablename__ = "airstrips"

    icao_code = Column(String(10), primary_key=True)
    iata_code = Column(String(10), nullable=True)

    name = Column(String(200), nullable=False)
    airport_type = Column(String(30), nullable=True)       

    city = Column(String(80), nullable=True)               
    county = Column(String(80), nullable=True)         
    county_code = Column(String(80), nullable=True)      

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    elevation_ft = Column(Integer, nullable=True)

    scheduled_service = Column(Boolean, nullable=True) 
    agent_phone = Column(String(20), nullable=True)        

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # def __repr__(self) -> str:
    #     data = {
    #         "icao": self.icao_code,
    #         "iata": self.iata_code,
    #         "name": self.name,
    #         "type": self.airport_type,
    #         "city": self.city,
    #         "county": self.county,
    #         "county_code": self.county_code,
    #         "lat": self.latitude,
    #         "long": self.longitude,
    #         "elev": self.elevation_ft,
    #         "sS": self.scheduled_service,
    #         "agent_phone": self.agent_phone,
    #         "update": self.updated_at,
    #     }
    #     return f"Data: {data}"
    def __repr__(self) -> str:
        return f"{self.icao_code} - {self.name} - {self.county}"