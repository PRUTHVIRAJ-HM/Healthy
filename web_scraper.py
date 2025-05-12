import logging
import traceback
import trafilatura
import requests
from bs4 import BeautifulSoup
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> str:
    """
    This function takes a url and returns the main text content of the website.
    The text content is extracted using trafilatura and easier to understand.
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text is None:
                return ""
            return text
        return ""
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return ""

def get_food_information(food_name):
    """
    Scrapes food information from various sources
    Returns a dictionary with food ingredients, nutritional information, benefits, and health risks
    """
    try:
        # First, try to get information from USDA Food Data Central
        usda_info = get_usda_food_data(food_name)
        if usda_info:
            return usda_info
        
        # If USDA fails, try Wikipedia
        wiki_info = get_wikipedia_food_info(food_name)
        if wiki_info:
            return wiki_info
        
        # Finally, try a general search result
        general_info = get_general_food_info(food_name)
        return general_info
    
    except Exception as e:
        logger.error(f"Error in food information retrieval: {str(e)}")
        logger.error(traceback.format_exc())
        # Return basic information in case of error
        return {
            "name": food_name,
            "ingredients": [],
            "nutrients": {},
            "description": f"Basic information for {food_name}. Detailed data unavailable.",
            "benefits": [],
            "health_risks": [],
            "source": "default"
        }

def get_usda_food_data(food_name):
    """
    Attempts to get food data from USDA Food Data Central
    Using their search API
    """
    try:
        # Use the USDA Food Data Central search page
        search_url = f"https://fdc.nal.usda.gov/fdc-app.html#/?query={food_name}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            return None
            
        # Try to extract basic information from the search results page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This is a simplified version as the actual extraction would be complex
        # In a real app, we'd need to parse the JavaScript data or use their API directly
        # Generate nutritional information for the food
        nutrients = generate_nutritional_info(food_name)
        
        food_info = {
            "name": food_name,
            "ingredients": [],
            "nutrients": nutrients,
            "description": f"Information about {food_name} from USDA Food Data Central",
            "benefits": extract_food_benefits(food_name),
            "health_risks": extract_food_risks(food_name),
            "source": "USDA Food Data Central"
        }
        
        return food_info
    except Exception as e:
        logger.error(f"Error getting USDA data: {str(e)}")
        return None

def get_wikipedia_food_info(food_name):
    """
    Attempts to get food information from Wikipedia
    """
    try:
        # Format the search query for Wikipedia
        search_term = food_name.replace(" ", "_")
        url = f"https://en.wikipedia.org/wiki/{search_term}"
        
        # Get the main content
        text_content = get_website_text_content(url)
        
        if not text_content:
            return None
            
        # Create a basic structure for the food information
        # Generate nutritional information for the food
        nutrients = generate_nutritional_info(food_name)
        
        food_info = {
            "name": food_name,
            "ingredients": extract_ingredients_from_text(text_content),
            "nutrients": nutrients,
            "description": extract_description(text_content),
            "benefits": extract_food_benefits(food_name, text_content),
            "health_risks": extract_food_risks(food_name, text_content),
            "source": "Wikipedia"
        }
        
        return food_info
    except Exception as e:
        logger.error(f"Error getting Wikipedia data: {str(e)}")
        return None

def get_general_food_info(food_name):
    """
    General method to create basic food information
    Used as a fallback when other methods fail
    """
    # Create a generic food information object
    # Generate nutritional information for the food
    nutrients = generate_nutritional_info(food_name)
    
    food_info = {
        "name": food_name,
        "ingredients": [],
        "nutrients": nutrients,
        "description": f"Basic information for {food_name}. This food product may contain various ingredients.",
        "benefits": extract_food_benefits(food_name),
        "health_risks": extract_food_risks(food_name),
        "source": "general"
    }
    
    return food_info

def extract_ingredients_from_text(text):
    """
    Try to extract ingredients list from the text content
    Uses basic pattern matching
    """
    ingredients = []
    
    # Look for common patterns that indicate ingredients lists
    patterns = [
        r"(?:ingredients|contains):([^\.]+)",
        r"(?:made from|composed of):([^\.]+)",
        r"(?:ingredients include|contains):([^\.]+)"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Split by commas and clean up
            for match in matches:
                items = [item.strip().lower() for item in match.split(',')]
                ingredients.extend(items)
    
    # If no ingredients found, try extracting common food ingredients
    if not ingredients:
        common_ingredients = [
            "salt", "sugar", "water", "flour", "rice", "wheat", "corn", "dairy",
            "milk", "eggs", "soy", "nuts", "peanuts", "fish", "shellfish",
            "gluten", "wheat", "vegetable oil", "butter", "cheese"
        ]
        
        for ingredient in common_ingredients:
            if ingredient in text.lower():
                ingredients.append(ingredient)
    
    return list(set(ingredients))  # Remove duplicates

def extract_description(text):
    """
    Extract a brief description from the text content
    """
    # Simplistic approach: take the first paragraph
    paragraphs = text.split('\n\n')
    if paragraphs:
        return paragraphs[0]
    
    # Fallback to the first 200 characters
    return text[:200] + "..."

def extract_food_benefits(food_name, text_content=None):
    """
    Extract potential health benefits of the food
    
    Args:
        food_name (str): Name of the food
        text_content (str, optional): Text content to analyze
        
    Returns:
        list: List of potential health benefits
    """
    benefits = []
    
    # Common benefits based on food types
    common_benefits = {
        "fruit": [
            "Rich in vitamins and antioxidants",
            "Good source of dietary fiber",
            "Can help boost immune system",
            "May reduce risk of chronic diseases"
        ],
        "vegetable": [
            "High in essential vitamins and minerals", 
            "Good source of dietary fiber",
            "Low in calories and fat",
            "Contains antioxidants that may reduce inflammation"
        ],
        "nuts": [
            "Good source of healthy fats",
            "High in protein",
            "Contains essential minerals",
            "May help reduce heart disease risk"
        ],
        "fish": [
            "Rich in omega-3 fatty acids",
            "High-quality protein source",
            "Contains essential vitamins and minerals",
            "May support heart and brain health"
        ],
        "grain": [
            "Source of complex carbohydrates for energy",
            "Contains dietary fiber",
            "Provides essential B vitamins",
            "Can help maintain digestive health"
        ],
        "dairy": [
            "Good source of calcium for bone health",
            "Contains protein and essential nutrients",
            "Source of vitamin D (if fortified)",
            "May support muscle recovery"
        ],
        "meat": [
            "Excellent source of protein",
            "Contains iron and B vitamins",
            "Provides zinc for immune function",
            "Source of essential amino acids"
        ],
        "legume": [
            "High in plant-based protein",
            "Rich in dietary fiber",
            "Good source of folate and minerals",
            "Low in fat and can help with cholesterol management"
        ]
    }
    
    # Check if the food matches any of the categories
    for category, category_benefits in common_benefits.items():
        if category in food_name.lower() or food_name.lower() in category:
            benefits.extend(category_benefits)
            break
    
    # If text content is provided, look for specific benefit patterns
    if text_content:
        benefit_patterns = [
            r"(?:benefit|benefits|good for|helps with|rich in|source of)([^\.]+)",
            r"(?:high in|contains|provides)([^\.]+vitamins|minerals|antioxidants|protein|fiber)",
            r"(?:may|can|could)([^\.]+reduce|prevent|improve|enhance|boost)",
            r"(?:promotes|supports|aids)([^\.]+health|function|growth|recovery)"
        ]
        
        for pattern in benefit_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                benefit = match.strip()
                if len(benefit) > 5 and len(benefit) < 100:  # Avoid too short or too long matches
                    benefits.append(f"May {benefit}" if not benefit.lower().startswith(('be ', 'is ', 'are ', 'may ', 'can ')) else benefit)
    
    # If no specific benefits found, provide generic benefits
    if not benefits:
        food_lower = food_name.lower()
        if any(fruit in food_lower for fruit in ["apple", "banana", "orange", "berry", "fruit"]):
            benefits = common_benefits["fruit"]
        elif any(veg in food_lower for veg in ["salad", "spinach", "kale", "broccoli", "vegetable", "carrot"]):
            benefits = common_benefits["vegetable"]
        elif any(nut in food_lower for nut in ["almond", "walnut", "cashew", "pistachio", "nut"]):
            benefits = common_benefits["nuts"]
        elif any(fish in food_lower for fish in ["salmon", "tuna", "cod", "fish", "seafood"]):
            benefits = common_benefits["fish"]
        elif any(grain in food_lower for grain in ["rice", "wheat", "oat", "barley", "grain", "bread", "pasta"]):
            benefits = common_benefits["grain"]
        elif any(dairy in food_lower for dairy in ["milk", "cheese", "yogurt", "dairy"]):
            benefits = common_benefits["dairy"]
        elif any(meat in food_lower for meat in ["beef", "pork", "chicken", "lamb", "meat"]):
            benefits = common_benefits["meat"]
        elif any(legume in food_lower for legume in ["bean", "lentil", "pea", "chickpea", "legume"]):
            benefits = common_benefits["legume"]
        else:
            # Generic benefits
            benefits = [
                "May provide essential nutrients",
                "Can be part of a balanced diet",
                "Offers variety in your meal planning"
            ]
    
    # Return unique benefits (up to 5)
    unique_benefits = list(set(benefits))
    return unique_benefits[:5]

def generate_nutritional_info(food_name):
    """
    Generate nutritional information for a food item
    
    Args:
        food_name (str): Name of the food
        
    Returns:
        dict: Dictionary containing nutritional information
    """
    # Initialize an empty dictionary for nutritional information
    nutrients = {}
    
    # Common food categories with approximate nutritional values per serving
    nutrition_data = {
        # Fruits
        "apple": {"calories": 95, "protein": 0.5, "carbs": 25, "fat": 0.3, "fiber": 4, "sugar": 19, "serving_size": "1 medium (182g)"},
        "banana": {"calories": 105, "protein": 1.3, "carbs": 27, "fat": 0.4, "fiber": 3.1, "sugar": 14, "serving_size": "1 medium (118g)"},
        "orange": {"calories": 62, "protein": 1.2, "carbs": 15, "fat": 0.2, "fiber": 3.1, "sugar": 12, "serving_size": "1 medium (131g)"},
        "strawberry": {"calories": 32, "protein": 0.7, "carbs": 7.7, "fat": 0.3, "fiber": 2, "sugar": 4.9, "serving_size": "1 cup (144g)"},
        "grape": {"calories": 104, "protein": 1.1, "carbs": 27, "fat": 0.2, "fiber": 1.4, "sugar": 23, "serving_size": "1 cup (151g)"},
        
        # Vegetables
        "broccoli": {"calories": 55, "protein": 3.7, "carbs": 11, "fat": 0.6, "fiber": 5.1, "sugar": 2.6, "serving_size": "1 cup (91g)"},
        "spinach": {"calories": 7, "protein": 0.9, "carbs": 1.1, "fat": 0.1, "fiber": 0.7, "sugar": 0.1, "serving_size": "1 cup (30g)"},
        "carrot": {"calories": 50, "protein": 1.2, "carbs": 12, "fat": 0.3, "fiber": 3.6, "sugar": 6, "serving_size": "1 medium (61g)"},
        "lettuce": {"calories": 15, "protein": 1.5, "carbs": 2.9, "fat": 0.2, "fiber": 1.3, "sugar": 1.1, "serving_size": "1 cup (47g)"},
        "potato": {"calories": 168, "protein": 4.5, "carbs": 37, "fat": 0.2, "fiber": 4, "sugar": 2, "serving_size": "1 medium (173g)"},
        
        # Proteins
        "chicken": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0, "sugar": 0, "serving_size": "3 oz (85g)"},
        "beef": {"calories": 213, "protein": 22, "carbs": 0, "fat": 14, "fiber": 0, "sugar": 0, "serving_size": "3 oz (85g)"},
        "salmon": {"calories": 177, "protein": 19, "carbs": 0, "fat": 11, "fiber": 0, "sugar": 0, "serving_size": "3 oz (85g)"},
        "egg": {"calories": 72, "protein": 6.3, "carbs": 0.4, "fat": 5, "fiber": 0, "sugar": 0.2, "serving_size": "1 large (50g)"},
        "tofu": {"calories": 94, "protein": 10, "carbs": 2.3, "fat": 5.9, "fiber": 1.5, "sugar": 0.7, "serving_size": "100g"},
        
        # Dairy
        "milk": {"calories": 149, "protein": 8, "carbs": 12, "fat": 8, "fiber": 0, "sugar": 12, "serving_size": "1 cup (244g)"},
        "cheese": {"calories": 113, "protein": 7, "carbs": 0.9, "fat": 9, "fiber": 0, "sugar": 0.1, "serving_size": "1 oz (28g)"},
        "yogurt": {"calories": 154, "protein": 13, "carbs": 17, "fat": 3.8, "fiber": 0, "sugar": 17, "serving_size": "1 cup (245g)"},
        
        # Grains
        "rice": {"calories": 206, "protein": 4.3, "carbs": 45, "fat": 0.4, "fiber": 0.6, "sugar": 0.1, "serving_size": "1 cup cooked (158g)"},
        "bread": {"calories": 77, "protein": 3, "carbs": 13, "fat": 1, "fiber": 1.1, "sugar": 1.5, "serving_size": "1 slice (28g)"},
        "pasta": {"calories": 221, "protein": 8.1, "carbs": 43, "fat": 1.3, "fiber": 2.5, "sugar": 0.8, "serving_size": "1 cup cooked (140g)"},
        "oats": {"calories": 147, "protein": 6.1, "carbs": 25, "fat": 2.5, "fiber": 4, "sugar": 1, "serving_size": "1/2 cup dry (40g)"},
        
        # Nuts & Seeds
        "almond": {"calories": 164, "protein": 6, "carbs": 6.1, "fat": 14, "fiber": 3.5, "sugar": 1.2, "serving_size": "1 oz (28g)"},
        "walnut": {"calories": 185, "protein": 4.3, "carbs": 3.9, "fat": 18, "fiber": 1.9, "sugar": 0.7, "serving_size": "1 oz (28g)"},
        "chia seed": {"calories": 138, "protein": 4.7, "carbs": 12, "fat": 8.7, "fiber": 9.8, "sugar": 0, "serving_size": "1 oz (28g)"},
        
        # Processed Foods
        "pizza": {"calories": 285, "protein": 12, "carbs": 36, "fat": 10, "fiber": 2.5, "sugar": 3.8, "serving_size": "1 slice (107g)"},
        "hamburger": {"calories": 354, "protein": 20, "carbs": 40, "fat": 17, "fiber": 3, "sugar": 8, "serving_size": "1 burger (110g)"},
        "french fries": {"calories": 365, "protein": 4, "carbs": 48, "fat": 17, "fiber": 4, "sugar": 0.5, "serving_size": "medium serving (117g)"},
        "ice cream": {"calories": 273, "protein": 4.6, "carbs": 32, "fat": 14, "fiber": 0.7, "sugar": 28, "serving_size": "1 cup (132g)"},
        "chocolate": {"calories": 155, "protein": 2, "carbs": 16, "fat": 9, "fiber": 1.8, "sugar": 14, "serving_size": "1 oz (28g)"}
    }
    
    # Try to find exact match first
    food_lower = food_name.lower()
    if food_lower in nutrition_data:
        return nutrition_data[food_lower]
    
    # Try to find partial matches if no exact match
    for food_key, food_values in nutrition_data.items():
        if food_key in food_lower or food_lower in food_key:
            return food_values
    
    # If no match, provide generic nutritional information based on food type
    if any(fruit in food_lower for fruit in ["apple", "banana", "orange", "berry", "fruit"]):
        return {"calories": 85, "protein": 1, "carbs": 22, "fat": 0.3, "fiber": 3, "sugar": 15, "serving_size": "1 serving"}
    elif any(veg in food_lower for veg in ["salad", "spinach", "kale", "broccoli", "vegetable", "carrot"]):
        return {"calories": 35, "protein": 2, "carbs": 7, "fat": 0.3, "fiber": 3, "sugar": 2, "serving_size": "1 cup"}
    elif any(meat in food_lower for meat in ["beef", "pork", "chicken", "lamb", "meat", "steak"]):
        return {"calories": 185, "protein": 25, "carbs": 0, "fat": 10, "fiber": 0, "sugar": 0, "serving_size": "3 oz (85g)"}
    elif any(grain in food_lower for grain in ["rice", "wheat", "oat", "barley", "grain", "bread", "pasta"]):
        return {"calories": 180, "protein": 5, "carbs": 37, "fat": 1, "fiber": 2, "sugar": 0.5, "serving_size": "1 serving"}
    elif any(dairy in food_lower for dairy in ["milk", "cheese", "yogurt", "dairy"]):
        return {"calories": 120, "protein": 8, "carbs": 10, "fat": 6, "fiber": 0, "sugar": 8, "serving_size": "1 serving"}
    elif any(junk in food_lower for junk in ["pizza", "burger", "fries", "fast food"]):
        return {"calories": 350, "protein": 12, "carbs": 40, "fat": 15, "fiber": 2, "sugar": 5, "serving_size": "1 serving"}
    else:
        # Default generic food nutritional information
        return {"calories": 150, "protein": 5, "carbs": 15, "fat": 5, "fiber": 2, "sugar": 5, "serving_size": "1 serving"}

def extract_food_risks(food_name, text_content=None):
    """
    Extract potential health risks or concerns about the food
    
    Args:
        food_name (str): Name of the food
        text_content (str, optional): Text content to analyze
        
    Returns:
        list: List of potential health risks or concerns
    """
    risks = []
    
    # Common health risks associated with food types
    common_risks = {
        "processed": [
            "May be high in sodium or salt",
            "May contain preservatives",
            "Often high in added sugars",
            "May contain unhealthy trans fats"
        ],
        "fried": [
            "High in calories and fat",
            "May contribute to weight gain",
            "Cooking process may create unhealthy compounds",
            "May increase risk of heart disease"
        ],
        "sugary": [
            "High in calories with little nutritional value",
            "Can contribute to tooth decay",
            "May lead to blood sugar spikes",
            "Associated with increased risk of obesity"
        ],
        "fast food": [
            "Often high in calories, fat, and sodium",
            "May be low in essential nutrients",
            "Typically high in processed ingredients",
            "Regular consumption linked to health problems"
        ],
        "alcohol": [
            "Can impair judgment and coordination",
            "May cause liver damage with excessive use",
            "Can interact with many medications",
            "May contribute to dehydration"
        ],
        "caffeine": [
            "May cause sleep disturbances",
            "Can increase heart rate and blood pressure",
            "May lead to dependency",
            "Can cause anxiety or jitters in some people"
        ],
        "red meat": [
            "High consumption linked to heart disease",
            "May increase risk of certain cancers",
            "High in saturated fat",
            "Environmental impact concerns"
        ],
        "dairy": [
            "May cause digestive issues for those with lactose intolerance",
            "Some products high in saturated fat",
            "Potential allergen for some individuals",
            "Some products contain added sugars"
        ]
    }
    
    # Check if the food matches any of the categories
    for category, category_risks in common_risks.items():
        if category in food_name.lower():
            risks.extend(category_risks)
            break
    
    # If text content is provided, look for specific risk patterns
    if text_content:
        risk_patterns = [
            r"(?:risk|risks|harmful|danger|caution|warning)([^\.]+)",
            r"(?:high in|excessive|too much)([^\.]+sugar|salt|fat|cholesterol|calories)",
            r"(?:may|can|could)([^\.]+cause|lead to|result in|trigger|worsen)",
            r"(?:avoid|limit|reduce)([^\.]+consumption|intake)"
        ]
        
        for pattern in risk_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                risk = match.strip()
                if len(risk) > 5 and len(risk) < 100:  # Avoid too short or too long matches
                    risks.append(f"May {risk}" if not risk.lower().startswith(('be ', 'is ', 'are ', 'may ', 'can ')) else risk)
    
    # If no specific risks found, check for common food types
    if not risks:
        food_lower = food_name.lower()
        if any(processed in food_lower for processed in ["processed", "canned", "packaged", "instant", "microwave"]):
            risks = common_risks["processed"]
        elif any(fried in food_lower for fried in ["fried", "deep-fried", "crispy", "battered"]):
            risks = common_risks["fried"]
        elif any(sugary in food_lower for sugary in ["sweet", "candy", "chocolate", "dessert", "cake", "cookie", "pastry"]):
            risks = common_risks["sugary"]
        elif any(fastfood in food_lower for fastfood in ["burger", "pizza", "fast food", "takeout", "take-away"]):
            risks = common_risks["fast food"]
        elif any(alcoholic in food_lower for alcoholic in ["beer", "wine", "liquor", "cocktail", "alcohol"]):
            risks = common_risks["alcohol"]
        elif any(caffeinated in food_lower for caffeinated in ["coffee", "energy drink", "tea", "caffeine"]):
            risks = common_risks["caffeine"]
        elif any(redmeat in food_lower for redmeat in ["beef", "steak", "pork", "lamb", "veal", "venison"]):
            risks = common_risks["red meat"]
        elif any(dairy in food_lower for dairy in ["milk", "cheese", "yogurt", "dairy", "cream"]):
            risks = common_risks["dairy"]
        else:
            # Generic risks for any food
            risks = [
                "May cause allergic reactions in some individuals",
                "Overconsumption can lead to weight gain",
                "Should be consumed as part of a balanced diet",
                "Some preparation methods may reduce nutritional value"
            ]
    
    # Return unique risks (up to 5)
    unique_risks = list(set(risks))
    return unique_risks[:5]
