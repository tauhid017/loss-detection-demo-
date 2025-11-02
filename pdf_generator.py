class DescriptionGenerator:
    def __init__(self):
        print("✅ Description generator initialized!")

    def enhance_description(self, image_caption, damage_type):
        try:
            severity = self.assess_severity(image_caption)
            description = self.create_professional_description(image_caption, damage_type, severity)
            return description
        except Exception as e:
            print(f"[Error in enhance_description]: {e}")
            return f"Professional assessment confirms {damage_type}. {image_caption} Recommended: Detailed inspection by certified appraiser."

    def assess_severity(self, caption):
        caption_lower = caption.lower()
        severe_keywords = ['severe', 'major', 'extensive', 'destroyed', 'broken', 'smashed', 'wrecked', 'totaled']
        moderate_keywords = ['moderate', 'multiple', 'several', 'significant', 'damaged', 'dents', 'cracks']
        minor_keywords = ['minor', 'small', 'slight', 'light', 'few', 'scratch', 'scratches']

        if any(keyword in caption_lower for keyword in severe_keywords):
            return "severe"
        elif any(keyword in caption_lower for keyword in moderate_keywords):
            return "moderate"
        elif any(keyword in caption_lower for keyword in minor_keywords):
            return "minor"
        else:
            return "moderate"

    def create_professional_description(self, caption, damage_type, severity):
        severity_phrases = {
            "severe": "**SEVERE DAMAGE ASSESSMENT**: The inspection indicates extensive and critical damage affecting multiple structural or functional areas of the property. Immediate mitigation and safety measures are required.",
            "moderate": "**MODERATE DAMAGE ASSESSMENT**: The inspection reveals notable damage that, while not catastrophic, demands professional repair and restoration. The extent of impairment may affect operational or residential usability until repairs are completed.",
            "minor": "**MINOR DAMAGE ASSESSMENT**: The inspection identifies superficial or localized damage with limited functional impact. Repairs can be addressed through routine maintenance and corrective procedures."
        }

        damage_specific = {
            "fire damage": f"Fire and smoke exposure have resulted in surface deterioration, soot accumulation, and thermal distress to key components. {caption}",
            "water damage": f"Prolonged moisture exposure has caused visible staining, swelling, or structural weakening in affected areas. {caption}",
            "hail damage": f"Impact marks and granule displacement from hail are visible across exposed surfaces. {caption}",
            "flood damage": f"Water intrusion has affected ground-level materials and electrical systems, requiring professional dehumidification and restoration. {caption}",
            "collision damage": f"Impact deformation and surface fracturing indicate substantial mechanical stress to the affected structure. {caption}",
            "vandalism": f"Intentional surface defacement and structural tampering are evident. {caption}",
            "storm damage": f"Wind, debris, and precipitation exposure have compromised external integrity and finish. {caption}",
            "theft": f"Signs of forced entry and material removal are observed, suggesting deliberate tampering. {caption}"
        }

        base_description = damage_specific.get(
            damage_type.lower(),
            f"Observed damage corresponds with {damage_type.lower()} conditions. {caption}"
        )

        recommendations = {
            "severe": "**RECOMMENDATION**: Immediate intervention by certified restoration professionals is required. Full structural safety evaluation and phased reconstruction are strongly advised.",
            "moderate": "**RECOMMENDATION**: Professional repair assessment, material replacement, and post-restoration verification are recommended to restore functional and visual integrity.",
            "minor": "**RECOMMENDATION**: Routine maintenance and targeted repair should be scheduled to prevent progressive deterioration."
        }

        recommendation = recommendations.get(
            severity,
            "**RECOMMENDATION**: Further professional evaluation is advised to determine corrective actions."
        )

        full_text = f"{severity_phrases[severity]} {base_description} {recommendation}"
        full_text = full_text.encode("ascii", "ignore").decode()
        return full_text
