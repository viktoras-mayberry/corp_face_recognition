import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.distance import geodesic
import re
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class LocationServiceError(Exception):
    """Custom exception for location service errors"""
    pass

class LocationService:
    """Professional service for intelligent location management with geocoding and validation"""
    
    def __init__(self):
        self.geolocator = Nominatim(
            user_agent="corps_attendance_system/1.0 (NYSC Corps Attendance)",
            timeout=10
        )
        # Nigeria bounding box coordinates
        self.nigeria_bounds = {
            'north': 14.0,
            'south': 4.0,
            'east': 15.0,
            'west': 3.0
        }
        
        # Common Nigerian states and their variations
        self.nigerian_states = {
            'abia', 'adamawa', 'akwa ibom', 'anambra', 'bauchi', 'bayelsa', 'benue',
            'borno', 'cross river', 'delta', 'ebonyi', 'edo', 'ekiti', 'enugu',
            'gombe', 'imo', 'jigawa', 'kaduna', 'kano', 'katsina', 'kebbi', 'kogi',
            'kwara', 'lagos', 'nasarawa', 'niger', 'ogun', 'ondo', 'osun', 'oyo',
            'plateau', 'rivers', 'sokoto', 'taraba', 'yobe', 'zamfara', 'fct', 'abuja'
        }

    def smart_geocode(self, address: str, city: str = '', state: str = '', country: str = 'Nigeria') -> Dict[str, Any]:
        """Enhanced geocoding with Nigerian context and fallback strategies"""
        try:
            # Clean and validate inputs
            address = address.strip()
            city = city.strip()
            state = state.strip()
            
            if not address:
                return {
                    'success': False,
                    'error': 'Address is required',
                    'suggestions': []
                }
            
            # Build progressive search queries from specific to general
            search_queries = self._build_search_queries(address, city, state, country)
            
            best_result = None
            all_results = []
            
            for query in search_queries:
                try:
                    logger.info(f"Attempting geocoding with query: {query}")
                    locations = self.geolocator.geocode(query, exactly_one=False, limit=5)
                    
                    if locations:
                        for location in locations:
                            if self._is_location_in_nigeria(location):
                                result = self._format_geocode_result(location, query)
                                all_results.append(result)
                                
                                # Score the result based on relevance
                                score = self._calculate_relevance_score(result, address, city, state)
                                result['relevance_score'] = score
                                
                                if not best_result or score > best_result['relevance_score']:
                                    best_result = result
                
                except (GeocoderTimedOut, GeocoderServiceError) as e:
                    logger.warning(f"Geocoding failed for query '{query}': {str(e)}")
                    continue
            
            if best_result:
                return {
                    'success': True,
                    'latitude': best_result['latitude'],
                    'longitude': best_result['longitude'],
                    'formatted_address': best_result['formatted_address'],
                    'accuracy': best_result['accuracy'],
                    'place_type': best_result.get('place_type', 'unknown'),
                    'query_used': best_result['query'],
                    'confidence': min(best_result['relevance_score'] / 100, 1.0),
                    'alternatives': [r for r in all_results if r != best_result][:3]
                }
            else:
                # Provide helpful suggestions
                suggestions = self._generate_address_suggestions(address, city, state)
                return {
                    'success': False,
                    'error': 'Location not found. Please check the address and try again.',
                    'suggestions': suggestions
                }
                
        except Exception as e:
            logger.error(f"Unexpected error in smart geocoding: {str(e)}")
            return {
                'success': False,
                'error': 'Geocoding service error. Please try again later.',
                'suggestions': []
            }
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Enhanced reverse geocoding with validation"""
        try:
            # Validate coordinates
            if not self.validate_coordinates(latitude, longitude)['valid']:
                return {
                    'success': False,
                    'error': 'Invalid coordinates for Nigeria'
                }
            
            location = self.geolocator.reverse(f"{latitude}, {longitude}", timeout=10)
            
            if location:
                # Parse address components
                components = self._parse_address_components(location.raw.get('display_name', ''))
                
                return {
                    'success': True,
                    'address': location.address,
                    'components': components,
                    'raw': location.raw
                }
            else:
                return {
                    'success': False,
                    'error': 'No address found for these coordinates'
                }
                
        except Exception as e:
            logger.error(f"Reverse geocoding error: {str(e)}")
            return {
                'success': False,
                'error': 'Reverse geocoding service error'
            }
    
    def validate_coordinates(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Validate if coordinates are within Nigeria's boundaries"""
        try:
            lat = float(latitude)
            lng = float(longitude)
            
            # Check if coordinates are within Nigeria's bounding box
            within_bounds = (
                self.nigeria_bounds['south'] <= lat <= self.nigeria_bounds['north'] and
                self.nigeria_bounds['west'] <= lng <= self.nigeria_bounds['east']
            )
            
            if not within_bounds:
                return {
                    'valid': False,
                    'error': 'Coordinates are outside Nigeria',
                    'suggestion': 'Please verify the coordinates or use an address instead'
                }
            
            return {
                'valid': True,
                'latitude': lat,
                'longitude': lng,
                'region': self._get_region_name(lat, lng)
            }
            
        except (ValueError, TypeError) as e:
            return {
                'valid': False,
                'error': 'Invalid coordinate format',
                'suggestion': 'Coordinates must be valid numbers'
            }
    
    def find_nearby_places(self, latitude: float, longitude: float, radius_km: int = 5) -> List[Dict[str, Any]]:
        """Find nearby places using geocoding service"""
        try:
            # This is a simplified implementation
            # In production, you might use Google Places API or similar
            places = []
            
            # For now, return a sample of common place types in Nigeria
            sample_places = [
                {'name': 'Local Government Secretariat', 'type': 'government', 'distance_km': 2.1},
                {'name': 'Primary Health Care Center', 'type': 'healthcare', 'distance_km': 1.5},
                {'name': 'Community School', 'type': 'education', 'distance_km': 0.8},
                {'name': 'Market Square', 'type': 'commercial', 'distance_km': 3.2}
            ]
            
            return sample_places
            
        except Exception as e:
            logger.error(f"Error finding nearby places: {str(e)}")
            return []
    
    def _build_search_queries(self, address: str, city: str, state: str, country: str) -> List[str]:
        """Build progressive search queries from specific to general"""
        queries = []
        
        # Most specific: Full address
        if city and state:
            queries.append(f"{address}, {city}, {state}, {country}")
        
        # Medium specificity: Address with state
        if state:
            queries.append(f"{address}, {state}, {country}")
        
        # Lower specificity: Address with city
        if city:
            queries.append(f"{address}, {city}, {country}")
        
        # Lowest specificity: Just address and country
        queries.append(f"{address}, {country}")
        
        # Fallback: Just the address
        queries.append(address)
        
        return queries
    
    def _is_location_in_nigeria(self, location) -> bool:
        """Enhanced check if geocoded location is within Nigeria"""
        if not location:
            return False
        
        # Check by address string
        address_lower = location.address.lower()
        if 'nigeria' in address_lower:
            return True
        
        # Check by coordinates
        if hasattr(location, 'latitude') and hasattr(location, 'longitude'):
            return self.validate_coordinates(location.latitude, location.longitude)['valid']
        
        # Check by state names
        for state in self.nigerian_states:
            if state in address_lower:
                return True
        
        return False
    
    def _format_geocode_result(self, location, query: str) -> Dict[str, Any]:
        """Format geocoding result with additional metadata"""
        # Determine accuracy based on location type
        place_type = self._extract_place_type(location.raw)
        accuracy = self._determine_accuracy(place_type, location.raw)
        
        return {
            'latitude': location.latitude,
            'longitude': location.longitude,
            'formatted_address': location.address,
            'place_type': place_type,
            'accuracy': accuracy,
            'query': query,
            'raw': location.raw
        }
    
    def _calculate_relevance_score(self, result: Dict[str, Any], address: str, city: str, state: str) -> float:
        """Calculate relevance score for a geocoding result"""
        score = 50.0  # Base score
        
        address_lower = result['formatted_address'].lower()
        
        # Boost score if original terms are found
        if address.lower() in address_lower:
            score += 30
        if city and city.lower() in address_lower:
            score += 15
        if state and state.lower() in address_lower:
            score += 20
        
        # Boost based on place type accuracy
        accuracy_boost = {
            'high': 25,
            'medium': 15,
            'low': 5
        }
        score += accuracy_boost.get(result['accuracy'], 0)
        
        return min(score, 100.0)
    
    def _extract_place_type(self, raw_data: Dict) -> str:
        """Extract place type from raw geocoding data"""
        if not raw_data:
            return 'unknown'
        
        place_type = raw_data.get('type', '').lower()
        category = raw_data.get('category', '').lower()
        
        # Map common types
        type_mapping = {
            'house': 'residential',
            'building': 'building',
            'road': 'street',
            'administrative': 'administrative',
            'place': 'locality'
        }
        
        return type_mapping.get(place_type, place_type or category or 'unknown')
    
    def _determine_accuracy(self, place_type: str, raw_data: Dict) -> str:
        """Determine accuracy level based on place type and raw data"""
        # High accuracy for specific addresses
        if place_type in ['residential', 'building', 'house']:
            return 'high'
        
        # Medium accuracy for streets and localities
        if place_type in ['street', 'locality', 'administrative']:
            return 'medium'
        
        # Low accuracy for general areas
        return 'low'
    
    def _parse_address_components(self, address: str) -> Dict[str, str]:
        """Parse address into components"""
        components = {
            'street': '',
            'locality': '',
            'state': '',
            'country': ''
        }
        
        if not address:
            return components
        
        parts = [part.strip() for part in address.split(',')]
        
        # Simple parsing logic (can be enhanced)
        if len(parts) >= 1:
            components['street'] = parts[0]
        if len(parts) >= 2:
            components['locality'] = parts[1]
        if len(parts) >= 3:
            components['state'] = parts[-2] if 'Nigeria' not in parts[-2] else parts[-3]
        if len(parts) >= 1:
            components['country'] = 'Nigeria' if 'nigeria' in address.lower() else parts[-1]
        
        return components
    
    def _get_region_name(self, latitude: float, longitude: float) -> str:
        """Get region name based on coordinates (simplified)"""
        # This is a simplified implementation
        # In production, you might use more sophisticated geospatial data
        
        if latitude > 10:
            return 'Northern Nigeria'
        elif latitude > 7:
            return 'Middle Belt'
        else:
            return 'Southern Nigeria'
    
    def _generate_address_suggestions(self, address: str, city: str, state: str) -> List[str]:
        """Generate helpful address suggestions"""
        suggestions = []
        
        if not city:
            suggestions.append('Try including the city or local government area')
        
        if not state:
            suggestions.append('Try including the state name')
        
        suggestions.extend([
            'Check the spelling of street names and landmarks',
            'Use well-known landmarks or institutions as reference points',
            'Try using the local government area instead of city name'
        ])
        
        return suggestions
