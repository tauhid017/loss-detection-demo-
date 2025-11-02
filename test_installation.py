print("Testing installation...")

try:
    import torch
    import torchvision
    from transformers import BlipProcessor, BlipForConditionalGeneration
    import streamlit as st
    from PIL import Image
    import numpy as np
    
    print("✅ All imports successful!")
    print(f"✅ PyTorch version: {torch.__version__}")
    print("✅ Installation completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")