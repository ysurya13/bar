from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class ExtractedEntry(Base):
    __tablename__ = "extracted_entries"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String, index=True)  # Grouping by upload session/batch
    data_category = Column(String, index=True)  # e.g., "Neraca", "Saldo Awal", "Penyusutan"
    
    kode_akun = Column(String, index=True)
    uraian_akun = Column(String)  # Denormalized for convenience
    
    # Financial Value
    nilai = Column(Numeric, nullable=True)
    
    tahun_anggaran = Column(Integer, nullable=False)
    
    kode_ba = Column(String, index=True)
    uraian_ba = Column(String)  # Denormalized for convenience
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BARMetadata(Base):
    __tablename__ = "bar_metadata"

    id = Column(Integer, primary_key=True, index=True)
    kode_ba = Column(String, index=True)
    tahun_anggaran = Column(Integer, index=True)
    
    nama_petugas = Column(String)
    nip_petugas = Column(String)
    jabatan_petugas = Column(String)
    jenis_ttd = Column(String)  # "Elektronik" or "Manual"
    
    catatan_kualitatif = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
class BARNonNeraca(Base):
    __tablename__ = "bar_non_neraca"

    id = Column(Integer, primary_key=True, index=True)
    kode_ba = Column(String, index=True)
    tahun_anggaran = Column(Integer, index=True)
    label = Column(String)
    nilai_awal = Column(Numeric(precision=20, scale=2), default=0.0)
    nilai_akhir = Column(Numeric(precision=20, scale=2), default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class OrganizationPIC(Base):
    __tablename__ = "organization_pics"

    id = Column(Integer, primary_key=True, index=True)
    kode_ba = Column(String, index=True)
    nama_pic = Column(String)
    nip_pic = Column(String)
    jabatan_pic = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

