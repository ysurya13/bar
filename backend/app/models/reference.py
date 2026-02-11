from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class ReferenceAccount(Base):
    __tablename__ = "ref_accounts"

    kode_akun = Column(String, primary_key=True, index=True)
    uraian_akun = Column(String, nullable=False)
    kategori = Column(String)  # e.g., "Neraca", "Laporan Operasional"

class ReferenceOrganization(Base):
    __tablename__ = "ref_organizations"

    kode_ba = Column(String, primary_key=True, index=True)
    uraian_ba = Column(String, nullable=False)

class ReferenceStaff(Base):
    __tablename__ = "ref_staff"

    id = Column(Integer, primary_key=True, index=True)
    kode_ba = Column(String, ForeignKey("ref_organizations.kode_ba"))
    
    nama_penandatangan = Column(String)
    nip_penandatangan = Column(String)
    
    pic_seksi = Column(String)
    pic_subdit = Column(String)
    
    # Hierarchy reference (optional self-reference or separate table if complex)
    # For now, simplistic flat structure as per requirements
    nama_kasubdit = Column(String)
    nip_kasubdit = Column(String)

    organization = relationship("ReferenceOrganization")
