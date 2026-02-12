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
            fontSize=12,
            spaceAfter=6
        )
        self.title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Normal'],
            alignment=1,
            fontSize=12,
            bold=True,
            spaceAfter=6
        )
        self.normal_style = self.styles['Normal']
        
    def generate_bar_pdf(self, metadata, summary_df, ba_name, year, counterpart_pic=None):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        elements = []
        
        # Adjust normal style to size 11 and justify
        self.normal_style.fontSize = 11
        self.normal_style.leading = 14
        self.normal_style.alignment = 4  # TA_JUSTIFY
        
        # 1. Header
        elements.append(Paragraph("BERITA ACARA", self.header_style))
        elements.append(Paragraph("REKONSILIASI DAN PEMUTAKHIRAN DATA BARANG MILIK NEGARA", self.header_style))
        elements.append(Paragraph(f"PADA {ba_name}", self.header_style))
        elements.append(Paragraph(f"PERIODE TAHUN {year}", self.header_style))
        
        elements.append(Spacer(1, 0.2 * inch))
        
        # 2. Opening & Officer Details (Pihak Pertama & Pihak Kedua)
        from datetime import datetime
        import locale
        
        # Try to set locale for Indonesian date
        try:
            locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
        except:
            pass # Fallback to default
            
        now = datetime.now()
        day_str = now.strftime("%A")
        date_str = now.strftime("%d %B %Y")
        
        # Map English days to Indonesian if locale failed
        day_map = {
            "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis",
            "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
        }
        day_in = day_map.get(day_str, day_str)
        
        narrative_header = f"""
        Pada hari ini <b>{day_in}, tanggal {date_str}</b> bertempat di Jakarta, kami yang bertanda tangan di bawah ini:
        """
        elements.append(Paragraph(narrative_header, self.normal_style))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Pihak Pertama (Counterpart PKKN)
        p1_name = counterpart_pic.nama_pic if (counterpart_pic and counterpart_pic.nama_pic) else "................"
        p1_nip = counterpart_pic.nip_pic if (counterpart_pic and counterpart_pic.nip_pic) else "................"
        p1_jab = counterpart_pic.jabatan_pic if (counterpart_pic and counterpart_pic.jabatan_pic) else "Petugas Akuntansi"
        
        pihak_1 = f"""
        <b>I. Pihak Pertama</b><br/>
        Nama &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {p1_name}<br/>
        NIP &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {p1_nip}<br/>
        Jabatan &nbsp;&nbsp;&nbsp;: {p1_jab}<br/>
        Dalam hal ini bertindak untuk dan atas nama Pengelola Barang pada Kantor Pusat Direktorat Jenderal Kekayaan Negara.
        """
        elements.append(Paragraph(pihak_1, self.normal_style))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Pihak Kedua (Assigned Officer K/L)
        p2_name = metadata.nama_petugas if (metadata and metadata.nama_petugas) else "................"
        p2_nip = metadata.nip_petugas if (metadata and metadata.nip_petugas) else "................"
        p2_jab = metadata.jabatan_petugas if (metadata and metadata.jabatan_petugas) else "Penanggung Jawab"
        
        pihak_2 = f"""
        <b>II. Pihak Kedua</b><br/>
        Nama &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {p2_name}<br/>
        NIP &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {p2_nip}<br/>
        Jabatan &nbsp;&nbsp;&nbsp;: {p2_jab}<br/>
        Dalam hal ini bertindak untuk dan atas nama penanggung jawab Unit Akuntansi Pengguna Barang pada {ba_name}.
        """
        elements.append(Paragraph(pihak_2, self.normal_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Final Statement
        statement = f"""
        Menyatakan bahwa telah melakukan Rekonsiliasi dan Pemutakhiran Data terkait Barang Milik Negara (BMN) pada {ba_name} dengan cara membandingkan data BMN pada Laporan Barang Pengguna (LBP) dan Laporan Barang Milik Negara (LBMN) periode Tahun {year} dengan hasil sebagai berikut:
        """
        elements.append(Paragraph(statement, self.normal_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # 3. Table
        # ... (keep existing table logic)
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
        
        # Table Styling - Utilizing ~6.8 inches width
        t = Table(table_data, colWidths=[2.8*inch, 1.35*inch, 1.35*inch, 1.35*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, 1), colors.whitesmoke), # Part I header
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
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
        elements.append(Spacer(1, 0.3 * inch))
        
        # 3.5 Closing Text
        closing_text = f"""
        Hal-hal penting lainnya mengenai data BMN terkait penyusunan LBP dan LKPP disajikan dalam Lampiran Berita Acara ini, yang merupakan bagian yang tidak terpisahkan dari Berita Acara ini.
        <br/><br/>
        Demikian Berita Acara Rekonsiliasi ini dibuat untuk bahan penyusunan Laporan BMN dan LKPP periode Tahun {year}, dan apabila di kemudian hari terdapat kekeliruan akan dilakukan perbaikan sebagaimana mestinya.
        """
        elements.append(Paragraph(closing_text, self.normal_style))
        elements.append(Spacer(1, 0.4 * inch))
        
        # 4. Signatures
        # Calculate available width (8.27in - 2*0.7in margins = 6.87in)
        # Divide equally: ~3.43in each
        col_width = 3.4 * inch
        
        # Style for signature cells
        sig_cell_style = ParagraphStyle(
            'SigCell',
            parent=self.normal_style,
            alignment=1, # Center
            fontSize=11,
            leading=13
        )
        
        sig_grey_style = ParagraphStyle(
            'SigGrey',
            parent=sig_cell_style,
            textColor=colors.grey,
            fontSize=8,
            italic=True
        )

        # Prepare Jabatan Paragraphs (to support wrapping)
        p1_jab_para = Paragraph(counterpart_pic.jabatan_pic if (counterpart_pic and counterpart_pic.jabatan_pic) else "Petugas Akuntansi,", sig_cell_style)
        p2_jab_para = Paragraph(metadata.jabatan_petugas if (metadata and metadata.jabatan_petugas) else "Penanggung Jawab,", sig_cell_style)
        
        # Electronic Sign Labels
        is_p2_elektronik = metadata and metadata.jenis_ttd == "Elektronik"
        p2_esign = Paragraph("<i>Ditandatangani secara elektronik</i>", sig_grey_style) if is_p2_elektronik else ""
        p1_esign = Paragraph("<i>Ditandatangani secara elektronik</i>", sig_grey_style) # Default PKKN is elektronik

        sig_data = [
            [p2_jab_para, p1_jab_para],
            ["", ""],
            ["", ""],
            ["", ""],
            [p2_esign, p1_esign],
            [Paragraph(f"<b>( {metadata.nama_petugas if (metadata and metadata.nama_petugas) else '................'} )</b>", sig_cell_style), 
             Paragraph(f"<b>( {counterpart_pic.nama_pic if (counterpart_pic and counterpart_pic.nama_pic) else '................'} )</b>", sig_cell_style)],
            [Paragraph(f"NIP {metadata.nip_petugas if (metadata and metadata.nip_petugas) else '................'}", sig_cell_style), 
             Paragraph(f"NIP {counterpart_pic.nip_pic if (counterpart_pic and counterpart_pic.nip_pic) else '................'}", sig_cell_style)]
        ]
        
        sig_table = Table(sig_data, colWidths=[col_width, col_width])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 0), # Row 1 (Jabatan)
            ('BOTTOMPADDING', (0, 1), (-1, 1), 5), # Row 2 (E-sign label)
            ('BOTTOMPADDING', (0, 3), (-1, 3), 15), # Increase gap before name
        ]))
        elements.append(sig_table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
