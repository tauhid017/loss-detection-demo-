import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import os

class ImageCaptioner:
    def __init__(self):
        print("Loading BLIP model...")
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        print("✅ BLIP model loaded successfully!")
    
    def generate_caption(self, image_path):
        """
        Generate caption for uploaded image
        """
        try:
            # Open and validate image
            if not os.path.exists(image_path):
                return "Error: Image file not found"
            
            image = Image.open(image_path).convert('RGB')
            
            # Process image
            inputs = self.processor(image, return_tensors="pt")
            
            # Generate caption
            with torch.no_grad():
                out = self.model.generate(
                    **inputs, 
                    max_length=50, 
                    num_beams=5,
                    early_stopping=True
                )
            
            caption = self.processor.decode(out[0], skip_special_tokens=True)
            return caption
            
        except Exception as e:
            return f"Error in caption generation: {str(e)}"