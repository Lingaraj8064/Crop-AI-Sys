"""
Crop Disease Detection System - Chatbot Service
Service for handling chatbot conversations and agricultural knowledge
"""

import json
import re
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import random

from app.models.plant_database import PlantDatabase
from app.services.plant_info_service import PlantInfoService

class ChatbotService:
    """Service class for agricultural chatbot functionality"""
    
    def __init__(self):
        """Initialize the chatbot service"""
        self.plant_db = PlantDatabase()
        self.plant_info_service = PlantInfoService()
        self.session_contexts = {}  # Store conversation contexts
        self.knowledge_base = self._load_knowledge_base()
        self.intent_patterns = self._load_intent_patterns()
        self.response_templates = self._load_response_templates()
    
    def process_message(self, user_message: str, session_id: str, context: Dict = None) -> Dict:
        """
        Process user message and generate appropriate response
        
        Args:
            user_message: User's input message
            session_id: Session identifier
            context: Additional context information
            
        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()
        
        try:
            # Clean and preprocess message
            cleaned_message = self._preprocess_message(user_message)
            
            # Get session context
            session_context = self._get_session_context(session_id)
            if context:
                session_context.update(context)
            
            # Detect intent
            intent_result = self._detect_intent(cleaned_message, session_context)
            intent = intent_result['intent']
            confidence = intent_result['confidence']
            entities = intent_result['entities']
            
            # Generate response based on intent
            response_data = self._generate_response(
                intent=intent,
                entities=entities,
                user_message=cleaned_message,
                session_context=session_context
            )
            
            # Update session context
            self._update_session_context(session_id, {
                'last_intent': intent,
                'last_entities': entities,
                'last_user_message': user_message,
                'conversation_turn': session_context.get('conversation_turn', 0) + 1
            })
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'response': response_data['response'],
                'type': intent,
                'confidence': confidence,
                'processing_time': processing_time,
                'entities': entities,
                'suggestions': response_data.get('suggestions', []),
                'context_updated': True
            }
            
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            return {
                'success': False,
                'error': 'Failed to process message',
                'response': "I'm sorry, I encountered an error processing your message. Could you please try again?",
                'processing_time': time.time() - start_time
            }
    
    def _preprocess_message(self, message: str) -> str:
        """Clean and preprocess user message"""
        # Convert to lowercase
        cleaned = message.lower().strip()
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Handle common abbreviations
        abbreviations = {
            "what's": "what is",
            "how's": "how is", 
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "doesn't": "does not"
        }
        
        for abbr, full in abbreviations.items():
            cleaned = cleaned.replace(abbr, full)
        
        return cleaned
    
    def _detect_intent(self, message: str, context: Dict) -> Dict:
        """
        Detect user intent from message
        
        Args:
            message: Preprocessed user message
            context: Session context
            
        Returns:
            Dictionary with intent, confidence, and entities
        """
        best_intent = 'general'
        best_confidence = 0.0
        entities = {}
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns['keywords']:
                # Simple keyword matching with scoring
                matches = 0
                total_keywords = len(pattern)
                
                for keyword in pattern:
                    if keyword.lower() in message:
                        matches += 1
                
                if total_keywords > 0:
                    confidence = matches / total_keywords
                    
                    # Boost confidence if multiple keywords match
                    if matches > 1:
                        confidence *= 1.2
                    
                    # Context boost
                    if context.get('last_intent') == intent:
                        confidence *= 1.1
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent
        
        # Extract entities based on intent
        entities = self._extract_entities(message, best_intent)
        
        return {
            'intent': best_intent,
            'confidence': min(best_confidence, 1.0),
            'entities': entities
        }
    
    def _extract_entities(self, message: str, intent: str) -> Dict:
        """Extract entities from message based on intent"""
        entities = {}
        
        # Plant names
        for plant in self.plant_db.get_all_plants():
            plant_name = plant.common_name.lower()
            if plant_name in message:
                entities['plant'] = plant.common_name
                entities['plant_id'] = plant.id
                break
        
        # Disease names
        for disease in self.plant_db.get_all_diseases():
            disease_name = disease.name.lower()
            if disease_name in message:
                entities['disease'] = disease.name
                break
        
        # Numbers (for measurements, quantities)
        numbers = re.findall(r'\b\d+\.?\d*\b', message)
        if numbers:
            entities['numbers'] = numbers
        
        # Seasonal references
        seasons = ['spring', 'summer', 'fall', 'autumn', 'winter']
        for season in seasons:
            if season in message:
                entities['season'] = season
                break
        
        # Problem indicators
        problem_words = ['problem', 'issue', 'disease', 'pest', 'dying', 'wilting', 'spots', 'yellow', 'brown']
        for word in problem_words:
            if word in message:
                entities['problem_type'] = word
                break
        
        return entities
    
    def _generate_response(self, intent: str, entities: Dict, user_message: str, session_context: Dict) -> Dict:
        """Generate response based on intent and entities"""
        try:
            response_data = {'response': '', 'suggestions': []}
            
            if intent == 'greeting':
                response_data = self._handle_greeting(entities, session_context)
            
            elif intent == 'plant_identification':
                response_data = self._handle_plant_identification(entities, user_message)
            
            elif intent == 'disease_symptoms':
                response_data = self._handle_disease_symptoms(entities, user_message)
            
            elif intent == 'treatment_advice':
                response_data = self._handle_treatment_advice(entities, user_message)
            
            elif intent == 'growing_conditions':
                response_data = self._handle_growing_conditions(entities, user_message)
            
            elif intent == 'pest_management':
                response_data = self._handle_pest_management(entities, user_message)
            
            elif intent == 'soil_management':
                response_data = self._handle_soil_management(entities, user_message)
            
            elif intent == 'watering_irrigation':
                response_data = self._handle_watering_irrigation(entities, user_message)
            
            elif intent == 'fertilization':
                response_data = self._handle_fertilization(entities, user_message)
            
            elif intent == 'harvesting':
                response_data = self._handle_harvesting(entities, user_message)
            
            elif intent == 'seasonal_care':
                response_data = self._handle_seasonal_care(entities, user_message)
            
            elif intent == 'organic_farming':
                response_data = self._handle_organic_farming(entities, user_message)
            
            else:
                response_data = self._handle_general_query(entities, user_message, session_context)
            
            return response_data
            
        except Exception as e:
            logging.error(f"Error generating response for intent {intent}: {e}")
            return {
                'response': "I understand you're asking about farming, but I need a bit more information. Could you rephrase your question?",
                'suggestions': ["Ask about plant diseases", "Get growing tips", "Learn about soil management"]
            }
    
    def _handle_greeting(self, entities: Dict, context: Dict) -> Dict:
        """Handle greeting messages"""
        greetings = [
            "Hello! I'm your agricultural AI assistant. How can I help you with your crops today?",
            "Hi there! I'm here to help with all your farming and gardening questions. What would you like to know?",
            "Welcome! I can assist you with plant diseases, growing tips, soil management, and more. What's on your mind?",
            "Greetings! I'm ready to help you with agricultural advice and crop management. How can I assist you?"
        ]
        
        suggestions = [
            "Identify a plant disease",
            "Get growing tips for a specific plant",
            "Learn about soil management",
            "Ask about pest control"
        ]
        
        return {
            'response': random.choice(greetings),
            'suggestions': suggestions
        }
    
    def _handle_plant_identification(self, entities: Dict, message: str) -> Dict:
        """Handle plant identification requests"""
        if entities.get('plant'):
            plant_name = entities['plant']
            plant_info = self.plant_info_service.get_plant_info(entities.get('plant_id', plant_name.lower()))
            
            if plant_info['success']:
                plant_data = plant_info['data']
                response = f"I can help you with {plant_name} ({plant_data['scientific_name']})! "
                response += f"This is a {plant_data['category']} that belongs to the {plant_data['family']} family. "
                response += f"It's suitable for USDA zones and requires {plant_data['soil_conditions']['drainage']}. "
                response += "What specific information would you like to know about this plant?"
                
                suggestions = [
                    f"Growing conditions for {plant_name}",
                    f"Common diseases of {plant_name}",
                    f"Care instructions for {plant_name}",
                    f"Harvesting tips for {plant_name}"
                ]
            else:
                response = "I'd be happy to help you identify a plant! Could you provide more details like the plant name, leaf shape, flower color, or upload an image for analysis?"
                suggestions = [
                    "Upload an image for identification",
                    "Describe the plant characteristics",
                    "Ask about common garden plants"
                ]
        else:
            response = "I can help you identify plants! You can either upload an image using our disease detection feature or describe the plant you're curious about."
            suggestions = [
                "Upload a plant image",
                "Ask about apple trees",
                "Ask about tomato plants",
                "Ask about corn crops"
            ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def _handle_disease_symptoms(self, entities: Dict, message: str) -> Dict:
        """Handle disease symptom questions"""
        if entities.get('plant') and entities.get('disease'):
            plant_name = entities['plant']
            disease_name = entities['disease']
            
            plant_info = self.plant_info_service.get_plant_info(entities.get('plant_id', plant_name.lower()))
            if plant_info['success']:
                plant_data = plant_info['data']
                for disease in plant_data.get('diseases', []):
                    if disease['name'].lower() == disease_name.lower():
                        response = f"{disease_name} in {plant_name} shows these symptoms: {disease['symptoms']}. "
                        response += f"This is caused by {disease['causes']}. "
                        response += f"The severity level is {disease['severity']}."
                        
                        suggestions = [
                            f"Treatment for {disease_name}",
                            f"Prevention of {disease_name}",
                            f"Immediate action for {disease_name}"
                        ]
                        return {'response': response, 'suggestions': suggestions}
        
        elif entities.get('plant'):
            plant_name = entities['plant']
            response = f"Common diseases in {plant_name} include various fungal, bacterial, and viral infections. "
            response += "The most frequent symptoms to watch for are discolored leaves, spots, wilting, unusual growths, or stunted development. "
            response += "Could you describe the specific symptoms you're seeing?"
            
        else:
            response = "Disease symptoms can vary widely, but common signs include:\n"
            response += "• Discolored or spotted leaves (yellow, brown, black spots)\n"
            response += "• Wilting or drooping despite adequate water\n"
            response += "• Unusual growths or galls\n"
            response += "• Stunted or distorted growth\n"
            response += "• Premature leaf drop\n\n"
            response += "Which plant are you concerned about, and what symptoms are you observing?"
        
        suggestions = [
            "Upload an image for disease detection",
            "Ask about specific plant diseases",
            "Learn about disease prevention"
        ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def _handle_treatment_advice(self, entities: Dict, message: str) -> Dict:
        """Handle treatment advice requests"""
        if entities.get('plant') and entities.get('disease'):
            plant_name = entities['plant']
            disease_name = entities['disease']
            
            plant_info = self.plant_info_service.get_plant_info(entities.get('plant_id', plant_name.lower()))
            if plant_info['success']:
                plant_data = plant_info['data']
                for disease in plant_data.get('diseases', []):
                    if disease['name'].lower() == disease_name.lower():
                        response = f"Treatment for {disease_name} in {plant_name}:\n\n"
                        response += "**Immediate Action:** " + disease['immediate_action'] + "\n\n"
                        response += "**Treatment Steps:**\n"
                        for i, treatment in enumerate(disease['treatment'][:4], 1):
                            response += f"{i}. {treatment}\n"
                        
                        if disease.get('organic_treatment'):
                            response += "\n**Organic Options:**\n"
                            for treatment in disease['organic_treatment'][:3]:
                                response += f"• {treatment}\n"
                        
                        suggestions = [
                            f"Prevention tips for {disease_name}",
                            "Organic treatment options",
                            "When to seek professional help"
                        ]
                        return {'response': response, 'suggestions': suggestions}
        
        response = "For effective disease treatment, I need to know:\n"
        response += "1. What plant you're treating\n"
        response += "2. What disease or symptoms you're seeing\n"
        response += "3. How severe the infection is\n\n"
        response += "Could you provide more details? You can also upload an image for accurate diagnosis."
        
        suggestions = [
            "Upload plant image for diagnosis",
            "Ask about fungicide applications", 
            "Learn about organic treatments",
            "Get prevention strategies"
        ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def _handle_growing_conditions(self, entities: Dict, message: str) -> Dict:
        """Handle growing conditions questions"""
        if entities.get('plant'):
            plant_name = entities['plant']
            plant_info = self.plant_info_service.get_plant_info(entities.get('plant_id', plant_name.lower()))
            
            if plant_info['success']:
                plant_data = plant_info['data']
                soil = plant_data['soil_requirements']
                weather = plant_data['weather_requirements']
                
                response = f"Optimal growing conditions for {plant_name}:\n\n"
                response += f"**Soil Requirements:**\n"
                response += f"• pH: {soil['ph_range']}\n"
                response += f"• Drainage: {soil['drainage']}\n"
                response += f"• Depth: {soil['depth_requirement']}\n\n"
                response += f"**Climate Requirements:**\n"
                response += f"• Temperature: {weather['optimal_temperature']}\n"
                response += f"• Sunlight: {weather['sunlight']}\n"
                response += f"• Rainfall: {weather['rainfall']}\n"
                
                if plant_data.get('suitable_regions'):
                    response += f"\n**Best Growing Regions:** {', '.join(plant_data['suitable_regions'][:3])}"
                
                suggestions = [
                    f"Soil preparation for {plant_name}",
                    f"Watering schedule for {plant_name}",
                    f"Fertilizing {plant_name}",
                    f"Common problems with {plant_name}"
                ]
            else:
                response = f"I'd love to help with growing conditions for {plant_name}, but I need more specific information. Could you clarify which variety or provide more details?"
                suggestions = ["Ask about common plants", "Specify plant variety"]
        else:
            response = "Growing conditions vary significantly by plant type. Key factors include:\n"
            response += "• **Soil:** pH, drainage, organic content\n"
            response += "• **Climate:** Temperature range, humidity, rainfall\n"
            response += "• **Light:** Full sun, partial shade, or shade\n"
            response += "• **Space:** Plant spacing and root depth requirements\n\n"
            response += "Which plant are you interested in growing?"
            
            suggestions = [
                "Ask about apple growing conditions",
                "Ask about tomato growing conditions", 
                "Ask about corn growing conditions",
                "Learn about soil preparation"
            ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def _handle_pest_management(self, entities: Dict, message: str) -> Dict:
        """Handle pest management questions"""
        response = "Effective pest management uses Integrated Pest Management (IPM) principles:\n\n"
        response += "**1. Prevention:**\n"
        response += "• Maintain healthy soil and plants\n"
        response += "• Choose resistant varieties\n"
        response += "• Practice crop rotation\n"
        response += "• Remove plant debris\n\n"
        response += "**2. Monitoring:**\n" 
        response += "• Regular inspection of plants\n"
        response += "• Identify pests early\n"
        response += "• Monitor beneficial insects\n\n"
        response += "**3. Control Methods:**\n"
        response += "• Biological: Beneficial insects, natural predators\n"
        response += "• Physical: Row covers, traps, barriers\n"
        response += "• Chemical: Targeted, least-toxic options first\n\n"
        
        if entities.get('plant'):
            plant_name = entities['plant']
            response += f"For {plant_name} specifically, common pests include aphids, spider mites, and various caterpillars."
        
        suggestions = [
            "Identify beneficial insects",
            "Organic pest control methods",
            "When to use pesticides",
            "Natural pest deterrents"
        ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def _handle_soil_management(self, entities: Dict, message: str) -> Dict:
        """Handle soil management questions"""
        response = "Healthy soil is the foundation of successful growing! Here are key soil management practices:\n\n"
        response += "**Soil Testing:**\n"
        response += "• Test pH levels (most plants prefer 6.0-7.0)\n"
        response += "• Check nutrient levels (N-P-K)\n"
        response += "• Assess organic matter content\n"
        response += "• Test every 2-3 years\n\n"
        response += "**Soil Improvement:**\n"
        response += "• Add compost regularly (2-4 inches annually)\n"
        response += "• Use organic mulch to retain moisture\n"
        response += "• Avoid compaction - don't work wet soil\n"
        response += "• Consider cover crops in off-season\n\n"
        response += "**Drainage:**\n"
        response += "• Ensure proper drainage to prevent root rot\n"
        response += "• Add organic matter to improve structure\n"
        response += "• Consider raised beds for problem areas\n"
        
        if entities.get('plant'):
            plant_name = entities['plant']
            plant_info = self.plant_info_service.get_plant_info(entities.get('plant_id', plant_name.lower()))
            if plant_info['success']:
                soil_req = plant_info['data']['soil_requirements']
                response += f"\n**For {plant_name} specifically:**\n"
                response += f"• pH: {soil_req['ph_range']}\n"
                response += f"• {soil_req['drainage']}\n"
        
        suggestions = [
            "How to test soil pH",
            "Making compost at home",
            "Improving clay soil",
            "Improving sandy soil"
        ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def _handle_watering_irrigation(self, entities: Dict, message: str) -> Dict:
        """Handle watering and irrigation questions"""
        response = "Proper watering is crucial for plant health. Here are key principles:\n\n"
        response += "**General Guidelines:**\n"
        response += "• Water deeply but less frequently\n"
        response += "• Water early morning (6-10 AM) for best absorption\n"
        response += "• Check soil moisture 2-3 inches deep\n"
        response += "• Adjust frequency based on weather and season\n\n"
        response += "**Watering Methods:**\n"
        response += "• **Drip irrigation:** Most efficient, reduces disease\n"
        response += "• **Soaker hoses:** Good for garden beds\n"
        response += "• **Hand watering:** Best for containers and new plants\n"
        response += "• **Sprinklers:** Avoid if possible, can promote disease\n\n"
        response += "**Signs of Problems:**\n"
        response += "• **Overwatering:** Yellow leaves, root rot, fungal issues\n"
        response += "• **Underwatering:** Wilting, dry/crispy leaves, stunted growth\n"
        
        if entities.get('plant'):
            plant_name = entities['plant']
            response += f"\n**For {plant_name}:** Most crops need 1-2 inches of water per week, including rainfall."
        
        suggestions = [
            "Setting up drip irrigation",
            "Watering container plants",
            "Watering during drought",
            "Signs of overwatering"
        ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def _handle_fertilization(self, entities: Dict, message: str) -> Dict:
        """Handle fertilization questions"""
        response = "Plant nutrition is essential for healthy growth and disease resistance:\n\n"
        response += "**Primary Nutrients (N-P-K):**\n"
        response += "• **Nitrogen (N):** Promotes leaf growth and green color\n"
        response += "• **Phosphorus (P):** Essential for root development and flowering\n"
        response += "• **Potassium (K):** Improves disease resistance and fruit quality\n\n"
        response += "**Fertilization Schedule:**\n"
        response += "• **Spring:** Apply balanced fertilizer as growth begins\n"
        response += "• **Growing season:** Side-dress with compost or organic fertilizer\n"
        response += "• **Fall:** Reduce nitrogen, focus on phosphorus and potassium\n\n"
        response += "**Organic Options:**\n"
        response += "• Compost: Slow-release, improves soil structure\n"
        response += "• Fish emulsion: Quick nitrogen boost\n"
        response += "• Bone meal: Phosphorus for flowering/fruiting\n"
        response += "• Kelp meal: Potassium and trace minerals\n"
        
        if entities.get('plant'):
            plant_name = entities['plant']
            plant_info = self.plant_info_service.get_plant_info(entities.get('plant_id', plant_name.lower()))
            if plant_info['success']:
                nutrition = plant_info['data']['care_instructions'].get('fertilization', [])
                if nutrition:
                    response += f"\n**For {plant_name}:**\n"
                    for tip in nutrition[:3]:
                        response += f"• {tip}\n"
        
        suggestions = [
            "Organic fertilizer recipes",
            "When to fertilize seedlings",
            "Signs of nutrient deficiency",
            "Compost tea benefits"
        ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def _handle_harvesting(self, entities: Dict, message: str) -> Dict:
        """Handle harvesting questions"""
        if entities.get('plant'):
            plant_name = entities['plant']
            plant_info = self.plant_info_service.get_plant_info(entities.get('plant_id', plant_name.lower()))
            
            if plant_info['success']:
                harvest_info = plant_info['data']['care_instructions'].get('harvesting', '')
                response = f"Harvesting {plant_name}:\n\n"
                response += f"**When to Harvest:** {harvest_info}\n\n"
                response += "**General Harvesting Tips:**\n"
                response += "• Harvest in the morning when plants are well-hydrated\n"
                response += "• Use clean, sharp tools to avoid damaging plants\n"
                response += "• Handle produce gently to prevent bruising\n"
                response += "• Regular harvesting often encourages more production\n"
                
                suggestions = [
                    f"Storage tips for {plant_name}",
                    f"Processing {plant_name} after harvest",
                    "Extending harvest season"
                ]
            else:
                response = f"I'd be happy to help with harvesting {plant_name}! Could you specify which variety you're growing?"
                suggestions = ["Ask about specific varieties"]
        else:
            response = "Harvest timing varies by crop, but here are general principles:\n\n"
            response += "• **Fruits:** Harvest when fully colored and slightly soft\n"
            response += "• **Leafy greens:** Pick outer leaves, let center continue growing\n"
            response += "• **Root vegetables:** Check size by gently digging around base\n"
            response += "• **Seeds/grains:** Harvest when dry and fully mature\n\n"
            response += "Which specific crop are you looking to harvest?"
            
            suggestions = [
                "Harvesting tomatoes",
                "Harvesting apples", 
                "Harvesting corn",
                "Post-harvest storage"
            ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def _handle_seasonal_care(self, entities: Dict, message: str) -> Dict:
        """Handle seasonal care questions"""
        current_season = entities.get('season', self._get_current_season())
        
        seasonal_tasks = {
            'spring': [
                "Start seeds indoors or plant outdoors after last frost",
                "Apply compost and organic fertilizers",
                "Prune damaged or dead branches",
                "Set up irrigation systems",
                "Begin pest monitoring programs"
            ],
            'summer': [
                "Maintain consistent watering schedule",
                "Harvest crops as they ripen",
                "Monitor for pests and diseases",
                "Provide shade for heat-sensitive plants",
                "Side-dress plants with compost"
            ],
            'fall': [
                "Harvest remaining crops before frost",
                "Plant cover crops in empty beds",
                "Collect and compost healthy plant debris",
                "Prepare tender plants for winter",
                "Plan next year's garden layout"
            ],
            'winter': [
                "Plan next season's planting schedule",
                "Order seeds and plan garden changes", 
                "Maintain tools and equipment",
                "Study new growing techniques",
                "Protect plants from frost and cold"
            ]
        }
        
        response = f"**{current_season.title()} Care Tasks:**\n\n"
        for i, task in enumerate(seasonal_tasks[current_season], 1):
            response += f"{i}. {task}\n"
        
        if entities.get('plant'):
            plant_name = entities['plant']
            seasonal_guide = self.plant_info_service.get_seasonal_care_guide(
                entities.get('plant_id', plant_name.lower()), 
                current_season
            )
            if seasonal_guide['success']:
                specific_tasks = seasonal_guide['data']['seasonal_specific'][:3]
                response += f"\n**Specific to {plant_name} in {current_season}:**\n"
                for task in specific_tasks:
                    response += f"• {task}\n"
        
        suggestions = [
            f"Next season preparation",
            f"Weather protection tips",
            f"Seasonal plant problems"
        ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def _handle_organic_farming(self, entities: Dict, message: str) -> Dict:
        """Handle organic farming questions"""
        response = "Organic farming focuses on sustainable, natural methods:\n\n"
        response += "**Core Principles:**\n"
        response += "• Build healthy soil through composting and organic matter\n"
        response += "• Use natural pest and disease management\n"
        response += "• Promote biodiversity and beneficial insects\n"
        response += "• Avoid synthetic chemicals and GMOs\n\n"
        response += "**Soil Building:**\n"
        response += "• Add 2-4 inches of compost annually\n"
        response += "• Use organic mulches to suppress weeds\n"
        response += "• Practice crop rotation to prevent soil depletion\n"
        response += "• Plant cover crops to add nitrogen and organic matter\n\n"
        response += "**Natural Pest Control:**\n"
        response += "• Encourage beneficial insects with diverse plantings\n"
        response += "• Use companion planting strategies\n"
        response += "• Apply organic-approved treatments like neem oil\n"
        response += "• Practice good garden sanitation\n\n"
        response += "**Organic Fertilizers:**\n"
        response += "• Compost and compost tea\n"
        response += "• Fish emulsion and kelp meal\n"
        response += "• Bone meal and blood meal\n"
        response += "• Green manure crops\n"
        
        suggestions = [
            "Making compost at home",
            "Companion planting guide",
            "Natural pest deterrents",
            "Organic certification process"
        ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def _handle_general_query(self, entities: Dict, message: str, context: Dict) -> Dict:
        """Handle general agricultural queries"""
        # Try to match with knowledge base
        for topic, info in self.knowledge_base.items():
            if any(keyword in message for keyword in info.get('keywords', [])):
                return {
                    'response': info['response'],
                    'suggestions': info.get('suggestions', [])
                }
        
        # Default response
        response = "I'm here to help with agricultural and farming questions! I can assist you with:\n\n"
        response += "• **Plant Disease Identification:** Upload images or describe symptoms\n"
        response += "• **Growing Advice:** Optimal conditions, planting, care instructions\n"
        response += "• **Problem Diagnosis:** Pest issues, nutrient deficiencies, diseases\n"
        response += "• **Seasonal Care:** What to do throughout the growing season\n"
        response += "• **Organic Methods:** Natural and sustainable farming practices\n\n"
        response += "What specific farming topic would you like to explore?"
        
        suggestions = [
            "Upload a plant image for analysis",
            "Ask about a specific plant",
            "Get soil management tips",
            "Learn about organic farming"
        ]
        
        return {'response': response, 'suggestions': suggestions}
    
    def get_suggested_questions(self, category: str = 'general') -> List[str]:
        """Get suggested questions for users"""
        suggestions = {
            'general': [
                "How do I identify plant diseases?",
                "What are the signs of overwatering?",
                "When should I fertilize my plants?",
                "How do I improve my soil quality?",
                "What is integrated pest management?"
            ],
            'diseases': [
                "What causes yellow leaves on tomatoes?",
                "How do I treat fungal infections?",
                "What are the symptoms of blight?",
                "How can I prevent plant diseases?",
                "When should I use fungicides?"
            ],
            'growing': [
                "What pH should my soil be?",
                "How much water do vegetables need?",
                "When is the best time to plant?",
                "How do I prepare soil for planting?",
                "What plants grow well together?"
            ],
            'organic': [
                "How do I make compost?",
                "What are natural pest control methods?",
                "How do I attract beneficial insects?",
                "What organic fertilizers work best?",
                "How do I transition to organic farming?"
            ]
        }
        
        return suggestions.get(category, suggestions['general'])
    
    def set_session_context(self, session_id: str, context_type: str, context_data: Dict) -> Dict:
        """Set context for a conversation session"""
        try:
            if session_id not in self.session_contexts:
                self.session_contexts[session_id] = {}
            
            self.session_contexts[session_id].update({
                'context_type': context_type,
                'context_data': context_data,
                'context_timestamp': datetime.now().timestamp()
            })
            
            return {'success': True}
            
        except Exception as e:
            logging.error(f"Error setting session context: {e}")
            return {'success': False, 'error': str(e)}
    
    def clear_session_context(self, session_id: str):
        """Clear context for a session"""
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
    
    def process_feedback(self, message_id: str, feedback_type: str, feedback_text: str) -> Dict:
        """Process user feedback on responses"""
        try:
            # Here you would typically log feedback to improve the system
            logging.info(f"Feedback received - Message: {message_id}, Type: {feedback_type}, Text: {feedback_text}")
            
            return {'success': True, 'message': 'Feedback recorded successfully'}
            
        except Exception as e:
            logging.error(f"Error processing feedback: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_session_context(self, session_id: str) -> Dict:
        """Get session context"""
        return self.session_contexts.get(session_id, {})
    
    def _update_session_context(self, session_id: str, updates: Dict):
        """Update session context"""
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {}
        
        self.session_contexts[session_id].update(updates)
    
    def _get_current_season(self) -> str:
        """Get current season"""
        month = datetime.now().month
        if 3 <= month <= 5:
            return 'spring'
        elif 6 <= month <= 8:
            return 'summer'
        elif 9 <= month <= 11:
            return 'fall'
        else:
            return 'winter'
    
    def _load_knowledge_base(self) -> Dict:
        """Load general agricultural knowledge base"""
        return {
            'companion_planting': {
                'keywords': ['companion', 'together', 'plant combinations'],
                'response': "Companion planting involves growing complementary plants together. Great combinations include tomatoes with basil, corn with beans and squash (Three Sisters), and marigolds with most vegetables for pest control.",
                'suggestions': ["Three Sisters planting method", "Pest-deterrent companion plants", "Beneficial plant combinations"]
            },
            'crop_rotation': {
                'keywords': ['crop rotation', 'rotating crops', 'plant succession'],
                'response': "Crop rotation prevents soil depletion and breaks pest/disease cycles. Rotate plant families: follow heavy feeders (tomatoes) with light feeders (herbs), then soil builders (legumes), then root crops.",
                'suggestions': ["4-year rotation plan", "Benefits of crop rotation", "Planning garden layout"]
            }
        }
    
    def _load_intent_patterns(self) -> Dict:
        """Load intent recognition patterns"""
        return {
            'greeting': {
                'keywords': [
                    ['hello', 'hi', 'hey'],
                    ['good morning', 'good afternoon'],
                    ['greetings']
                ]
            },
            'plant_identification': {
                'keywords': [
                    ['what', 'plant', 'is'],
                    ['identify', 'plant'],
                    ['what', 'type', 'plant'],
                    ['plant', 'name']
                ]
            },
            'disease_symptoms': {
                'keywords': [
                    ['symptoms', 'disease'],
                    ['what', 'wrong', 'plant'],
                    ['leaves', 'yellow', 'brown'],
                    ['spots', 'leaves'],
                    ['dying', 'wilting']
                ]
            },
            'treatment_advice': {
                'keywords': [
                    ['how', 'treat'],
                    ['treatment', 'disease'],
                    ['cure', 'fix'],
                    ['medicine', 'fungicide']
                ]
            },
            'growing_conditions': {
                'keywords': [
                    ['growing', 'conditions'],
                    ['how', 'grow'],
                    ['soil', 'requirements'],
                    ['temperature', 'climate']
                ]
            },
            'pest_management': {
                'keywords': [
                    ['pest', 'control'],
                    ['insects', 'bugs'],
                    ['aphids', 'caterpillars'],
                    ['natural', 'pest']
                ]
            },
            'soil_management': {
                'keywords': [
                    ['soil', 'ph'],
                    ['compost', 'fertilizer'],
                    ['soil', 'test'],
                    ['nutrients']
                ]
            },
            'watering_irrigation': {
                'keywords': [
                    ['water', 'irrigation'],
                    ['how', 'often', 'water'],
                    ['overwatering', 'underwatering'],
                    ['drip', 'irrigation']
                ]
            },
            'fertilization': {
                'keywords': [
                    ['fertilize', 'fertilizer'],
                    ['nutrients', 'feeding'],
                    ['nitrogen', 'phosphorus', 'potassium'],
                    ['organic', 'fertilizer']
                ]
            },
            'harvesting': {
                'keywords': [
                    ['harvest', 'harvesting'],
                    ['when', 'ready'],
                    ['ripe', 'mature'],
                    ['pick', 'picking']
                ]
            },
            'seasonal_care': {
                'keywords': [
                    ['spring', 'summer', 'fall', 'winter'],
                    ['seasonal', 'care'],
                    ['season', 'tasks'],
                    ['monthly', 'care']
                ]
            },
            'organic_farming': {
                'keywords': [
                    ['organic', 'natural'],
                    ['chemical', 'free'],
                    ['sustainable', 'farming'],
                    ['organic', 'methods']
                ]
            }
        }
    
    def _load_response_templates(self) -> Dict:
        """Load response templates"""
        return {
            'clarification_needed': [
                "Could you provide more details about {topic}?",
                "I'd be happy to help with {topic}! Could you be more specific?",
                "To give you the best advice about {topic}, I need a bit more information."
            ],
            'plant_not_found': [
                "I'm not familiar with that plant. Could you double-check the spelling or provide more details?",
                "That plant isn't in my database yet. Could you describe it or provide its scientific name?"
            ]
        }