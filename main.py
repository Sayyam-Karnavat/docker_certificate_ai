import cv2
from pdf2image import convert_from_bytes
import numpy as np
from pyzbar.pyzbar import decode
import requests
import fitz  # PyMuPDF
import hashlib
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from io import BytesIO
from deploy_config import CertificateBlockchain
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


def extract_text_from_pdf(pdf_stream):
    """Extracts text from a PDF file stream."""
    try:
        # Open the PDF from the BytesIO stream
        document = fitz.open(stream=pdf_stream, filetype="pdf")
        page = document[0]
        text = page.get_text()
        return str(text).replace("\n", "").replace(" ", "").replace("\t", "").strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return None  # Return None to indicate failure


def convert_to_md5_hash(text):
    """Converts text to an MD5 hash."""
    return hashlib.md5(text.encode()).hexdigest()


def verification_engine(pdf_from_frontend):
    """Verification engine to check if the PDF is genuine."""
    global blockchain_obj
    try:
        # Convert the FileStorage object to a BytesIO stream
        pdf_stream = BytesIO(pdf_from_frontend.read())

        # Extract text and convert to MD5 hash
        user_pdf_text = extract_text_from_pdf(pdf_stream=pdf_stream)
        if user_pdf_text is None:
            return {"Result": "INVALID", "IPFS_file_hash": "NULL"}

        user_pdf_hash = convert_to_md5_hash(user_pdf_text)

        # Reset stream position to the beginning before using it again
        pdf_stream.seek(0)

        # Convert the first page of the PDF to an image for QR code detection using convert_from_bytes
        pages = convert_from_bytes(pdf_stream.read(), dpi=300, first_page=0, last_page=1)
        image = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)

        # Detect and decode QR code
        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(image)

        if points is not None:
            points = points[0].astype(int)
            x, y, w, h = cv2.boundingRect(points)
            qr_region = image[y:y + h, x:x + w]
            decoded_objects = decode(qr_region)
            if decoded_objects:
                for obj in decoded_objects:
                    QR_code_link = obj.data.decode('utf-8')
                    # Check if QR code link is empty or not a valid URL
                    if not QR_code_link:
                        logger.error("QR code detected but no valid link found.")
                        return {"Result": "INVALID", "IPFS_file_hash": "NULL"}
                    # Extract the hash from the QR code link
                    IPFS_hash_of_file = str(QR_code_link).split("/")[-1]
            else:
                logger.error("QR Code detected but could not decode the content.")
                return {"Result": "INVALID", "IPFS_file_hash": "NULL"}
        else:
            logger.error("No QR Code found.")
            return {"Result": "INVALID", "IPFS_file_hash": "NULL"}

        # Download the PDF from the IPFS link
        try:
            ipfs_response = requests.get(url=QR_code_link, headers={"Accept": "application/pdf"}, timeout=5)
            ipfs_response.raise_for_status()  # Raise an error for bad responses
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch the certificate from IPFS: {e}")
            return {"Result": "INVALID", "IPFS_file_hash": "NULL"}

        # Process the downloaded IPFS PDF
        ipfs_pdf_data = BytesIO(ipfs_response.content)
        ipfs_pdf_extracted_text = extract_text_from_pdf(ipfs_pdf_data)
        if ipfs_pdf_extracted_text is None:
            return {"Result": "INVALID", "IPFS_file_hash": "NULL"}
        ipfs_pdf_hash = convert_to_md5_hash(ipfs_pdf_extracted_text)

        ##### Compare the extracted hashes and also check if hash exists in blockchain or not  ####
        # blockchain_result = blockchain_obj.check_ocr_hash_existence(hash_to_check=ipfs_pdf_hash)

        if user_pdf_hash == ipfs_pdf_hash:
            return {"Result": "Genuine", "IPFS_file_hash": str(IPFS_hash_of_file)}
        else:
            return {"Result": "Fake", "IPFS_file_hash": "NULL"}
    except Exception as e:
        logger.error(f"An error occurred in verification engine: {e}")
        return {"Result": "INVALID", "IPFS_file_hash": "NULL"}


@app.route("/verify_pdf", methods=["POST"])
def verify_certificate():
    """Endpoint to verify the uploaded PDF."""
    try:
        # Access the uploaded file from the form
        pdf_file = request.files.get('pdf_file')
        if not pdf_file:
            return jsonify({"Result": "INVALID", "IPFS_file_hash": "NULL"}), 400
        # Run verification
        result = verification_engine(pdf_from_frontend=pdf_file)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({"Result": "INVALID", "IPFS_file_hash": "NULL"}), 400


@app.route("/writeToBlockchain", methods = ['POST'])
def write_data_to_blockchain():
    global blockchain_obj
    try:
        pdf_file = request.files.get("pdf_file")
        if not pdf_file:
            return jsonify({"ERR": "INVALID"}), 400
        pdf_stream = BytesIO(pdf_file.read())
        extracted_text = extract_text_from_pdf(pdf_stream=pdf_stream)
        hash_data = convert_to_md5_hash(extracted_text)
        transaction_id = blockchain_obj.write_to_blockchain(ocr_hash=hash_data)

        if transaction_id == 0 : # That means error has occurred (possibly timeout error)
            return jsonify({"ERR": "Timeout error!!!"}), 400
        
        return jsonify({"Success" : str(transaction_id)}), 200
    except Exception as e:
        logger.error(f"Error Writing data to Blockchain: {e}")
        return jsonify({"ERR": str(e)}), 400


@app.route("/user_form", methods=['GET'])
def user_form():
    """Renders the form to upload a PDF file."""
    return render_template('form.html')


@app.route("/", methods=['GET'])
def index_server():
    return "Server is Running !!!"


if __name__ == "__main__":
    blockchain_obj = CertificateBlockchain()
    app.run(host="0.0.0.0", port=4444)
