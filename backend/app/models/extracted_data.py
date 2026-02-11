from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class ExtractedEntry(Base):
    __tablename__ = "extracted_entries"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String, index=True)  # Grouping by upload session/batch
    
    kode_akun = Column(String, ForeignKey("ref_accounts.kode_akun"))
    
    # Financial Value
    nilai = Column(Numeric, nullable=True)
    
    tahun_anggaran = Column(Integer, nullable=False)
    
    kode_ba = Column(String, ForeignKey("ref_organizations.kode_ba"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    account = relationship("ReferenceAccount")
    organization = relationship("ReferenceOrganization")
