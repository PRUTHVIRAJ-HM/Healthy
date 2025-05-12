import re
import logging
from models import FoodSafetyKnowledge

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_prescription(prescription_text):
    """
    Analyzes a prescription text to identify medications and medical conditions
    Returns a dictionary of restrictions
    """
    try:
        # Convert text to lowercase for easier matching
        text = prescription_text.lower()
        
        # Extract information
        medications = extract_medications(text)
        conditions = extract_conditions(text)
        allergies = extract_allergies(text)
        
        # Get food restrictions for each medication
        medication_restrictions = []
        for med in medications:
            risky_foods = FoodSafetyKnowledge.get_risky_foods_for_medication(med)
            if risky_foods:
                medication_restrictions.extend(risky_foods)
        
        # Get food restrictions for each condition
        condition_restrictions = []
        for condition in conditions:
            foods_to_avoid = FoodSafetyKnowledge.get_foods_to_avoid_for_condition(condition)
            if foods_to_avoid:
                condition_restrictions.extend(foods_to_avoid)
        
        # Combine all restrictions
        all_restrictions = list(set(medication_restrictions + condition_restrictions + allergies))
        
        return {
            "medications": medications,
            "conditions": conditions,
            "allergies": allergies,
            "restrictions": all_restrictions
        }
    
    except Exception as e:
        logger.error(f"Error analyzing prescription: {str(e)}")
        return {
            "medications": [],
            "conditions": [],
            "allergies": [],
            "restrictions": []
        }

def extract_medications(text):
    """
    Extract medication names from prescription text
    """
    medications = []
    
    # Common medications (simplified list)
    common_meds = [
        "warfarin", "coumadin", "atorvastatin", "lipitor", "simvastatin", "zocor", 
        "lisinopril", "prinivil", "zestril", "metformin", "glucophage", "amlodipine", 
        "norvasc", "metoprolol", "lopressor", "toprol", "losartan", "cozaar", 
        "albuterol", "proventil", "ventolin", "omeprazole", "prilosec", "gabapentin", 
        "neurontin", "hydrochlorothiazide", "levothyroxine", "synthroid", "amoxicillin",
        "penicillin", "aspirin", "ibuprofen", "acetaminophen", "tylenol", "advil",
        "insulin", "prednisone", "fluoxetine", "prozac", "sertraline", "zoloft",
        "furosemide", "lasix", "citalopram", "celexa", "montelukast", "singulair"
    ]
    
    # Check for common medications in the text
    for med in common_meds:
        if med in text:
            medications.append(med)
    
    # Look for patterns like "prescribed medication_name"
    prescribed_pattern = r"prescri\w+\s+(\w+)"
    prescribed_matches = re.findall(prescribed_pattern, text)
    medications.extend(prescribed_matches)
    
    # Look for patterns like "take medication_name"
    take_pattern = r"take\s+(\w+)"
    take_matches = re.findall(take_pattern, text)
    medications.extend(take_matches)
    
    # Look for mg dosages which often accompany medication names
    dosage_pattern = r"(\w+)\s+\d+\s*mg"
    dosage_matches = re.findall(dosage_pattern, text)
    medications.extend(dosage_matches)
    
    # Remove duplicates and common words that aren't medications
    non_meds = ["the", "and", "with", "this", "your", "you", "for", "daily", "once", "twice", "day", "morning", "night"]
    filtered_meds = [med for med in medications if med.lower() not in non_meds and len(med) > 2]
    
    return list(set(filtered_meds))  # Remove duplicates

def extract_conditions(text):
    """
    Extract medical conditions from prescription text
    """
    conditions = []
    
    # Common medical conditions
    common_conditions = [
        "diabetes", "hypertension", "high blood pressure", "high cholesterol", 
        "heart disease", "asthma", "copd", "arthritis", "depression", "anxiety", 
        "thyroid", "hypothyroidism", "hyperthyroidism", "gerd", "acid reflux",
        "migraine", "allergies", "gout", "kidney disease", "liver disease",
        "osteoporosis", "cancer", "epilepsy", "seizures", "parkinsons", 
        "alzheimers", "celiac", "gluten", "lactose intolerance", "ibs",
        "crohns", "colitis", "fibromyalgia", "lupus", "psoriasis", "eczema"
    ]
    
    # Check for common conditions in the text
    for condition in common_conditions:
        if condition in text:
            conditions.append(condition)
    
    # Look for patterns like "diagnosed with condition"
    diagnosed_pattern = r"diagnos\w+\s+with\s+(\w+(\s+\w+)?)"
    diagnosed_matches = re.findall(diagnosed_pattern, text)
    if diagnosed_matches:
        conditions.extend([match[0] for match in diagnosed_matches])
    
    # Look for patterns like "treat condition"
    treat_pattern = r"treat\w+\s+(\w+(\s+\w+)?)"
    treat_matches = re.findall(treat_pattern, text)
    if treat_matches:
        conditions.extend([match[0] for match in treat_matches])
    
    return list(set(conditions))  # Remove duplicates

def extract_allergies(text):
    """
    Extract food allergies from prescription text
    """
    allergies = []
    
    # Common food allergies
    common_allergies = FoodSafetyKnowledge.ALLERGIES
    
    # Check for common allergies in the text
    for allergy in common_allergies:
        allergy_pattern = rf"allerg\w+\s+to\s+{allergy}"
        if re.search(allergy_pattern, text) or f"allergic to {allergy}" in text:
            allergies.append(allergy)
    
    # Look for patterns like "allergic to food"
    allergic_pattern = r"allerg\w+\s+to\s+(\w+(\s+\w+)?)"
    allergic_matches = re.findall(allergic_pattern, text)
    if allergic_matches:
        allergies.extend([match[0] for match in allergic_matches])
    
    return list(set(allergies))  # Remove duplicates

def check_food_safety(food_name, food_info, restrictions):
    """
    Check if a food is safe based on the user's restrictions
    Returns a dictionary with safety information
    """
    try:
        is_safe = True
        unsafe_ingredients = []
        explanation = []
        
        # Get ingredients from food info
        ingredients = food_info.get("ingredients", [])
        food_description = food_info.get("description", "")
        
        # If no ingredients found, try to extract from description
        if not ingredients and food_description:
            from web_scraper import extract_ingredients_from_text
            potential_ingredients = extract_ingredients_from_text(food_description)
            ingredients.extend(potential_ingredients)
        
        # Check if the food name itself is in restrictions
        if food_name.lower() in [r.lower() for r in restrictions.get("restrictions", [])]:
            is_safe = False
            unsafe_ingredients.append(food_name)
            explanation.append(f"{food_name} is directly listed in your restrictions.")
        
        # Check each ingredient against restrictions
        for ingredient in ingredients:
            for restriction in restrictions.get("restrictions", []):
                if restriction.lower() in ingredient.lower() or ingredient.lower() in restriction.lower():
                    is_safe = False
                    unsafe_ingredients.append(ingredient)
                    explanation.append(f"{ingredient} may interact with your health condition or medication.")
        
        # Check if any medications have specific interactions with this food
        for medication in restrictions.get("medications", []):
            risky_foods = FoodSafetyKnowledge.get_risky_foods_for_medication(medication)
            for risky_food in risky_foods:
                if risky_food.lower() in food_name.lower() or any(risky_food.lower() in ingredient.lower() for ingredient in ingredients):
                    is_safe = False
                    unsafe_ingredients.append(risky_food)
                    explanation.append(f"{risky_food} may interact with your medication {medication}.")
        
        # Check for allergies
        for allergy in restrictions.get("allergies", []):
            if allergy.lower() in food_name.lower() or any(allergy.lower() in ingredient.lower() for ingredient in ingredients):
                is_safe = False
                unsafe_ingredients.append(allergy)
                explanation.append(f"{allergy} is listed in your allergies.")
        
        # Prepare the recommendation
        recommendation = "This food appears to be safe for you to consume." if is_safe else "This food may not be safe for you based on your prescription."
        
        # Remove duplicate explanations and ingredients
        unique_explanations = list(set(explanation))
        unique_ingredients = list(set(unsafe_ingredients))
        
        # Get food benefits and health risks based on safety status
        benefits = food_info.get("benefits", [])
        health_risks = food_info.get("health_risks", [])
        
        return {
            "is_safe": is_safe,
            "unsafe_ingredients": unique_ingredients,
            "recommendation": recommendation,
            "explanation": unique_explanations,
            "benefits": benefits,
            "health_risks": health_risks,
            "food_info": food_info
        }
    
    except Exception as e:
        logger.error(f"Error checking food safety: {str(e)}")
        return {
            "is_safe": False,
            "unsafe_ingredients": [],
            "recommendation": "Could not determine if this food is safe. Please consult with your doctor or pharmacist.",
            "explanation": ["An error occurred during analysis. Please try again or consult a healthcare professional."],
            "benefits": food_info.get("benefits", []),
            "health_risks": food_info.get("health_risks", []),
            "food_info": food_info
        }
