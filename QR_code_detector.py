import cv2
from pdf2image import convert_from_path
import numpy as np
from pyzbar.pyzbar import decode
import requests
import fitz  # PyMuPDF
import hashlib
import pytesseract
from PIL import Image
from deploy_config import CertificateBlockchain


class CertificateVerifier:
    def __init__(self):
        # Set Tesseract executable path
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        self.blockchain_obj = CertificateBlockchain()

    def convert_pdf_to_image(self, pdf_path):
        """Converts a PDF page to an image and detects QR code if present."""
        try:
            # Convert the first page of the PDF to an image with high resolution
            pages = convert_from_path(pdf_path, dpi=300, first_page=0, last_page=1)
            image = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)

            pdf_to_image_filename = pdf_path.split(".")[0]
            cv2.imwrite(f"{pdf_to_image_filename}.png", image)

            # Check if the PDF is from IPFS, which doesn't contain QR code
            if "IPFS" in pdf_to_image_filename:
                print("PDF is an IPFS file, skipping QR code extraction.")
                return -1

            # Extract QR code data
            qr_extracted_data = self.find_qr_code_cv2(image)
            return qr_extracted_data

        except Exception as e:
            print(f"Error converting PDF to image: {e}")
            return None

    def ocr_extracted_text(self, image_path):
        """Extracts text from an image using OCR."""
        try:
            img = Image.open(image_path)
            extracted_text = pytesseract.image_to_string(image=img)
            return extracted_text
        except Exception as e:
            print(f"Error during OCR extraction: {e}")
            return ""

    def extract_qr_code_region(self, image, points):
        """Extracts the QR code region from the image."""
        points = points[0].astype(int)
        x, y, w, h = cv2.boundingRect(points)
        qr_region = image[y:y + h, x:x + w]
        return qr_region

    def find_qr_code_cv2(self, image):
        """Detects and decodes QR code from an image."""
        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(image)

        if points is not None:
            qr_region = self.extract_qr_code_region(image, points)
            decoded_objects = decode(qr_region)
            if decoded_objects:
                for obj in decoded_objects:
                    return obj.data.decode('utf-8')
            else:
                print("QR Code detected but could not decode the content.")
        else:
            print("No QR Code found.")
        return None

    def store_certificate_from_ipfs(self, ipfs_link):
        """Downloads a PDF from an IPFS link and saves it locally."""
        try:
            pdf_save_name = "IPFS_certificate.pdf"
            response = requests.get(url=ipfs_link, headers={"Accept": "application/pdf"}, timeout=5)
            if response.status_code == 200:
                with open(pdf_save_name, "wb") as f:
                    f.write(response.content)
                print(f"PDF file saved successfully as {pdf_save_name}")
                return pdf_save_name
            else:
                print(f"Certificate not found on IPFS, Status Code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred while downloading from IPFS: {e}")
        return None

    def extract_text_from_pdf(self, pdf_file):
        """Extracts text from a PDF file."""
        try:
            document = fitz.open(pdf_file)
            page = document[0]
            text = page.get_text()
            return str(text).replace("\n", "").replace(" ", "").replace("\t", "").strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def convert_to_md5_hash(self, text):
        """Converts text to an MD5 hash."""
        return hashlib.md5(text.encode()).hexdigest()

    def verify_certificate(self, user_pdf):
        """Main verification flow for the certificate."""
        try:
            # Step 1: Extract and hash data from user PDF
            user_pdf_data = self.extract_text_from_pdf(user_pdf)
            user_pdf_hash = self.convert_to_md5_hash(user_pdf_data)
            print(f"Extracted user PDF text: {user_pdf_data} - Hash value: {user_pdf_hash}")

            # Step 2: Convert PDF to image and extract QR code link
            qr_code_link = self.convert_pdf_to_image(pdf_path=user_pdf)
            print(f"Decoded Data from QR Code: {qr_code_link}")

            # Step 3: Download and verify IPFS certificate
            ipfs_pdf_filename = self.store_certificate_from_ipfs(ipfs_link=qr_code_link)
            if ipfs_pdf_filename:
                ipfs_pdf_data = self.extract_text_from_pdf(ipfs_pdf_filename)
                ipfs_pdf_hash = self.convert_to_md5_hash(ipfs_pdf_data)
                print(f"Extracted IPFS PDF text: {ipfs_pdf_data} - Hash value: {ipfs_pdf_hash}")

                # Compare the extracted hashes
                if user_pdf_hash == ipfs_pdf_hash:
                    print("(Hash comparison) Certificate is Genuine!")
                else:
                    print("Certificate is Fake!")

                # Step 4: Check hash existence on the blockchain
                self.check_hash_on_blockchain(user_pdf_hash, ipfs_pdf_hash)
            else:
                print("Failed to download IPFS certificate.")

        except Exception as e:
            print(f"An error occurred during verification: {e}")

    def check_hash_on_blockchain(self, user_pdf_hash, user_ocr_hash):
        """Check whether the PDF and OCR hashes exist on the blockchain."""
        pdf_result = self.blockchain_obj.check_pdf_hash_existence(hash_to_check=user_pdf_hash)
        ocr_result = self.blockchain_obj.check_pdf_hash_existence(hash_to_check=user_ocr_hash)

        if pdf_result:
            print("PDF Hash exists in blockchain. Certificate is genuine!")
        else:
            print("PDF Hash does not exist in blockchain!")

        if ocr_result:
            print("OCR Hash exists in blockchain. Certificate is genuine!")
        else:
            print("OCR Hash does not exist in blockchain!")


if __name__ == "__main__":
    verifier = CertificateVerifier()
    verifier.verify_certificate("certificate.pdf")
