from algopy import ARC4Contract, String , subroutine
from algopy.arc4 import abimethod




class HelloWorld(ARC4Contract):
    @abimethod()
    def hello(self, name: String) -> String:
        return "Hello, " + name
    
    @abimethod()
    def write_certificate_data(self , pdf_extracted_text_hash : String , OCR_extracted_text_hash : String)-> None:
        self.clear_storage()
        self.pdf_data_hash = pdf_extracted_text_hash
        self.ocr_data_hash = OCR_extracted_text_hash

    @subroutine
    def clear_storage(self)-> None:
        self.pdf_data_hash = String("")
        self.ocr_data_hash = String("")

