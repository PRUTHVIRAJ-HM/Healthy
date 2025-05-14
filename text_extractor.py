import os
import logging
import tempfile
from PIL import Image
import PyPDF2
import io
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load TrOCR model and processor globally for reuse
try:
    logger.debug("Loading TrOCR model...")
    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
    model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
    TROCR_AVAILABLE = True
    logger.debug("TrOCR model loaded successfully")
except Exception as e:
    logger.error(f"Error loading TrOCR model: {str(e)}")
    TROCR_AVAILABLE = False

def extract_text_from_image(image_path):
    """
    Extract text from an image file using TrOCR
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Extracted text from the image
    """
    try:
        if not TROCR_AVAILABLE:
            logger.error("TrOCR model not available")
            return ""
            
        # Open the image
        image = Image.open(image_path).convert("RGB")
        
        # Process image with TrOCR
        pixel_values = processor(images=image, return_tensors="pt").pixel_values
        
        # Generate text
        generated_ids = model.generate(pixel_values)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        logger.debug(f"Extracted text from image using TrOCR: {text[:100]}...")
        return text
    
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        return ""

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using PyPDF2
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        # Open the PDF file
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from each page
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        
        # If extracted text is very short or empty, it might be a scanned PDF
        if len(text.strip()) < 50:
            logger.debug("Limited text extracted directly. PDF may be scanned. Attempting OCR...")
            return extract_text_from_pdf_using_ocr(pdf_path)
            
        logger.debug(f"Extracted text from PDF: {text[:100]}...")
        return text
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        
        # Try OCR as fallback for scanned PDFs
        try:
            logger.debug("Attempting OCR fallback for PDF...")
            return extract_text_from_pdf_using_ocr(pdf_path)
        except Exception as ocr_error:
            logger.error(f"OCR fallback failed: {str(ocr_error)}")
            return ""

def extract_text_from_pdf_using_ocr(pdf_path):
    """
    Extract text from a PDF using OCR (for scanned PDFs)
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF using OCR
    """
    try:
        from pdf2image import convert_from_path
        
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        
        # Extract text from each image
        text = ""
        for i, image in enumerate(images):
            # Create a temporary file to save the image
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_filename = temp_file.name
                
            # Save the image
            image.save(temp_filename, 'JPEG')
            
            # Extract text from the image
            logger.debug(f"Processing page {i+1} with TrOCR")
            page_text = extract_text_from_image(temp_filename)
            text += page_text + "\n\n"
            
            # Remove the temporary file
            os.unlink(temp_filename)
        
        return text
    
    except Exception as e:
        logger.error(f"Error using OCR on PDF: {str(e)}")
        return ""