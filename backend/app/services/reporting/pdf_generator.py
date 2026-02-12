import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch

class BARPDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.header_style = ParagraphStyle(
            'Header',
            parent=self.styles['Heading1'],
            alignment=1, # Center
            fontSize=14,
            spaceAfter=12
        )
        self.title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Normal'],
            alignment=1,
            fontSize=12,
            bold=True,
            spaceAfter=10
        )
        self.normal_style = self.styles['Normal']
        
    def generate_bar_pdf(self, metadata, summary_df, ba_name, year, counterpart_pic=None):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        
        # 1. Header
        elements.append(Paragraph("BERITA ACARA REKONSILIASI (BAR)", self.header_style))
        elements.append(Paragraph(f"Tingkat Unit Akuntansi Kuasa Pengguna Barang (UAKPB)", self.title_style))
        elements.append(Paragraph(f"Tahun Anggaran {year}", self.title_style))
        elements.append(Paragraph(f"Satker: {ba_name}", self.title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # 2. Officer Details
        officer_text = f"""
        Pada hari ini .................., tanggal ........ bulan ................. tahun ................., 
        bertempat di .................................., kami yang bertanda tangan di bawah ini:
        <br/><br/>
        Nama: {metadata.nama_petugas if metadata else '................'} <br/>
        NIP: {metadata.nip_petugas if metadata else '................'} <br/>
        Jabatan: {metadata.jenis_ttd if metadata else '................'}
        """
        elements.append(Paragraph(officer_text, self.normal_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # 3. Table
        # Prepare data for reportlab table
        table_data = [["Category", "Saldo Awal", "Mutasi", "Saldo Akhir"]]
        
        # Helper to format numbers
        def fmt(x):
            try:
                return "{:,.2f}".format(float(x))
            except:
                return str(x)

        # Separate Part I and II
        part1 = summary_df[summary_df['Part'] == 'I - Neraca']
        part2 = summary_df[summary_df['Part'] == 'II - Non Neraca']
        
        table_data.append(["I. POSISI BMN DI NERACA", "", "", ""])
        for _, row in part1.iterrows():
            table_data.append([row['Category'], fmt(row['Saldo Awal']), fmt(row['Mutasi']), fmt(row['Saldo Akhir'])])
            
        table_data.append(["II. BMN NON NERACA", "", "", ""])
        for _, row in part2.iterrows():
            table_data.append([row['Category'], fmt(row['Saldo Awal']), fmt(row['Mutasi']), fmt(row['Saldo Akhir'])])
            
        # Grand Total
        total_awal = summary_df['Saldo Awal'].sum()
        total_mutasi = summary_df['Mutasi'].sum()
        total_akhir = summary_df['Saldo Akhir'].sum()
        table_data.append(["TOTAL (I + II)", fmt(total_awal), fmt(total_mutasi), fmt(total_akhir)])
        
        # Table Styling
        t = Table(table_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'), # Labels
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.whitesmoke), # Part I header
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # TOTAL Row bold
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))
        
        # Style for Part II header
        p2_idx = len(part1) + 2
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, p2_idx), (-1, p2_idx), colors.whitesmoke),
            ('FONTNAME', (0, p2_idx), (-1, p2_idx), 'Helvetica-Bold'),
        ]))
        
        elements.append(t)
        elements.append(Spacer(1, 0.5 * inch))
        
        # 4. Signatures
        sig_data = [
            ["Disetujui Oleh:", "", "Petugas Akuntansi,"],
            [ba_name if ba_name else "Unit Terkait", "", counterpart_pic.nama_pic if (counterpart_pic and counterpart_pic.nama_pic) else "................"],
            ["", "", ""],
            ["", "", ""],
            ["( ................................ )", "", f"( {counterpart_pic.nama_pic if (counterpart_pic and counterpart_pic.nama_pic) else '................'} )"],
            ["NIP ............................", "", f"NIP {counterpart_pic.nip_pic if (counterpart_pic and counterpart_pic.nip_pic) else '................'}"]
        ]
        sig_table = Table(sig_data, colWidths=[2.5*inch, 1.0*inch, 2.5*inch])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(sig_table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
