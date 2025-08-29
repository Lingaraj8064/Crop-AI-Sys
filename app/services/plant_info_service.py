"""
Crop Disease Detection System - Plant Information Service
Service for managing plant and disease information
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

from app.models.plant_database import PlantDatabase, PlantSpeciesData, DiseaseInfo, PlantCategory, SeverityLevel
from app.models.database import AnalysisResult
from app import db

class PlantInfoService:
    """Service class for plant and disease information management"""
    
    def __init__(self):
        """Initialize the plant information service"""
        self.plant_db = PlantDatabase()
        self.cache = {}  # Simple in-memory cache
        self.cache_timeout = 3600  # 1 hour
    
    def get_plant_info(self, plant_id: str, include_stats: bool = False) -> Dict:
        """
        Get comprehensive plant information
        
        Args:
            plant_id: Plant identifier
            include_stats: Whether to include analysis statistics
            
        Returns:
            Dictionary with plant information
        """
        try:
            # Check cache first
            cache_key = f"plant_{plant_id}_{include_stats}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            plant = self.plant_db.get_plant(plant_id)
            if not plant:
                return {
                    'success': False,
                    'error': f'Plant not found: {plant_id}',
                    'code': 'PLANT_NOT_FOUND'
                }
            
            # Get basic plant information
            plant_info = plant.to_dict()
            
            # Add analysis statistics if requested
            if include_stats:
                stats = self._get_plant_statistics(plant.common_name)
                plant_info['statistics'] = stats
            
            # Add additional computed information
            plant_info['computed_info'] = self._compute_additional_info(plant)
            
            result = {
                'success': True,
                'data': plant_info
            }
            
            # Cache the result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logging.error(f"Error getting plant info for {plant_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to retrieve plant information',
                'code': 'RETRIEVAL_ERROR'
            }
    
    def get_disease_info(self, disease_id: str, include_stats: bool = False) -> Dict:
        """
        Get comprehensive disease information
        
        Args:
            disease_id: Disease identifier
            include_stats: Whether to include detection statistics
            
        Returns:
            Dictionary with disease information
        """
        try:
            cache_key = f"disease_{disease_id}_{include_stats}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            disease = self.plant_db.get_disease(disease_id)
            if not disease:
                return {
                    'success': False,
                    'error': f'Disease not found: {disease_id}',
                    'code': 'DISEASE_NOT_FOUND'
                }
            
            disease_info = disease.to_dict()
            
            # Add detection statistics if requested
            if include_stats:
                stats = self._get_disease_statistics(disease.name)
                disease_info['statistics'] = stats
            
            # Add related information
            disease_info['related_info'] = self._get_related_disease_info(disease)
            
            result = {
                'success': True,
                'data': disease_info
            }
            
            self._cache_result(cache_key, result)
            return result
            
        except Exception as e:
            logging.error(f"Error getting disease info for {disease_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to retrieve disease information',
                'code': 'RETRIEVAL_ERROR'
            }
    
    def search_plants(self, query: str, filters: Dict = None) -> Dict:
        """
        Search plants with filters
        
        Args:
            query: Search query string
            filters: Additional filters (category, region, etc.)
            
        Returns:
            Dictionary with search results
        """
        try:
            filters = filters or {}
            
            # Get all plants
            all_plants = self.plant_db.get_all_plants()
            results = []
            
            query_lower = query.lower().strip()
            
            # Apply text search
            for plant in all_plants:
                relevance_score = 0
                
                # Check common name
                if query_lower in plant.common_name.lower():
                    relevance_score += 10
                
                # Check scientific name
                if query_lower in plant.scientific_name.lower():
                    relevance_score += 8
                
                # Check family
                if query_lower in plant.family.lower():
                    relevance_score += 5
                
                # Check disease names
                for disease in plant.diseases:
                    if query_lower in disease.name.lower():
                        relevance_score += 3
                
                # Check care instructions
                care_text = json.dumps(plant.care_instructions.to_dict()).lower()
                if query_lower in care_text:
                    relevance_score += 1
                
                if relevance_score > 0:
                    plant_dict = plant.to_dict()
                    plant_dict['relevance_score'] = relevance_score
                    results.append(plant_dict)
            
            # Apply filters
            filtered_results = self._apply_plant_filters(results, filters)
            
            # Sort by relevance
            filtered_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return {
                'success': True,
                'data': {
                    'query': query,
                    'filters': filters,
                    'total_results': len(filtered_results),
                    'results': filtered_results
                }
            }
            
        except Exception as e:
            logging.error(f"Error searching plants: {e}")
            return {
                'success': False,
                'error': 'Search failed',
                'code': 'SEARCH_ERROR'
            }
    
    def search_diseases(self, query: str, filters: Dict = None) -> Dict:
        """
        Search diseases with filters
        
        Args:
            query: Search query string
            filters: Additional filters (severity, type, etc.)
            
        Returns:
            Dictionary with search results
        """
        try:
            filters = filters or {}
            
            all_diseases = self.plant_db.get_all_diseases()
            results = []
            
            query_lower = query.lower().strip()
            
            for disease in all_diseases:
                relevance_score = 0
                
                # Check disease name
                if query_lower in disease.name.lower():
                    relevance_score += 10
                
                # Check scientific name
                if disease.scientific_name and query_lower in disease.scientific_name.lower():
                    relevance_score += 8
                
                # Check symptoms
                if query_lower in disease.symptoms.lower():
                    relevance_score += 5
                
                # Check causes
                if query_lower in disease.causes.lower():
                    relevance_score += 3
                
                if relevance_score > 0:
                    disease_dict = disease.to_dict()
                    disease_dict['relevance_score'] = relevance_score
                    results.append(disease_dict)
            
            # Apply filters
            filtered_results = self._apply_disease_filters(results, filters)
            
            # Sort by relevance
            filtered_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return {
                'success': True,
                'data': {
                    'query': query,
                    'filters': filters,
                    'total_results': len(filtered_results),
                    'results': filtered_results
                }
            }
            
        except Exception as e:
            logging.error(f"Error searching diseases: {e}")
            return {
                'success': False,
                'error': 'Disease search failed',
                'code': 'SEARCH_ERROR'
            }
    
    def get_plant_recommendations(self, conditions: Dict) -> Dict:
        """
        Get plant recommendations based on growing conditions
        
        Args:
            conditions: Dictionary with soil, climate, and other conditions
            
        Returns:
            Dictionary with recommended plants
        """
        try:
            all_plants = self.plant_db.get_all_plants()
            recommendations = []
            
            for plant in all_plants:
                suitability_score = self._calculate_suitability_score(plant, conditions)
                
                if suitability_score > 0.5:  # Only include suitable plants
                    plant_dict = plant.to_dict()
                    plant_dict['suitability_score'] = round(suitability_score, 2)
                    plant_dict['suitability_reasons'] = self._get_suitability_reasons(plant, conditions)
                    recommendations.append(plant_dict)
            
            # Sort by suitability score
            recommendations.sort(key=lambda x: x['suitability_score'], reverse=True)
            
            return {
                'success': True,
                'data': {
                    'conditions': conditions,
                    'total_recommendations': len(recommendations),
                    'recommendations': recommendations[:10]  # Top 10 recommendations
                }
            }
            
        except Exception as e:
            logging.error(f"Error getting plant recommendations: {e}")
            return {
                'success': False,
                'error': 'Failed to generate recommendations',
                'code': 'RECOMMENDATION_ERROR'
            }
    
    def get_disease_risk_assessment(self, plant_id: str, conditions: Dict) -> Dict:
        """
        Assess disease risk for a plant under given conditions
        
        Args:
            plant_id: Plant identifier
            conditions: Environmental conditions
            
        Returns:
            Dictionary with risk assessment
        """
        try:
            plant = self.plant_db.get_plant(plant_id)
            if not plant:
                return {
                    'success': False,
                    'error': 'Plant not found',
                    'code': 'PLANT_NOT_FOUND'
                }
            
            risk_assessments = []
            
            for disease in plant.diseases:
                risk_level = self._calculate_disease_risk(disease, conditions)
                
                risk_assessments.append({
                    'disease_name': disease.name,
                    'risk_level': risk_level['level'],
                    'risk_score': risk_level['score'],
                    'risk_factors': risk_level['factors'],
                    'prevention_priority': risk_level['prevention_priority']
                })
            
            # Sort by risk score
            risk_assessments.sort(key=lambda x: x['risk_score'], reverse=True)
            
            return {
                'success': True,
                'data': {
                    'plant_name': plant.common_name,
                    'conditions': conditions,
                    'overall_risk': self._calculate_overall_risk(risk_assessments),
                    'disease_risks': risk_assessments,
                    'recommendations': self._generate_risk_recommendations(risk_assessments)
                }
            }
            
        except Exception as e:
            logging.error(f"Error assessing disease risk: {e}")
            return {
                'success': False,
                'error': 'Risk assessment failed',
                'code': 'RISK_ASSESSMENT_ERROR'
            }
    
    def get_seasonal_care_guide(self, plant_id: str, season: str = None) -> Dict:
        """
        Get seasonal care guide for a plant
        
        Args:
            plant_id: Plant identifier
            season: Specific season (spring, summer, fall, winter)
            
        Returns:
            Dictionary with seasonal care instructions
        """
        try:
            plant = self.plant_db.get_plant(plant_id)
            if not plant:
                return {
                    'success': False,
                    'error': 'Plant not found',
                    'code': 'PLANT_NOT_FOUND'
                }
            
            # Get current season if not specified
            if not season:
                season = self._get_current_season()
            
            care_guide = {
                'plant_name': plant.common_name,
                'season': season.title(),
                'general_care': plant.care_instructions.to_dict(),
                'seasonal_specific': self._get_seasonal_care_tasks(plant, season),
                'disease_prevention': self._get_seasonal_disease_prevention(plant, season),
                'optimal_conditions': self._get_seasonal_conditions(plant, season)
            }
            
            return {
                'success': True,
                'data': care_guide
            }
            
        except Exception as e:
            logging.error(f"Error getting seasonal care guide: {e}")
            return {
                'success': False,
                'error': 'Failed to generate care guide',
                'code': 'CARE_GUIDE_ERROR'
            }
    
    def _get_plant_statistics(self, plant_name: str) -> Dict:
        """Get analysis statistics for a plant"""
        try:
            # Total analyses
            total_analyses = AnalysisResult.query.filter(
                AnalysisResult.plant_name == plant_name
            ).count()
            
            # Healthy vs diseased
            healthy_count = AnalysisResult.query.filter(
                AnalysisResult.plant_name == plant_name,
                AnalysisResult.is_healthy == True
            ).count()
            
            # Disease distribution
            disease_stats = db.session.query(
                AnalysisResult.disease_name,
                db.func.count(AnalysisResult.disease_name).label('count')
            ).filter(
                AnalysisResult.plant_name == plant_name,
                AnalysisResult.disease_name.isnot(None)
            ).group_by(AnalysisResult.disease_name).all()
            
            # Average confidence
            avg_confidence = db.session.query(
                db.func.avg(AnalysisResult.confidence)
            ).filter(
                AnalysisResult.plant_name == plant_name
            ).scalar() or 0
            
            return {
                'total_analyses': total_analyses,
                'healthy_count': healthy_count,
                'diseased_count': total_analyses - healthy_count,
                'health_percentage': round((healthy_count / total_analyses * 100), 1) if total_analyses > 0 else 0,
                'disease_distribution': [
                    {'disease': disease, 'count': count}
                    for disease, count in disease_stats
                ],
                'average_confidence': round(avg_confidence, 1)
            }
            
        except Exception as e:
            logging.error(f"Error getting plant statistics: {e}")
            return {}
    
    def _get_disease_statistics(self, disease_name: str) -> Dict:
        """Get detection statistics for a disease"""
        try:
            # Total detections
            total_detections = AnalysisResult.query.filter(
                AnalysisResult.disease_name == disease_name
            ).count()
            
            # Affected plants
            affected_plants = db.session.query(
                AnalysisResult.plant_name,
                db.func.count(AnalysisResult.plant_name).label('count')
            ).filter(
                AnalysisResult.disease_name == disease_name
            ).group_by(AnalysisResult.plant_name).all()
            
            # Confidence distribution
            confidence_stats = db.session.query(
                db.func.avg(AnalysisResult.confidence).label('avg'),
                db.func.min(AnalysisResult.confidence).label('min'),
                db.func.max(AnalysisResult.confidence).label('max')
            ).filter(
                AnalysisResult.disease_name == disease_name
            ).first()
            
            return {
                'total_detections': total_detections,
                'affected_plants': [
                    {'plant': plant, 'detections': count}
                    for plant, count in affected_plants
                ],
                'confidence_stats': {
                    'average': round(confidence_stats.avg or 0, 1),
                    'minimum': round(confidence_stats.min or 0, 1),
                    'maximum': round(confidence_stats.max or 0, 1)
                } if confidence_stats else {}
            }
            
        except Exception as e:
            logging.error(f"Error getting disease statistics: {e}")
            return {}
    
    def _compute_additional_info(self, plant: PlantSpeciesData) -> Dict:
        """Compute additional information about a plant"""
        return {
            'disease_count': len(plant.diseases),
            'severity_distribution': self._get_severity_distribution(plant.diseases),
            'growing_difficulty': self._assess_growing_difficulty(plant),
            'care_frequency': self._assess_care_frequency(plant),
            'companion_compatibility': len(plant.companion_plants),
            'seasonal_requirements': self._get_seasonal_requirements_summary(plant)
        }
    
    def _get_related_disease_info(self, disease: DiseaseInfo) -> Dict:
        """Get related information for a disease"""
        return {
            'severity_category': disease.severity.value,
            'treatment_complexity': self._assess_treatment_complexity(disease),
            'prevention_difficulty': self._assess_prevention_difficulty(disease),
            'organic_options_available': len(disease.organic_treatment) > 0,
            'contagiousness': disease.contagious_level,
            'affected_plant_parts': disease.affected_parts
        }
    
    def _apply_plant_filters(self, plants: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to plant search results"""
        filtered = plants
        
        if filters.get('category'):
            filtered = [p for p in filtered if p['category'].lower() == filters['category'].lower()]
        
        if filters.get('region'):
            region_filter = filters['region'].lower()
            filtered = [p for p in filtered 
                       if any(region_filter in region.lower() for region in p.get('suitable_regions', []))]
        
        if filters.get('difficulty'):
            # This would require implementing difficulty assessment
            pass
        
        return filtered
    
    def _apply_disease_filters(self, diseases: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to disease search results"""
        filtered = diseases
        
        if filters.get('severity'):
            filtered = [d for d in filtered if d['severity'].lower() == filters['severity'].lower()]
        
        if filters.get('type'):
            filtered = [d for d in filtered if d['type'].lower() == filters['type'].lower()]
        
        return filtered
    
    def _calculate_suitability_score(self, plant: PlantSpeciesData, conditions: Dict) -> float:
        """Calculate how suitable a plant is for given conditions"""
        score = 0.0
        factors = 0
        
        # Soil pH compatibility
        if 'soil_ph' in conditions:
            soil_ph = conditions['soil_ph']
            if plant.soil_requirements.ph_min <= soil_ph <= plant.soil_requirements.ph_max:
                score += 1.0
            else:
                # Partial score based on how close it is
                ph_mid = (plant.soil_requirements.ph_min + plant.soil_requirements.ph_max) / 2
                deviation = abs(soil_ph - ph_mid)
                score += max(0, 1 - deviation / 2)  # Decrease score with deviation
            factors += 1
        
        # Temperature compatibility
        if 'temperature' in conditions:
            temp = conditions['temperature']
            if plant.weather_requirements.temp_min <= temp <= plant.weather_requirements.temp_max:
                score += 1.0
            factors += 1
        
        # Region compatibility
        if 'region' in conditions:
            user_region = conditions['region'].lower()
            if any(user_region in region.lower() for region in plant.suitable_regions):
                score += 1.0
            factors += 1
        
        return score / factors if factors > 0 else 0.0
    
    def _get_suitability_reasons(self, plant: PlantSpeciesData, conditions: Dict) -> List[str]:
        """Get reasons why a plant is suitable for given conditions"""
        reasons = []
        
        if 'soil_ph' in conditions:
            soil_ph = conditions['soil_ph']
            if plant.soil_requirements.ph_min <= soil_ph <= plant.soil_requirements.ph_max:
                reasons.append(f"Soil pH {soil_ph} is within optimal range")
        
        if 'temperature' in conditions:
            temp = conditions['temperature']
            if plant.weather_requirements.temp_min <= temp <= plant.weather_requirements.temp_max:
                reasons.append(f"Temperature {temp}°F is suitable")
        
        return reasons
    
    def _calculate_disease_risk(self, disease: DiseaseInfo, conditions: Dict) -> Dict:
        """Calculate disease risk under given conditions"""
        risk_score = 0.0
        risk_factors = []
        
        # Parse favorable conditions if available
        if disease.favorable_conditions:
            favorable = disease.favorable_conditions.lower()
            
            # Check temperature conditions
            if 'temperature' in conditions:
                temp = conditions['temperature']
                if 'cool' in favorable and temp < 65:
                    risk_score += 0.3
                    risk_factors.append("Cool temperature favors this disease")
                elif 'warm' in favorable and temp > 75:
                    risk_score += 0.3
                    risk_factors.append("Warm temperature favors this disease")
            
            # Check humidity conditions
            if 'humidity' in conditions:
                humidity = conditions['humidity']
                if 'humid' in favorable and humidity > 70:
                    risk_score += 0.4
                    risk_factors.append("High humidity increases disease risk")
                elif 'moist' in favorable and humidity > 60:
                    risk_score += 0.3
                    risk_factors.append("Moist conditions favor disease development")
        
        # Base risk based on severity
        severity_risk = {
            'Low': 0.1,
            'Medium': 0.3,
            'High': 0.5,
            'Critical': 0.7
        }
        
        base_risk = severity_risk.get(disease.severity.value, 0.3)
        total_risk = min(base_risk + risk_score, 1.0)
        
        # Determine risk level
        if total_risk >= 0.7:
            level = "High"
            prevention_priority = "High"
        elif total_risk >= 0.4:
            level = "Medium"
            prevention_priority = "Medium"
        else:
            level = "Low"
            prevention_priority = "Low"
        
        return {
            'score': round(total_risk, 2),
            'level': level,
            'factors': risk_factors,
            'prevention_priority': prevention_priority
        }
    
    def _calculate_overall_risk(self, risk_assessments: List[Dict]) -> Dict:
        """Calculate overall disease risk from individual assessments"""
        if not risk_assessments:
            return {'level': 'Low', 'score': 0.0}
        
        # Calculate weighted average (higher risks weighted more)
        total_weighted_score = sum(assessment['risk_score'] ** 2 for assessment in risk_assessments)
        avg_score = total_weighted_score / len(risk_assessments)
        
        if avg_score >= 0.6:
            level = "High"
        elif avg_score >= 0.3:
            level = "Medium"  
        else:
            level = "Low"
        
        return {
            'level': level,
            'score': round(avg_score, 2),
            'high_risk_diseases': len([a for a in risk_assessments if a['risk_level'] == 'High'])
        }
    
    def _generate_risk_recommendations(self, risk_assessments: List[Dict]) -> List[str]:
        """Generate recommendations based on disease risk assessments"""
        recommendations = []
        
        high_risk_diseases = [a for a in risk_assessments if a['risk_level'] == 'High']
        medium_risk_diseases = [a for a in risk_assessments if a['risk_level'] == 'Medium']
        
        if high_risk_diseases:
            recommendations.append(f"High priority: Monitor for {', '.join(d['disease_name'] for d in high_risk_diseases[:3])}")
            recommendations.append("Implement preventive treatments immediately")
        
        if medium_risk_diseases:
            recommendations.append(f"Medium priority: Watch for signs of {', '.join(d['disease_name'] for d in medium_risk_diseases[:2])}")
        
        recommendations.append("Maintain good plant hygiene and air circulation")
        recommendations.append("Regular inspection is recommended")
        
        return recommendations[:5]
    
    def _get_seasonal_care_tasks(self, plant: PlantSpeciesData, season: str) -> List[str]:
        """Get seasonal care tasks for a plant"""
        seasonal_tasks = {
            'spring': [
                "Begin regular watering schedule",
                "Apply balanced fertilizer",
                "Prune dead or damaged parts",
                "Start pest monitoring"
            ],
            'summer': [
                "Increase watering frequency",
                "Provide shade during extreme heat",
                "Monitor for pest activity",
                "Harvest mature produce"
            ],
            'fall': [
                "Reduce watering frequency",
                "Collect and dispose of fallen leaves",
                "Prepare for dormant season",
                "Apply pre-winter treatments"
            ],
            'winter': [
                "Minimal watering",
                "Protect from frost",
                "Plan for next season",
                "Maintain tools and equipment"
            ]
        }
        
        base_tasks = seasonal_tasks.get(season.lower(), [])
        
        # Add plant-specific tasks based on care instructions
        if hasattr(plant.care_instructions, 'seasonal_care'):
            plant_specific = plant.care_instructions.seasonal_care.get(season.lower(), [])
            base_tasks.extend(plant_specific)
        
        return base_tasks
    
    def _get_seasonal_disease_prevention(self, plant: PlantSpeciesData, season: str) -> List[str]:
        """Get seasonal disease prevention measures"""
        prevention_measures = []
        
        for disease in plant.diseases:
            # Add seasonal prevention based on disease characteristics
            if season.lower() == 'spring' and disease.disease_type == 'fungal':
                prevention_measures.append(f"Apply preventive fungicide for {disease.name}")
            elif season.lower() == 'summer' and 'humid' in disease.favorable_conditions.lower():
                prevention_measures.append(f"Ensure good air circulation to prevent {disease.name}")
        
        return list(set(prevention_measures))  # Remove duplicates
    
    def _get_seasonal_conditions(self, plant: PlantSpeciesData, season: str) -> Dict:
        """Get optimal seasonal conditions for a plant"""
        base_conditions = plant.weather_requirements.to_dict()
        
        # Adjust conditions based on season
        seasonal_adjustments = {
            'spring': {'watering': 'Regular', 'fertilizing': 'Begin fertilization'},
            'summer': {'watering': 'Frequent', 'protection': 'Shade during peak hours'},
            'fall': {'watering': 'Reduced', 'preparation': 'Prepare for dormancy'},
            'winter': {'watering': 'Minimal', 'protection': 'Frost protection'}
        }
        
        conditions = base_conditions.copy()
        conditions.update(seasonal_adjustments.get(season.lower(), {}))
        
        return conditions
    
    def _get_current_season(self) -> str:
        """Determine current season based on date"""
        month = datetime.now().month
        
        if 3 <= month <= 5:
            return 'spring'
        elif 6 <= month <= 8:
            return 'summer'
        elif 9 <= month <= 11:
            return 'fall'
        else:
            return 'winter'
    
    def _get_severity_distribution(self, diseases: List[DiseaseInfo]) -> Dict:
        """Get distribution of disease severities"""
        severity_counts = {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
        
        for disease in diseases:
            severity_counts[disease.severity.value] += 1
        
        return severity_counts
    
    def _assess_growing_difficulty(self, plant: PlantSpeciesData) -> str:
        """Assess the difficulty of growing a plant"""
        difficulty_score = 0
        
        # Soil requirements complexity
        soil_req = plant.soil_requirements
        if soil_req.ph_max - soil_req.ph_min < 1.0:  # Narrow pH range
            difficulty_score += 1
        
        # Weather requirements complexity
        weather_req = plant.weather_requirements
        if weather_req.temp_max - weather_req.temp_min < 20:  # Narrow temperature range
            difficulty_score += 1
        
        # Disease susceptibility
        if len(plant.diseases) > 3:
            difficulty_score += 1
        
        # Care requirements complexity
        care = plant.care_instructions
        if len(care.pruning) > 3 or len(care.fertilization) > 3:
            difficulty_score += 1
        
        if difficulty_score >= 3:
            return "Hard"
        elif difficulty_score >= 2:
            return "Medium"
        else:
            return "Easy"
    
    def _assess_care_frequency(self, plant: PlantSpeciesData) -> str:
        """Assess how frequently a plant needs care"""
        # This is a simplified assessment
        care_tasks = (
            len(plant.care_instructions.watering) +
            len(plant.care_instructions.fertilization) +
            len(plant.care_instructions.pruning) +
            len(plant.care_instructions.pest_management)
        )
        
        if care_tasks > 12:
            return "High"
        elif care_tasks > 8:
            return "Medium"
        else:
            return "Low"
    
    def _get_seasonal_requirements_summary(self, plant: PlantSpeciesData) -> Dict:
        """Get summary of seasonal requirements"""
        return {
            'growing_season': plant.growing_season,
            'frost_tolerance': plant.weather_requirements.frost_tolerance,
            'seasonal_care_available': bool(getattr(plant.care_instructions, 'seasonal_care', {}))
        }
    
    def _assess_treatment_complexity(self, disease: DiseaseInfo) -> str:
        """Assess complexity of disease treatment"""
        treatment_steps = len(disease.treatment)
        
        if treatment_steps > 4:
            return "Complex"
        elif treatment_steps > 2:
            return "Moderate"
        else:
            return "Simple"
    
    def _assess_prevention_difficulty(self, disease: DiseaseInfo) -> str:
        """Assess difficulty of disease prevention"""
        prevention_steps = len(disease.prevention)
        
        if prevention_steps > 4 or disease.contagious_level == "High":
            return "Difficult"
        elif prevention_steps > 2:
            return "Moderate"
        else:
            return "Easy"
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get result from cache if valid"""
        if key in self.cache:
            cached_item = self.cache[key]
            if (datetime.now() - cached_item['timestamp']).seconds < self.cache_timeout:
                return cached_item['data']
            else:
                # Remove expired item
                del self.cache[key]
        return None
    
    def _cache_result(self, key: str, result: Dict):
        """Cache result with timestamp"""
        self.cache[key] = {
            'data': result,
            'timestamp': datetime.now()
        }
        
        # Simple cache size management
        if len(self.cache) > 100:
            # Remove oldest entries
            oldest_keys = sorted(self.cache.keys(), 
                               key=lambda k: self.cache[k]['timestamp'])[:20]
            for old_key in oldest_keys:
                del self.cache[old_key]