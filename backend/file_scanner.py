import magic
import re
from pathlib import Path
from PyPDF2 import PdfReader
import io

class FileScanner:
    def __init__(self):
        self.suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'vbscript:',
            r'eval\s*\(',
            r'document\.write',
            r'window\.location',
            r'exec\s*\(',
            r'shell\s*\(',
            r'cmd\s*\(',
            r'powershell',
            r'wget\s+',
            r'curl\s+',
            r'base64',
            r'\\x[0-9a-fA-F]{2}',
        ]
        
        self.macro_patterns = [
            r'AutoOpen',
            r'AutoClose',
            r'Document_Open',
            r'Macro',
            r'VBA',
            r'CreateObject',
            r'Shell',
            r'WScript',
        ]
    
    def scan_file(self, file_path: Path, original_filename: str):
        """Scan file for malicious content"""
        results = {
            "is_safe": True,
            "threats": [],
            "file_type": "unknown",
            "details": {}
        }
        
        try:
            # 1. Validate file type using magic bytes
            file_type = self._validate_file_type(file_path, original_filename)
            results["file_type"] = file_type
            
            if file_type == "invalid":
                results["is_safe"] = False
                results["threats"].append("File type mismatch - possible extension spoofing")
                return results
            
            # 2. Scan based on file type
            extension = file_path.suffix.lower()
            
            if extension == ".pdf":
                self._scan_pdf(file_path, results)
            elif extension in [".doc", ".docx"]:
                self._scan_office(file_path, results)
            
            # 3. Generic content scan
            self._scan_content(file_path, results)
            
        except Exception as e:
            results["is_safe"] = False
            results["threats"].append(f"Scan error: {str(e)}")
        
        return results
    
    def _validate_file_type(self, file_path: Path, original_filename: str):
        """Validate file type using magic bytes"""
        try:
            mime = magic.from_file(str(file_path), mime=True)
            extension = Path(original_filename).suffix.lower()
            
            # Check if MIME type matches extension
            if extension == ".pdf" and mime != "application/pdf":
                return "invalid"
            elif extension in [".doc", ".docx"] and mime not in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                return "invalid"
            
            return mime
        except:
            return "unknown"
    
    def _scan_pdf(self, file_path: Path, results):
        """Scan PDF for malicious content"""
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                
                # Check for JavaScript
                if reader.get_js():
                    results["is_safe"] = False
                    results["threats"].append("PDF contains JavaScript")
                    results["details"]["javascript"] = True
                
                # Check for embedded files
                if "/EmbeddedFiles" in str(reader.pages[0]) if reader.pages else False:
                    results["threats"].append("PDF contains embedded files")
                    results["details"]["embedded_files"] = True
                
        except Exception as e:
            results["threats"].append(f"PDF scan error: {str(e)}")
    
    def _scan_office(self, file_path: Path, results):
        """Scan Office documents for macros"""
        try:
            content = file_path.read_bytes()
            content_str = content.decode('utf-8', errors='ignore')
            
            # Check for macro patterns
            for pattern in self.macro_patterns:
                if re.search(pattern, content_str, re.IGNORECASE):
                    results["is_safe"] = False
                    results["threats"].append(f"Suspicious macro pattern: {pattern}")
                    results["details"]["macros"] = True
                    break
                    
        except Exception as e:
            results["threats"].append(f"Office scan error: {str(e)}")
    
    def _scan_content(self, file_path: Path, results):
        """Generic content scan for suspicious patterns"""
        try:
            content = file_path.read_bytes()
            content_str = content.decode('utf-8', errors='ignore')
            
            for pattern in self.suspicious_patterns:
                if re.search(pattern, content_str, re.IGNORECASE):
                    results["is_safe"] = False
                    results["threats"].append(f"Suspicious pattern detected: {pattern}")
                    results["details"]["suspicious_content"] = True
                    break
                    
        except Exception as e:
            results["threats"].append(f"Content scan error: {str(e)}")