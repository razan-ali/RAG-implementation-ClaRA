import os
import uuid
from typing import List, Tuple
from pathlib import Path
import PyPDF2
from docx import Document
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter

from models import DocumentType, DocumentMetadata, DocumentChunk
from config import settings


class DocumentProcessor:
    """Process and chunk documents for RAG"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def process_document(
        self,
        file_path: str,
        filename: str
    ) -> Tuple[DocumentMetadata, List[DocumentChunk]]:
        """Process a document and return metadata and chunks"""

        # Determine document type
        file_ext = Path(filename).suffix.lower().replace('.', '')
        try:
            doc_type = DocumentType(file_ext)
        except ValueError:
            raise ValueError(f"Unsupported file type: {file_ext}")

        # Extract text based on document type
        text = self._extract_text(file_path, doc_type)

        # Get file size
        file_size = os.path.getsize(file_path)

        # Generate document ID
        document_id = str(uuid.uuid4())

        # Chunk the document
        chunks = self._chunk_text(text, document_id, filename)

        # Create metadata
        metadata = DocumentMetadata(
            filename=filename,
            document_type=doc_type,
            file_size=file_size,
            num_chunks=len(chunks),
            document_id=document_id
        )

        return metadata, chunks

    def _extract_text(self, file_path: str, doc_type: DocumentType) -> str:
        """Extract text from different document types"""

        if doc_type == DocumentType.PDF:
            return self._extract_pdf(file_path)
        elif doc_type == DocumentType.DOCX:
            return self._extract_docx(file_path)
        elif doc_type == DocumentType.TXT:
            return self._extract_txt(file_path)
        elif doc_type == DocumentType.CSV:
            return self._extract_csv(file_path)
        elif doc_type == DocumentType.XLSX:
            return self._extract_xlsx(file_path)
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
        return text

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        doc = Document(file_path)
        text = "\n\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text

    def _extract_txt(self, file_path: str) -> str:
        """Extract text from TXT"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()

    def _extract_csv(self, file_path: str) -> str:
        """Extract text from CSV"""
        df = pd.read_csv(file_path)
        # Convert dataframe to readable text format
        text = f"CSV Data with {len(df)} rows and {len(df.columns)} columns\n\n"
        text += f"Columns: {', '.join(df.columns)}\n\n"
        text += df.to_string(index=False)
        return text

    def _extract_xlsx(self, file_path: str) -> str:
        """Extract text from XLSX"""
        xl_file = pd.ExcelFile(file_path)
        text = ""

        for sheet_name in xl_file.sheet_names:
            df = pd.read_excel(xl_file, sheet_name=sheet_name)
            text += f"\n\n--- Sheet: {sheet_name} ---\n\n"
            text += f"Columns: {', '.join(df.columns)}\n\n"
            text += df.to_string(index=False)

        return text

    def _chunk_text(
        self,
        text: str,
        document_id: str,
        filename: str
    ) -> List[DocumentChunk]:
        """Split text into chunks"""

        # Split text using langchain's text splitter
        text_chunks = self.text_splitter.split_text(text)

        # Create DocumentChunk objects
        chunks = []
        for idx, chunk_text in enumerate(text_chunks):
            chunk = DocumentChunk(
                chunk_id=f"{document_id}_chunk_{idx}",
                document_id=document_id,
                content=chunk_text,
                chunk_index=idx,
                metadata={
                    "source_file": filename,
                    "chunk_number": idx,
                    "total_chunks": len(text_chunks)
                }
            )
            chunks.append(chunk)

        return chunks
