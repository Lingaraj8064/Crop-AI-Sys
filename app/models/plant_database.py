"""
Crop Disease Detection System - Plant Database Models
Data structures and classes for plant and disease information
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

class SeverityLevel(Enum):
    """Disease severity levels"""
    LOW = "Low"
    MEDIUM = "Medium" 
    HIGH = "High"
    CRITICAL = "Critical"

class PlantCategory(Enum):
    """Plant category types"""
    FRUIT = "Fruit"
    VEGETABLE = "Vegetable"
    GRAIN = "Grain"
    HERB = "Herb"
    TREE = "Tree"
    LEGUME = "Legume"

@dataclass
class SoilRequirements:
    """Soil requirements data structure"""
    ph_min: float
    ph_max: float
    drainage: str
    nutrients: List[str]
    organic_matter: str
    depth_requirement: str
    soil_types: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'ph_range': f"{self.ph_min}-{self.ph_max}",
            'drainage': self.drainage,
            'nutrients': self.nutrients,
            'organic_matter': self.organic_matter,
            'depth_requirement': self.depth_requirement,
            'soil_types': self.soil_types
        }

@dataclass
class WeatherRequirements:
    """Weather requirements data structure"""
    temp_min: float
    temp_max: float
    temp_optimal_min: float
    temp_optimal_max: float
    rainfall_min: float
    rainfall_max: float
    humidity_range: str
    sunlight_hours: str
    frost_tolerance: str
    chill_hours: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'temperature_range': f"{self.temp_min}-{self.temp_max}°F",
            'optimal_temperature': f"{self.temp_optimal_min}-{self.temp_optimal_max}°F", 
            'rainfall': f"{self.rainfall_min}-{self.rainfall_max} inches annually",
            'humidity': self.humidity_range,
            'sunlight': self.sunlight_hours,
            'frost_tolerance': self.frost_tolerance,
            'chill_hours': self.chill_hours
        }

@dataclass
class DiseaseInfo:
    """Disease information data structure"""
    name: str
    scientific_name: Optional[str]
    severity: SeverityLevel
    disease_type: str  # fungal, bacterial, viral, nutritional
    symptoms: str
    causes: str
    prevention: List[str]
    treatment: List[str]
    immediate_action: str
    organic_treatment: List[str] = field(default_factory=list)
    affected_parts: List[str] = field(default_factory=list)
    favorable_conditions: str = ""
    spread_method: str = ""
    contagious_level: str = "Medium"
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'scientific_name': self.scientific_name,
            'severity': self.severity.value,
            'type': self.disease_type,
            'symptoms': self.symptoms,
            'causes': self.causes,
            'prevention': self.prevention,
            'treatment': self.treatment,
            'immediate_action': self.immediate_action,
            'organic_treatment': self.organic_treatment,
            'affected_parts': self.affected_parts,
            'favorable_conditions': self.favorable_conditions,
            'spread_method': self.spread_method,
            'contagious_level': self.contagious_level
        }

@dataclass
class CareInstructions:
    """Plant care instructions data structure"""
    watering: List[str]
    fertilization: List[str]
    pruning: List[str]
    pest_management: List[str]
    harvesting: str
    post_harvest: List[str] = field(default_factory=list)
    seasonal_care: Dict[str, List[str]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'watering': self.watering,
            'fertilization': self.fertilization,
            'pruning': self.pruning,
            'pest_management': self.pest_management,
            'harvesting': self.harvesting,
            'post_harvest': self.post_harvest,
            'seasonal_care': self.seasonal_care
        }

@dataclass
class PlantSpeciesData:
    """Complete plant species data structure"""
    id: str
    common_name: str
    scientific_name: str
    family: str
    category: PlantCategory
    soil_requirements: SoilRequirements
    weather_requirements: WeatherRequirements
    care_instructions: CareInstructions
    diseases: List[DiseaseInfo] = field(default_factory=list)
    suitable_regions: List[str] = field(default_factory=list)
    growing_season: str = ""
    maturity_time: str = ""
    yield_info: str = ""
    nutritional_value: Dict[str, Any] = field(default_factory=dict)
    companion_plants: List[str] = field(default_factory=list)
    incompatible_plants: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'common_name': self.common_name,
            'scientific_name': self.scientific_name,
            'family': self.family,
            'category': self.category.value,
            'soil_requirements': self.soil_requirements.to_dict(),
            'weather_requirements': self.weather_requirements.to_dict(),
            'care_instructions': self.care_instructions.to_dict(),
            'diseases': [disease.to_dict() for disease in self.diseases],
            'suitable_regions': self.suitable_regions,
            'growing_season': self.growing_season,
            'maturity_time': self.maturity_time,
            'yield_info': self.yield_info,
            'nutritional_value': self.nutritional_value,
            'companion_plants': self.companion_plants,
            'incompatible_plants': self.incompatible_plants
        }
    
    def get_disease_by_name(self, disease_name: str) -> Optional[DiseaseInfo]:
        """Get disease information by name"""
        for disease in self.diseases:
            if disease.name.lower() == disease_name.lower():
                return disease
        return None
    
    def is_healthy_conditions(self, soil_ph: float, temperature: float) -> bool:
        """Check if conditions are suitable for healthy growth"""
        soil_ok = self.soil_requirements.ph_min <= soil_ph <= self.soil_requirements.ph_max
        temp_ok = self.weather_requirements.temp_min <= temperature <= self.weather_requirements.temp_max
        return soil_ok and temp_ok

class PlantDatabase:
    """Plant database management class"""
    
    def __init__(self, data_file: str = None):
        """Initialize plant database"""
        self.data_file = data_file or 'app/data/plant_database.json'
        self.plants: Dict[str, PlantSpeciesData] = {}
        self.diseases: Dict[str, DiseaseInfo] = {}
        self._load_data()
    
    def _load_data(self):
        """Load plant data from JSON file or create default data"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self._parse_json_data(data)
            except Exception as e:
                print(f"Error loading plant database: {e}")
                self._create_default_data()
        else:
            self._create_default_data()
    
    def _parse_json_data(self, data: Dict):
        """Parse JSON data into plant objects"""
        for plant_id, plant_data in data.get('plants', {}).items():
            try:
                # Parse soil requirements
                soil_req = SoilRequirements(
                    ph_min=plant_data['soil_requirements']['ph_min'],
                    ph_max=plant_data['soil_requirements']['ph_max'],
                    drainage=plant_data['soil_requirements']['drainage'],
                    nutrients=plant_data['soil_requirements']['nutrients'],
                    organic_matter=plant_data['soil_requirements']['organic_matter'],
                    depth_requirement=plant_data['soil_requirements']['depth_requirement'],
                    soil_types=plant_data['soil_requirements'].get('soil_types', [])
                )
                
                # Parse weather requirements
                weather_req = WeatherRequirements(
                    temp_min=plant_data['weather_requirements']['temp_min'],
                    temp_max=plant_data['weather_requirements']['temp_max'],
                    temp_optimal_min=plant_data['weather_requirements']['temp_optimal_min'],
                    temp_optimal_max=plant_data['weather_requirements']['temp_optimal_max'],
                    rainfall_min=plant_data['weather_requirements']['rainfall_min'],
                    rainfall_max=plant_data['weather_requirements']['rainfall_max'],
                    humidity_range=plant_data['weather_requirements']['humidity_range'],
                    sunlight_hours=plant_data['weather_requirements']['sunlight_hours'],
                    frost_tolerance=plant_data['weather_requirements']['frost_tolerance'],
                    chill_hours=plant_data['weather_requirements'].get('chill_hours')
                )
                
                # Parse care instructions
                care_inst = CareInstructions(
                    watering=plant_data['care_instructions']['watering'],
                    fertilization=plant_data['care_instructions']['fertilization'],
                    pruning=plant_data['care_instructions']['pruning'],
                    pest_management=plant_data['care_instructions']['pest_management'],
                    harvesting=plant_data['care_instructions']['harvesting'],
                    post_harvest=plant_data['care_instructions'].get('post_harvest', []),
                    seasonal_care=plant_data['care_instructions'].get('seasonal_care', {})
                )
                
                # Parse diseases
                diseases = []
                for disease_data in plant_data.get('diseases', []):
                    disease = DiseaseInfo(
                        name=disease_data['name'],
                        scientific_name=disease_data.get('scientific_name'),
                        severity=SeverityLevel(disease_data['severity']),
                        disease_type=disease_data['type'],
                        symptoms=disease_data['symptoms'],
                        causes=disease_data['causes'],
                        prevention=disease_data['prevention'],
                        treatment=disease_data['treatment'],
                        immediate_action=disease_data['immediate_action'],
                        organic_treatment=disease_data.get('organic_treatment', []),
                        affected_parts=disease_data.get('affected_parts', []),
                        favorable_conditions=disease_data.get('favorable_conditions', ''),
                        spread_method=disease_data.get('spread_method', ''),
                        contagious_level=disease_data.get('contagious_level', 'Medium')
                    )
                    diseases.append(disease)
                    self.diseases[disease.name.lower().replace(' ', '_')] = disease
                
                # Create plant species
                plant = PlantSpeciesData(
                    id=plant_id,
                    common_name=plant_data['common_name'],
                    scientific_name=plant_data['scientific_name'],
                    family=plant_data['family'],
                    category=PlantCategory(plant_data['category']),
                    soil_requirements=soil_req,
                    weather_requirements=weather_req,
                    care_instructions=care_inst,
                    diseases=diseases,
                    suitable_regions=plant_data.get('suitable_regions', []),
                    growing_season=plant_data.get('growing_season', ''),
                    maturity_time=plant_data.get('maturity_time', ''),
                    yield_info=plant_data.get('yield_info', ''),
                    nutritional_value=plant_data.get('nutritional_value', {}),
                    companion_plants=plant_data.get('companion_plants', []),
                    incompatible_plants=plant_data.get('incompatible_plants', [])
                )
                
                self.plants[plant_id] = plant
                
            except Exception as e:
                print(f"Error parsing plant data for {plant_id}: {e}")
    
    def _create_default_data(self):
        """Create default plant data"""
        # Apple
        apple_diseases = [
            DiseaseInfo(
                name="Apple Scab",
                scientific_name="Venturia inaequalis",
                severity=SeverityLevel.HIGH,
                disease_type="fungal",
                symptoms="Dark, scaly lesions on leaves and fruit, premature leaf drop, reduced fruit quality",
                causes="Fungal infection caused by Venturia inaequalis, thrives in cool, moist conditions",
                prevention=[
                    "Plant resistant apple varieties",
                    "Ensure proper air circulation by pruning",
                    "Remove fallen leaves and debris",
                    "Apply preventive fungicides in early spring"
                ],
                treatment=[
                    "Apply copper-based fungicides",
                    "Use systemic fungicides like myclobutanil",
                    "Remove infected plant parts immediately",
                    "Improve orchard sanitation practices"
                ],
                immediate_action="Remove infected leaves and apply fungicide treatment immediately to prevent spread",
                organic_treatment=[
                    "Neem oil spray",
                    "Baking soda solution",
                    "Compost tea application"
                ],
                affected_parts=["leaves", "fruit", "twigs"],
                favorable_conditions="Cool, moist conditions with temperatures 55-75°F",
                spread_method="Wind and rain dispersal of spores",
                contagious_level="High"
            )
        ]
        
        apple_plant = PlantSpeciesData(
            id="apple",
            common_name="Apple",
            scientific_name="Malus domestica",
            family="Rosaceae",
            category=PlantCategory.FRUIT,
            soil_requirements=SoilRequirements(
                ph_min=6.0, ph_max=7.0,
                drainage="Well-draining, loamy soil",
                nutrients=["phosphorus", "potassium", "organic matter"],
                organic_matter="Rich in organic matter",
                depth_requirement="Minimum 3 feet for proper root development",
                soil_types=["loamy", "sandy loam", "clay loam"]
            ),
            weather_requirements=WeatherRequirements(
                temp_min=32, temp_max=85,
                temp_optimal_min=60, temp_optimal_max=75,
                rainfall_min=25, rainfall_max=40,
                humidity_range="Moderate humidity with good air circulation",
                sunlight_hours="6-8 hours daily",
                frost_tolerance="Cold hardy, requires chill hours",
                chill_hours="400-1000 hours below 45°F"
            ),
            care_instructions=CareInstructions(
                watering=[
                    "Deep, infrequent watering",
                    "1-2 inches per week during growing season",
                    "Reduce watering before harvest"
                ],
                fertilization=[
                    "Apply balanced fertilizer in early spring",
                    "Supplement with compost annually",
                    "Avoid excessive nitrogen"
                ],
                pruning=[
                    "Prune during dormant season",
                    "Remove dead, diseased, and crossing branches",
                    "Maintain open center for air circulation"
                ],
                pest_management=[
                    "Monitor for aphids and scale insects",
                    "Use integrated pest management",
                    "Encourage beneficial insects"
                ],
                harvesting="Harvest when apples are firm, fully colored, and easily separate from branch with a twist"
            ),
            diseases=apple_diseases,
            suitable_regions=["USDA Zones 3-8", "Temperate climates"],
            growing_season="Spring to Fall",
            maturity_time="2-5 years to fruit production",
            yield_info="15-50 bushels per mature tree"
        )
        
        self.plants["apple"] = apple_plant
        
        # Add apple diseases to disease database
        for disease in apple_diseases:
            self.diseases[disease.name.lower().replace(' ', '_')] = disease
    
    def get_plant(self, plant_id: str) -> Optional[PlantSpeciesData]:
        """Get plant by ID"""
        return self.plants.get(plant_id.lower())
    
    def get_plant_by_name(self, plant_name: str) -> Optional[PlantSpeciesData]:
        """Get plant by common name"""
        for plant in self.plants.values():
            if plant.common_name.lower() == plant_name.lower():
                return plant
        return None
    
    def get_disease(self, disease_id: str) -> Optional[DiseaseInfo]:
        """Get disease by ID"""
        return self.diseases.get(disease_id.lower().replace(' ', '_'))
    
    def get_all_plants(self) -> List[PlantSpeciesData]:
        """Get all plants"""
        return list(self.plants.values())
    
    def get_all_diseases(self) -> List[DiseaseInfo]:
        """Get all diseases"""
        return list(self.diseases.values())
    
    def search_plants(self, query: str) -> List[PlantSpeciesData]:
        """Search plants by name or scientific name"""
        results = []
        query_lower = query.lower()
        
        for plant in self.plants.values():
            if (query_lower in plant.common_name.lower() or 
                query_lower in plant.scientific_name.lower()):
                results.append(plant)
        
        return results
    
    def get_plants_by_category(self, category: PlantCategory) -> List[PlantSpeciesData]:
        """Get plants by category"""
        return [plant for plant in self.plants.values() if plant.category == category]
    
    def save_to_file(self, file_path: str = None):
        """Save plant database to JSON file"""
        file_path = file_path or self.data_file
        
        data = {
            'plants': {
                plant_id: plant.to_dict() 
                for plant_id, plant in self.plants.items()
            },
            'metadata': {
                'version': '1.0.0',
                'total_plants': len(self.plants),
                'total_diseases': len(self.diseases)
            }
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)