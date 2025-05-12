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
        food_info = {
            "name": food_name,
            "ingredients": [],
            "nutrients": {},
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
        food_info = {
            "name": food_name,
            "ingredients": extract_ingredients_from_text(text_content),
            "nutrients": {},
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
    food_info = {
        "name": food_name,
        "ingredients": [],
        "nutrients": {},
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
