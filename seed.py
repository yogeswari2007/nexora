#!/usr/bin/env python3
"""
NEXORA - Next-generation hotel discovery and booking
Seeder: builds hotels.db (SQLite) with 50 accessibility-rich hotels across India.
"""
import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotels.db")

# ---------------------------------------------------------------------------
# Per-city context: famous places, nearby hospitals, restaurants, transport
# ---------------------------------------------------------------------------
CITY = {
    "New Delhi": {
        "state": "Delhi", "region": "North",
        "lat": 28.6139, "lon": 77.2090,
        "places": [("India Gate", 1.5, "Monument"), ("Red Fort", 6.5, "Monument"),
                   ("Qutub Minar", 13.0, "Monument"), ("Humayun's Tomb", 6.0, "Monument"),
                   ("Connaught Place", 2.5, "Shopping")],
        "hospitals": [("AIIMS Hospital", 3.2), ("Apollo Hospital", 4.1)],
        "restaurants": [("Bukhara", 2.0, "North Indian", "High"), ("Karim's", 7.0, "Mughlai", "Mid")],
        "transport": [("Indira Gandhi Intl Airport", 14.0), ("New Delhi Railway Station", 2.4), ("Rajiv Chowk Metro", 1.0)],
    },
    "Mumbai": {
        "state": "Maharashtra", "region": "West",
        "lat": 19.0760, "lon": 72.8777,
        "places": [("Gateway of India", 2.0, "Monument"), ("Marine Drive", 3.0, "Waterfront"),
                   ("Juhu Beach", 12.0, "Beach"), ("Elephanta Caves", 9.0, "Heritage"),
                   ("Colaba Causeway", 2.5, "Shopping")],
        "hospitals": [("Lilavati Hospital", 4.0), ("Reliance Foundation", 5.0)],
        "restaurants": [("Trishna", 3.0, "Seafood", "High"), ("Cafe Mondegar", 2.5, "Cafe", "Mid")],
        "transport": [("Chhatrapati Shivaji Intl Airport", 4.2), ("Mumbai CSMT", 3.0), ("Churchgate Station", 3.2)],
    },
    "Bengaluru": {
        "state": "Karnataka", "region": "South",
        "lat": 12.9716, "lon": 77.5946,
        "places": [("Lalbagh Botanical Garden", 4.0, "Garden"), ("Cubbon Park", 3.0, "Garden"),
                   ("Vidhana Soudha", 3.5, "Landmark"), ("Bannerghatta National Park", 22.0, "Nature"),
                   ("MG Road", 1.5, "Shopping")],
        "hospitals": [("Manipal Hospital", 3.5), ("Apollo Clinic", 2.0)],
        "restaurants": [("Truffles", 2.5, "Continental", "Mid"), ("MTR", 4.5, "South Indian", "Mid")],
        "transport": [("Kempegowda Intl Airport", 35.0), ("KSR Railway Station", 3.0), ("MG Road Metro", 1.2)],
    },
    "Hyderabad": {
        "state": "Telangana", "region": "South",
        "lat": 17.3850, "lon": 78.4867,
        "places": [("Charminar", 5.0, "Monument"), ("Golconda Fort", 12.0, "Fort"),
                   ("Hussain Sagar Lake", 4.0, "Lake"), ("Ramoji Film City", 34.0, "Entertainment"),
                   ("Banjara Hills", 8.0, "Shopping")],
        "hospitals": [("Apollo Hospitals", 6.0), ("Yashoda Hospital", 5.0)],
        "restaurants": [("Paradise Biryani", 6.0, "Hyderabadi", "Mid"), ("Bawarchi", 7.0, "Biryani", "Mid")],
        "transport": [("Rajiv Gandhi Intl Airport", 30.0), ("Secunderabad Station", 6.0), ("Metro Ameerpet", 3.0)],
    },
    "Chennai": {
        "state": "Tamil Nadu", "region": "South",
        "lat": 13.0827, "lon": 80.2707,
        "places": [("Marina Beach", 4.0, "Beach"), ("Kapaleeshwarar Temple", 3.0, "Temple"),
                   ("Fort St. George", 3.5, "Heritage"), ("Mahabalipuram", 55.0, "Heritage"),
                   ("Pondy Bazaar", 2.0, "Shopping")],
        "hospitals": [("Apollo Main Hospital", 5.0), ("Fortis Malar", 4.0)],
        "restaurants": [("Dakshin", 3.0, "South Indian", "High"), ("Murugan Idli", 4.0, "South Indian", "Low")],
        "transport": [("Chennai Intl Airport", 12.0), ("Chennai Central", 5.0), ("Marina Beach Metro", 2.0)],
    },
    "Kolkata": {
        "state": "West Bengal", "region": "East",
        "lat": 22.5726, "lon": 88.3639,
        "places": [("Victoria Memorial", 2.5, "Museum"), ("Howrah Bridge", 5.0, "Landmark"),
                   ("Dakshineswar Temple", 20.0, "Temple"), ("Park Street", 1.5, "Nightlife"),
                   ("Princep Ghat", 4.0, "Waterfront")],
        "hospitals": [("SSKM Hospital", 3.0), ("Fortis Kolkata", 6.0)],
        "restaurants": [("Bhojohori Manna", 2.0, "Bengali", "Mid"), ("Flurys", 1.5, "Cafe", "Mid")],
        "transport": [("Netaji Subhas Intl Airport", 17.0), ("Howrah Station", 5.5), ("Esplanade Metro", 2.0)],
    },
    "Jaipur": {
        "state": "Rajasthan", "region": "North",
        "lat": 26.9124, "lon": 75.7873,
        "places": [("Hawa Mahal", 1.0, "Monument"), ("Amber Fort", 11.0, "Fort"),
                   ("City Palace", 1.5, "Palace"), ("Jantar Mantar", 1.2, "Heritage"),
                   ("Johari Bazaar", 1.0, "Shopping")],
        "hospitals": [("SMS Hospital", 4.0), ("Fortis Escorts", 6.0)],
        "restaurants": [("Chokhi Dhani", 20.0, "Rajasthani", "High"), ("LMB", 1.5, "Rajasthani", "Mid")],
        "transport": [("Jaipur Intl Airport", 12.0), ("Jaipur Junction", 3.0), ("C Scheme Bus Stand", 1.0)],
    },
    "Agra": {
        "state": "Uttar Pradesh", "region": "North",
        "lat": 27.1767, "lon": 78.0081,
        "places": [("Taj Mahal", 2.0, "Monument"), ("Agra Fort", 4.0, "Fort"),
                   ("Mehtab Bagh", 5.0, "Garden"), ("Fatehpur Sikri", 40.0, "Heritage"),
                   ("Sadar Bazaar", 2.0, "Shopping")],
        "hospitals": [("SN Medical College", 3.0), ("Amar Ujala Hospital", 2.0)],
        "restaurants": [("Pinch of Spice", 3.0, "Multi-cuisine", "Mid"), ("Joney's Place", 1.8, "Cafe", "Low")],
        "transport": [("Agra Airport", 7.0), ("Agra Cantt Station", 5.0), ("Shahjahan Gardens Bus", 3.0)],
    },
    "Goa": {
        "state": "Goa", "region": "West",
        "lat": 15.2993, "lon": 74.1240,
        "places": [("Baga Beach", 2.0, "Beach"), ("Fort Aguada", 8.0, "Fort"),
                   ("Calangute Beach", 1.5, "Beach"), ("Dudhsagar Falls", 50.0, "Nature"),
                   ("Anjuna Flea Market", 5.0, "Shopping")],
        "hospitals": [("SMS Hospital", 4.0), ("Manipal Hospital Goa", 5.0)],
        "restaurants": [("Britto's", 2.5, "Seafood", "High"), ("Beatles Cafe", 6.0, "Continental", "Mid")],
        "transport": [("Goa Airport (Dabolim)", 38.0), ("Madgaon Junction", 22.0), ("Panjim Bus Stand", 12.0)],
    },
    "Udaipur": {
        "state": "Rajasthan", "region": "North",
        "lat": 24.5854, "lon": 73.7125,
        "places": [("City Palace", 1.0, "Palace"), ("Lake Pichola", 1.0, "Lake"),
                   ("Jag Mandir", 1.5, "Island"), ("Fateh Sagar Lake", 3.0, "Lake"),
                   ("Saheliyon-ki-Bari", 3.0, "Garden")],
        "hospitals": [("MB Hospital", 2.0), ("Suhas Hospital", 4.0)],
        "restaurants": [("Ambrai", 1.5, "Rajsthani", "High"), ("Cafe Natraj", 2.0, "Cafe", "Mid")],
        "transport": [("Maharana Pratap Airport", 25.0), ("Udaipur City Station", 2.0), ("Chetak Circle Bus", 1.0)],
    },
    "Varanasi": {
        "state": "Uttar Pradesh", "region": "North",
        "lat": 25.3176, "lon": 82.9739,
        "places": [("Kashi Vishwanath Temple", 1.0, "Temple"), ("Dashashwamedh Ghat", 1.0, "Ghat"),
                   ("Sarnath", 10.0, "Heritage"), ("Assi Ghat", 3.0, "Ghat"),
                   ("Tulsi Ghat", 2.0, "Ghat")],
        "hospitals": [("BHU Hospital", 6.0), ("Heritage Hospital", 2.0)],
        "restaurants": [("Kashi Chat Bhandar", 1.0, "Street Food", "Low"), ("Kesar", 1.5, "Cafe", "Mid")],
        "transport": [("Lal Bahadur Shastri Airport", 26.0), ("Varanasi Junction", 4.0), ("Cantt Bus", 3.0)],
    },
    "Kochi": {
        "state": "Kerala", "region": "South",
        "lat": 9.9312, "lon": 76.2673,
        "places": [("Fort Kochi", 1.0, "Heritage"), ("Chinese Fishing Nets", 1.2, "Landmark"),
                   ("Mattancherry Palace", 1.5, "Palace"), ("Marine Drive", 4.0, "Waterfront"),
                   ("Cherai Beach", 28.0, "Beach")],
        "hospitals": [("Amrita Hospital", 10.0), ("Medical Trust", 5.0)],
        "restaurants": [("Grand Pavilion", 2.0, "Kerala", "Mid"), ("Dhe Puttu", 3.0, "Kerala", "Mid")],
        "transport": [("Cochin Intl Airport", 28.0), ("Ernakulam Junction", 4.0), ("Fort Kochi Jetty", 1.0)],
    },
    "Amritsar": {
        "state": "Punjab", "region": "North",
        "lat": 31.6340, "lon": 74.8723,
        "places": [("Golden Temple", 1.0, "Temple"), ("Jallianwala Bagh", 1.2, "Monument"),
                   ("Wagah Border", 28.0, "Ceremony"), ("Partition Museum", 1.3, "Museum"),
                   ("Hall Bazaar", 1.5, "Shopping")],
        "hospitals": [("Sri Guru Ram Das Hospital", 3.0), ("Apollo Clinic", 2.0)],
        "restaurants": [("Kesar Da Dhaba", 2.0, "Punjabi", "Mid"), ("Bharawan Da Dhaba", 1.5, "Punjabi", "Low")],
        "transport": [("Sri Guru Ram Dass Jee Intl Airport", 11.0), ("Amritsar Junction", 2.5), ("Golden Temple Bus", 1.0)],
    },
    "Shimla": {
        "state": "Himachal Pradesh", "region": "North",
        "lat": 31.1048, "lon": 77.1734,
        "places": [("Mall Road", 0.5, "Shopping"), ("Kufri", 15.0, "Hill Station"),
                   ("Christ Church", 0.6, "Church"), ("The Ridge", 0.5, "Landmark"),
                   ("Jakhoo Temple", 2.0, "Temple")],
        "hospitals": [("Deen Dayal Upadhyay Hospital", 2.0), ("Krishna Hospital", 3.0)],
        "restaurants": [("Cafe Sol", 1.0, "Cafe", "Mid"), ("Ashiana", 1.5, "North Indian", "Mid")],
        "transport": [("Shimla Airport", 21.0), ("Shimla Railway Station", 2.0), ("Shimla ISBT", 1.0)],
    },
    "Darjeeling": {
        "state": "West Bengal", "region": "East",
        "lat": 27.0360, "lon": 88.2627,
        "places": [("Tiger Hill", 10.0, "Viewpoint"), ("Toy Train", 1.0, "Heritage"),
                   ("Batasia Loop", 5.0, "Viewpoint"), ("Happy Valley Tea Estate", 2.0, "Estate"),
                   ("Peace Pagoda", 3.0, "Temple")],
        "hospitals": [("Sadar Hospital", 2.0), ("Darjeeling Dist Hospital", 2.0)],
        "restaurants": [("Glenary's", 1.0, "Bakery", "Mid"), ("Kunga Restaurant", 1.5, "Tibetan", "Mid")],
        "transport": [("Bagdogra Airport", 90.0), ("Darjeeling Station", 1.0), ("Sherpa Bus Stand", 0.5)],
    },
    "Pune": {
        "state": "Maharashtra", "region": "West",
        "lat": 18.5204, "lon": 73.8567,
        "places": [("Sinhagad Fort", 25.0, "Fort"), ("Aga Khan Palace", 4.0, "Palace"),
                   ("Shaniwar Wada", 3.0, "Fort"), ("Dagdusheth Ganpati", 3.0, "Temple"),
                   ("Lonavala", 65.0, "Hill Station")],
        "hospitals": [("Ruby Hall Clinic", 4.0), ("Sahyadri Hospital", 6.0)],
        "restaurants": [("Dorabjee", 3.0, "Parsi", "Mid"), ("Malaka Spice", 8.0, "Thai", "High")],
        "transport": [("Pune Airport", 12.0), ("Pune Junction", 3.0), ("Pune Metro", 1.5)],
    },
    "Ahmedabad": {
        "state": "Gujarat", "region": "West",
        "lat": 23.0225, "lon": 72.5714,
        "places": [("Sabarmati Ashram", 5.0, "Heritage"), ("Kankaria Lake", 8.0, "Lake"),
                   ("Sidi Saiyyed Mosque", 4.0, "Mosque"), ("Akshardham Temple", 30.0, "Temple"),
                   ("Riverside Promenade", 3.0, "Waterfront")],
        "hospitals": [("CIMS Hospital", 7.0), ("Apollo Hospital", 9.0)],
        "restaurants": [("Agashiye", 2.0, "Gujarati", "High"), ("Gordhan Thal", 3.0, "Gujarati", "Mid")],
        "transport": [("Sardar Vallabhbhai Patel Intl Airport", 9.0), ("Ahmedabad Junction", 4.0), ("BRTS", 1.0)],
    },
    "Mysuru": {
        "state": "Karnataka", "region": "South",
        "lat": 12.2958, "lon": 76.6394,
        "places": [("Mysore Palace", 1.0, "Palace"), ("Chamundi Hill", 13.0, "Temple"),
                   ("Brindavan Gardens", 18.0, "Garden"), ("Ranganathittu Birds Sanctuary", 20.0, "Nature"),
                   ("Mysore Zoo", 2.0, "Zoo")],
        "hospitals": [("Krishna Rajendra Hospital", 2.0), ("Columbia Asia", 6.0)],
        "restaurants": [("Oyster Bay", 2.0, "Multi-cuisine", "High"), ("Mylari", 3.0, "South Indian", "Mid")],
        "transport": [("Mysuru Airport", 12.0), ("Mysuru Junction", 2.0), ("KSRTC Bus Stand", 1.0)],
    },
    "Rishikesh": {
        "state": "Uttarakhand", "region": "North",
        "lat": 30.0869, "lon": 78.2676,
        "places": [("Laxman Jhula", 2.0, "Bridge"), ("Triveni Ghat", 3.0, "Ghat"),
                   ("The Beatles Ashram", 2.5, "Heritage"), ("Neelkanth Temple", 32.0, "Temple"),
                   ("Ganga Aarti", 3.0, "Ceremony")],
        "hospitals": [("Himalayan Hospital", 4.0), ("Rishikesh Civil Hospital", 3.0)],
        "restaurants": [("The Little Buddha Cafe", 2.0, "Cafe", "Mid"), ("Cafe de Goa", 1.5, "Cafe", "Low")],
        "transport": [("Dehradun Airport", 35.0), ("Rishikesh Station", 1.5), ("Rishikesh Bus Stand", 1.0)],
    },
    "Shillong": {
        "state": "Meghalaya", "region": "East",
        "lat": 25.5788, "lon": 91.8933,
        "places": [("Umiam Lake", 18.0, "Lake"), ("Elephant Falls", 10.0, "Waterfall"),
                   ("Ward's Lake", 1.5, "Lake"), ("Shillong Peak", 10.0, "Viewpoint"),
                   ("Police Bazar", 1.0, "Shopping")],
        "hospitals": [("North Eastern Hill University Hospital", 5.0), ("Woodland Hospital", 4.0)],
        "restaurants": [("Cafe Shillong", 1.0, "Cafe", "Mid"), ("Bar B Q", 2.0, "Khasi", "Mid")],
        "transport": [("Shillong Airport (Umroi)", 35.0), ("Shillong Bus Stand", 1.0), ("Nongthymmai", 2.0)],
    },
    "Lucknow": {
        "state": "Uttar Pradesh", "region": "North",
        "lat": 26.8467, "lon": 80.9462,
        "places": [("Bara Imambara", 2.0, "Monument"), ("Rumi Darwaza", 2.0, "Gateway"),
                   ("Hazratganj", 2.5, "Shopping"), ("Chota Imambara", 2.5, "Monument"),
                   ("Ambedkar Park", 12.0, "Park")],
        "hospitals": [("SGPGI", 8.0), ("King George Hospital", 3.0)],
        "restaurants": [("Dastarkhwan", 4.0, "Awadhi", "Mid"), ("Tunday Kababi", 3.0, "Awadhi", "Low")],
        "transport": [("Chaudhary Charan Singh Intl Airport", 12.0), ("Lucknow Charbagh", 2.0), ("Alambagh", 4.0)],
    },
    "Jodhpur": {
        "state": "Rajasthan", "region": "North",
        "lat": 26.2389, "lon": 73.0243,
        "places": [("Mehrangarh Fort", 2.0, "Fort"), ("Umaid Bhawan Palace", 3.0, "Palace"),
                   ("Jaswant Thada", 2.5, "Monument"), ("Clock Tower", 1.0, "Market"),
                   ("Mandore Gardens", 6.0, "Garden")],
        "hospitals": [("AIIMS Jodhpur", 10.0), ("Mahatma Gandhi Hospital", 2.0)],
        "restaurants": [("Gypsy", 1.5, "Rajasthani", "Mid"), ("The Olive", 2.0, "Cafe", "Mid")],
        "transport": [("Jodhpur Airport", 5.0), ("Jodhpur Junction", 1.5), ("Sardar Market", 1.0)],
    },
    "Gangtok": {
        "state": "Sikkim", "region": "East",
        "lat": 27.3389, "lon": 88.6065,
        "places": [("MG Marg", 0.5, "Shopping"), ("Tsomgo Lake", 38.0, "Lake"),
                   ("Rumtek Monastery", 24.0, "Monastery"), ("Nathula Pass", 52.0, "Viewpoint"),
                   ("Ban Jhakri Falls", 8.0, "Waterfall")],
        "hospitals": [("STNM Hospital", 2.0), ("Central Referral Hospital", 5.0)],
        "restaurants": [("The Taste of Tibet", 1.0, "Tibetan", "Mid"), ("Baker's Cafe", 0.8, "Cafe", "Low")],
        "transport": [("Bagdogra Airport", 120.0), ("Gangtok Bus Stand", 0.5), ("Taxi Stand", 0.5)],
    },
    "Bhopal": {
        "state": "Madhya Pradesh", "region": "Central",
        "lat": 23.2599, "lon": 77.4126,
        "places": [("Bhimbetka Rock Shelters", 45.0, "Heritage"), ("Sanchi Stupa", 46.0, "Monument"),
                   ("Upper Lake", 4.0, "Lake"), ("Bharat Bhavan", 3.0, "Museum"),
                   ("Taj-ul-Masajid", 2.0, "Mosque")],
        "hospitals": [("AIIMS Bhopal", 12.0), ("Bansal Hospital", 5.0)],
        "restaurants": [("Mangal Singh", 3.0, "Bhopali", "Mid"), ("Bayroute", 4.0, "Biryani", "Mid")],
        "transport": [("Raja Bhoj Airport", 12.0), ("Bhopal Junction", 3.0), ("Bhopal Depot", 1.0)],
    },
    "Chandigarh": {
        "state": "Chandigarh", "region": "North",
        "lat": 30.7333, "lon": 76.7794,
        "places": [("Rock Garden", 3.0, "Garden"), ("Sukhna Lake", 2.0, "Lake"),
                   ("Capitol Complex", 2.5, "Landmark"), ("Rose Garden", 4.0, "Garden"),
                   ("Elante Mall", 3.0, "Shopping")],
        "hospitals": [("PGIMER", 5.0), ("Government Medical College", 4.0)],
        "restaurants": [("Biryani Blues", 2.0, "Biryani", "Mid"), ("Black Lotus", 3.0, "Multi-cuisine", "High")],
        "transport": [("Chandigarh Airport", 10.0), ("Chandigarh Junction", 6.0), ("ISBT-17", 2.0)],
    },
    "Bhubaneswar": {
        "state": "Odisha", "region": "East",
        "lat": 20.2961, "lon": 85.8245,
        "places": [("Lingaraj Temple", 3.0, "Temple"), ("Khandagiri Caves", 8.0, "Heritage"),
                   ("Nandankanan Zoo", 18.0, "Zoo"), ("Udayagiri Caves", 8.0, "Heritage"),
                   ("Ekamra Kanan", 7.0, "Garden")],
        "hospitals": [("AIIMS Bhubaneswar", 10.0), ("Kalinga Hospital", 8.0)],
        "restaurants": [("Diana Hotel", 3.0, "Odisha", "Mid"), ("Keshari", 4.0, "Odisha", "Low")],
        "transport": [("Biju Patnaik Intl Airport", 5.0), ("Bhubaneswar Station", 4.0), ("Baramunda Bus", 5.0)],
    },
    "Kaziranga": {
        "state": "Assam", "region": "East",
        "lat": 26.5827, "lon": 93.1933,
        "places": [("Kaziranga National Park", 2.0, "Wildlife"), ("Kohora Safari", 3.0, "Nature"),
                   ("Brahmaputra River", 2.0, "River"), ("Panbari Reserve", 4.0, "Forest"),
                   ("Biswanath Ghat", 25.0, "Ghat")],
        "hospitals": [("Kaziranga PHC", 2.0), ("Golaghat Civil Hospital", 40.0)],
        "restaurants": [("Jungle Cafe", 1.0, "Assamese", "Mid"), ("Wild Grass", 2.0, "Assamese", "High")],
        "transport": [("Jorhat Airport", 100.0), ("Kaziranga Bus Stand", 1.0), ("Bokakhat Taxi", 15.0)],
    },
    "Kanyakumari": {
        "state": "Tamil Nadu", "region": "South",
        "lat": 8.0883, "lon": 77.5385,
        "places": [("Vivekananda Rock Memorial", 1.0, "Monument"), ("Thiruvalluvar Statue", 1.0, "Statue"),
                   ("Kanyakumari Beach", 0.5, "Beach"), ("Suchindram Temple", 11.0, "Temple"),
                   ("Sunrise & Sunset Point", 0.5, "Viewpoint")],
        "hospitals": [("Kanyakumari Govt Hospital", 1.5), ("Annai Hospital", 2.0)],
        "restaurants": [("Saravana Bhavan", 1.0, "South Indian", "Low"), ("Ocean Breeze", 3.0, "Seafood", "Mid")],
        "transport": [("Trivandrum Intl Airport", 90.0), ("Kanyakumari Station", 0.5), ("Nagercoil Bus", 15.0)],
    },
    "Coorg": {
        "state": "Karnataka", "region": "South",
        "lat": 12.4244, "lon": 75.7382,
        "places": [("Abbey Falls", 5.0, "Waterfall"), ("Raja Seat", 2.0, "Viewpoint"),
                   ("Dubare Elephant Camp", 25.0, "Nature"), ("Namdroling Monastery", 35.0, "Monastery"),
                   ("Coffee Plantations", 3.0, "Estate")],
        "hospitals": [("Coorg Institute of Health", 3.0), ("Madikeri Govt Hospital", 2.0)],
        "restaurants": [("Cuchimane", 2.0, "Coorgi", "Mid"), ("Embassy", 1.5, "Coorgi", "Mid")],
        "transport": [("Mangalore Airport", 130.0), ("Madikeri Bus Stand", 1.0), ("Kushalnagar", 30.0)],
    },
    "Ooty": {
        "state": "Tamil Nadu", "region": "South",
        "lat": 11.4102, "lon": 76.6950,
        "places": [("Botanical Garden", 2.0, "Garden"), ("Ooty Lake", 1.5, "Lake"),
                   ("Doddabetta Peak", 9.0, "Viewpoint"), ("Toy Train", 1.0, "Heritage"),
                   ("Rose Garden", 3.0, "Garden")],
        "hospitals": [("Government Hospital Ooty", 2.0), ("Mountain View Hospital", 3.0)],
        "restaurants": [("The Fernhill", 2.0, "Multi-cuisine", "High"), ("Shinkows", 1.0, "Chinese", "Mid")],
        "transport": [("Coimbatore Airport", 100.0), ("Ooty (Udhagamandalam) Station", 1.0), ("Ooty Bus Depot", 1.0)],
    },
    "Puri": {
        "state": "Odisha", "region": "East",
        "lat": 19.8135, "lon": 85.8312,
        "places": [("Jagannath Temple", 1.0, "Temple"), ("Puri Beach", 1.5, "Beach"),
                   ("Konark Sun Temple", 35.0, "Monument"), ("Chilika Lake", 50.0, "Lake"),
                   ("Gundicha Temple", 3.0, "Temple")],
        "hospitals": [("District Headquarter Hospital", 1.5), ("Institute of Medical Sciences", 3.0)],
        "restaurants": [("Chandrika", 1.0, "Odisha", "Mid"), ("Pahala Rasagola", 2.0, "Sweets", "Low")],
        "transport": [("Bhubaneswar Airport", 60.0), ("Puri Railway Station", 0.5), ("Puri Bus Stand", 1.0)],
    },
    "Hampi": {
        "state": "Karnataka", "region": "South",
        "lat": 15.3350, "lon": 76.4600,
        "places": [("Virupaksha Temple", 1.0, "Temple"), ("Vittala Temple", 3.0, "Temple"),
                   ("Matanga Hill", 1.0, "Viewpoint"), ("Hampi Bazaar", 0.5, "Market"),
                   ("Royal Enclosure", 2.0, "Heritage")],
        "hospitals": [("Hampi PHC", 1.0), ("Hospet Hospital", 13.0)],
        "restaurants": [("The Gouthami", 1.0, "South Indian", "Low"), ("Mango Tree", 0.8, "Multi-cuisine", "Mid")],
        "transport": [("Kempegowda Airport", 350.0), ("Hospet Junction", 13.0), ("Hampi Bus Stop", 0.5)],
    },
    "Leh": {
        "state": "Ladakh", "region": "North",
        "lat": 34.1526, "lon": 77.5771,
        "places": [("Pangong Lake", 140.0, "Lake"), ("Shanti Stupa", 2.0, "Stupa"),
                   ("Leh Palace", 1.0, "Palace"), ("Nubra Valley", 150.0, "Valley"),
                   ("Khardung La", 40.0, "Mountain Pass")],
        "hospitals": [("SNM Hospital Leh", 2.0), ("Sonam Norbu Memorial", 2.0)],
        "restaurants": [("Bon Appetit", 1.0, "Tibetan", "Mid"), ("Gesmo Restaurant", 0.8, "Cafe", "Mid")],
        "transport": [("Kushok Bakula Rimpochee Airport", 2.0), ("Leh Bus Stand", 0.5), ("Taxi Stand Leh", 0.5)],
    },
    "Tirupati": {
        "state": "Andhra Pradesh", "region": "South",
        "lat": 13.6288, "lon": 79.4192,
        "places": [("Tirumala Temple", 22.0, "Temple"), ("Sri Padmavathi Ammavari Temple", 5.0, "Temple"),
                   ("Kapila Theertham", 3.0, "Temple"), ("Sri Venkateswara Zoo", 5.0, "Zoo"),
                   ("Chandragiri Fort", 11.0, "Fort")],
        "hospitals": [("SVIMS Hospital", 5.0), ("Sri Venkateswara Hospital", 3.0)],
        "restaurants": [("Hotel Bhimas", 2.0, "Andhra", "Mid"), ("Mayura", 3.0, "Multi-cuisine", "Mid")],
        "transport": [("Tirupati Airport (Renigunta)", 10.0), ("Tirupati Station", 2.0), ("Tirumala Bus Stand", 3.0)],
    },
    "Visakhapatnam": {
        "state": "Andhra Pradesh", "region": "South",
        "lat": 17.6868, "lon": 83.2185,
        "places": [("Rushikonda Beach", 10.0, "Beach"), ("Kailasagiri Hill Park", 6.0, "Landmark"),
                   ("Borra Caves", 80.0, "Cave"), ("Simhachalam Temple", 16.0, "Temple"),
                   ("Araku Valley", 115.0, "Nature")],
        "hospitals": [("King George Hospital", 4.0), ("Care Hospital", 6.0)],
        "restaurants": [("Daspalla", 2.0, "Seafood", "Mid"), ("New Andhra Restaurant", 3.0, "Andhra", "Mid")],
        "transport": [("Visakhapatnam Airport", 12.0), ("Visakhapatnam Junction", 3.0), ("Dwaraka Bus Station", 2.5)],
    },
    "Vijayawada": {
        "state": "Andhra Pradesh", "region": "South",
        "lat": 16.5062, "lon": 80.6480,
        "places": [("Kanaka Durga Temple", 3.0, "Temple"), ("Prakasam Barrage", 2.0, "Landmark"),
                   ("Undavalli Caves", 10.0, "Cave"), ("Victoria Museum", 2.5, "Museum"),
                   ("Bhavani Island", 5.0, "Island")],
        "hospitals": [("Vijayawada General Hospital", 3.0), ("Manipal Hospital", 5.0)],
        "restaurants": [("Pista House", 2.0, "Biryani", "Mid"), ("Amaravathi Biryani", 3.5, "Andhra", "Mid")],
        "transport": [("Vijayawada Airport (Gannavaram)", 18.0), ("Vijayawada Junction", 2.0), ("Benz Circle Bus", 2.0)],
    },

    "Mount Abu": {
        "state": "Rajasthan", "region": "North",
        "lat": 24.5854, "lon": 72.7153,
        "places": [("Dilwara Temples", 5.0, "Temple"), ("Nakki Lake", 1.0, "Lake"),
                   ("Guru Shikhar", 18.0, "Peak"), ("Sunset Point", 2.0, "Viewpoint"),
                   ("Achalgarh Fort", 9.0, "Fort")],
        "hospitals": [("Mount Abu Govt Hospital", 1.0), ("Sirohi Civil Hospital", 35.0)],
        "restaurants": [("Moti Mahal", 1.0, "Rajasthani", "Mid"), ("Bikaner Sweets", 0.8, "Sweets", "Low")],
        "transport": [("Udaipur Airport", 160.0), ("Abu Road Station", 27.0), ("Mount Abu Bus Stand", 0.5)],
    },
    "Auroville": {
        "state": "Tamil Nadu", "region": "South",
        "lat": 12.0104, "lon": 79.8079,
        "places": [("Matrimandir", 1.0, "Landmark"), ("Auroville Beach", 8.0, "Beach"),
                   ("Pondicherry French Quarter", 12.0, "Heritage"), ("Serenity Beach", 7.0, "Beach"),
                   ("Bharat Nivas", 2.0, "Cultural")],
        "hospitals": [("Government Hospital", 12.0), ("Auroville Health Centre", 2.0)],
        "restaurants": [("Solar Kitchen", 1.0, "Community", "Mid"), ("La Pizzeria", 12.0, "Italian", "Mid")],
        "transport": [("Chennai Intl Airport", 170.0), ("Puducherry Station", 14.0), ("Auroville Bus", 1.0)],
    },
    "Manali": {
        "state": "Himachal Pradesh", "region": "North",
        "lat": 32.2396, "lon": 77.1887,
        "places": [("Solang Valley", 14.0, "Adventure"), ("Hadimba Temple", 2.0, "Temple"),
                   ("Kasol & Manikaran", 60.0, "Nature"), ("Rohtang Pass", 50.0, "Mountain Pass"),
                   ("Old Manali", 1.5, "Cafe")],
        "hospitals": [("District Hospital Kullu", 40.0), ("Manali PHC", 1.5)],
        "restaurants": [("Cafe 1947", 1.0, "Cafe", "Mid"), ("The Johnson's", 1.5, "Multi-cuisine", "High")],
        "transport": [("Kullu Airport", 40.0), ("Manali Bus Stand", 0.5), ("Taxi Stand", 0.5)],
    },
    "Dharamshala": {
        "state": "Himachal Pradesh", "region": "North",
        "lat": 32.2189, "lon": 76.3234,
        "places": [("McLeod Ganj", 3.0, "Hill Station"), ("Tsuglagkhang Monastery", 3.0, "Monastery"),
                   ("Bhagsu Falls", 6.0, "Waterfall"), ("Triund Trek", 10.0, "Trek"),
                   ("Kangra Fort", 30.0, "Fort")],
        "hospitals": [("Zonal Hospital Dharamshala", 3.0), ("Delek Hospital", 3.0)],
        "restaurants": [("Nick's Italian", 3.0, "Italian", "Mid"), ("Jimmy's Cafe", 2.5, "Cafe", "Mid")],
        "transport": [("Kangra Airport", 18.0), ("Dharamshala Bus Stand", 1.0), ("McLeod Ganj Taxi", 3.0)],
    },
    "Alleppey": {
        "state": "Kerala", "region": "South",
        "lat": 9.4981, "lon": 76.3388,
        "places": [("Alleppey Backwaters", 1.0, "Backwaters"), ("Alappuzha Beach", 1.5, "Beach"),
                   ("Vembanad Lake", 2.0, "Lake"), ("Kuttanad Rice Fields", 15.0, "Nature"),
                   ("Marari Beach", 12.0, "Beach")],
        "hospitals": [("Alappuzha Medical College", 2.0), ("District Hospital", 1.5)],
        "restaurants": [("Karimeen", 1.0, "Kerala", "Mid"), ("The Backyard", 1.5, "Seafood", "Mid")],
        "transport": [("Kochi Airport", 85.0), ("Alappuzha Station", 1.0), ("Alappuzha Bus", 0.5)],
    },
    "Munnar": {
        "state": "Kerala", "region": "South",
        "lat": 10.0889, "lon": 77.0595,
        "places": [("Eravikulam National Park", 12.0, "Wildlife"), ("Mattupetty Dam", 8.0, "Dam"),
                   ("Tea Museum", 4.0, "Museum"), ("Top Station", 40.0, "Viewpoint"),
                   ("Attukal Waterfalls", 6.0, "Waterfall")],
        "hospitals": [("Government Hospital Munnar", 2.0), ("Kochi Medical Centre", 120.0)],
        "restaurants": [("Rapsy Restaurant", 2.0, "Kerala", "Mid"), ("Saravana Bhavan", 1.5, "South Indian", "Low")],
        "transport": [("Kochi Airport", 120.0), ("Munnar Bus Stand", 0.5), ("Adimali Taxi", 20.0)],
    },
    "Panchgani": {
        "state": "Maharashtra", "region": "West",
        "lat": 17.9200, "lon": 73.8000,
        "places": [("Sydenham Point", 2.0, "Viewpoint"), ("Parsi Point", 3.0, "Viewpoint"),
                   ("Table Land", 2.0, "Plateau"), ("Venna Lake", 12.0, "Lake"),
                   ("Rajpuri Caves", 4.0, "Caves")],
        "hospitals": [("Satara Civil Hospital", 50.0), ("Panchgani PHC", 1.0)],
        "restaurants": [("Hilltop", 1.0, "Multi-cuisine", "Mid"), ("Sher-e-Punjab", 2.0, "Punjabi", "Mid")],
        "transport": [("Pune Airport", 150.0), ("Dapoli Station", 100.0), ("Panchgani Bus", 0.5)],
    },
    "Siliguri": {
        "state": "West Bengal", "region": "East",
        "lat": 26.7271, "lon": 88.3953,
        "places": [("Mahananda Wildlife Sanctuary", 15.0, "Wildlife"), ("Salugara Monastery", 5.0, "Monastery"),
                   ("Gajoldoba", 30.0, "Lake"), ("Coronation Bridge", 12.0, "Bridge"),
                   ("ISKCON Siliguri", 3.0, "Temple")],
        "hospitals": [("North Bengal Medical College", 6.0), ("Amitabha Hospital", 3.0)],
        "restaurants": [("Raj Sangeet", 2.0, "Multi-cuisine", "Mid"), ("Amodini", 3.0, "Bengali", "Mid")],
        "transport": [("Bagdogra Airport", 12.0), ("New Jalpaiguri Station", 5.0), ("Siliguri ISBT", 2.0)],
    },
    "Vadodara": {
        "state": "Gujarat", "region": "West",
        "lat": 22.3072, "lon": 73.1812,
        "places": [("Laxmi Vilas Palace", 2.0, "Palace"), ("Sayaji Garden", 2.0, "Garden"),
                   ("Baroda Museum", 2.0, "Museum"), ("Kirti Mandir", 3.0, "Monument"),
                   ("Kamladevi Complex", 4.0, "Shopping")],
        "hospitals": [("Baroda Medical College", 4.0), ("Sterling Hospital", 6.0)],
        "restaurants": [("Saffron", 3.0, "Gujarati", "High"), ("Maharaja", 2.0, "Gujarati", "Mid")],
        "transport": [("Vadodara Airport", 6.0), ("Vadodara Junction", 2.0), ("Alkapuri Bus", 1.0)],
    },
    "Nainital": {
        "state": "Uttarakhand", "region": "North",
        "lat": 29.3919, "lon": 79.4542,
        "places": [("Naini Lake", 1.0, "Lake"), ("Naina Devi Temple", 1.0, "Temple"),
                   ("Snow View Point", 2.0, "Viewpoint"), ("Mall Road", 0.5, "Shopping"),
                   ("Tiffin Top", 2.5, "Viewpoint")],
        "hospitals": [("Susheela Tiwari Hospital", 2.0), ("Nainital Hospital", 1.5)],
        "restaurants": [("Sakley's", 1.0, "Cafe", "Mid"), ("Sher-e-Punjab", 1.5, "Punjabi", "Mid")],
        "transport": [("Pantnagar Airport", 70.0), ("Kathgodam Station", 30.0), ("Nainital Bus", 0.5)],
    },
    "Ajmer": {
        "state": "Rajasthan", "region": "North",
        "lat": 26.4499, "lon": 74.6399,
        "places": [("Ajmer Sharif Dargah", 1.0, "Dargah"), ("Ana Sagar Lake", 2.0, "Lake"),
                   ("Adhai Din Ka Jhonpra", 1.5, "Monument"), ("Mayo College", 3.0, "Heritage"),
                   ("Soniji Ki Nasiyan", 1.0, "Temple")],
        "hospitals": [("JLN Medical College", 2.0), ("Ajmer Hospital", 1.5)],
        "restaurants": [("Mohanlal", 1.0, "Sweets", "Low"), ("Anna", 2.0, "Multi-cuisine", "Mid")],
        "transport": [("Kishangarh Airport", 30.0), ("Ajmer Junction", 1.0), ("Ajmer Bus", 0.5)],
    },
    "Port Blair": {
        "state": "Andaman & Nicobar", "region": "East",
        "lat": 11.6234, "lon": 92.7265,
        "places": [("Cellular Jail", 2.0, "Monument"), ("Radhanagar Beach", 35.0, "Beach"),
                   ("Ross Island", 3.0, "Heritage"), ("North Bay", 4.0, "Beach"),
                   ("Havelock Island", 60.0, "Island")],
        "hospitals": [("GB Pant Hospital", 2.0), ("Andaman Hospital", 3.0)],
        "restaurants": [("Anju Coco", 2.0, "Seafood", "Mid"), ("New Lighthouse", 3.0, "Seafood", "High")],
        "transport": [("Veer Savarkar Airport", 3.0), ("Phoenix Bay Jetty", 2.0), ("Rajnagar Bus", 1.0)],
    },
    "Kovalam": {
        "state": "Kerala", "region": "South",
        "lat": 8.3981, "lon": 76.9784,
        "places": [("Lighthouse Beach", 1.0, "Beach"), ("Samudra Beach", 2.0, "Beach"),
                   ("Hawa Beach", 1.0, "Beach"), ("Vizhinjam Lighthouse", 1.5, "Landmark"),
                   ("Veli Lake", 15.0, "Lake")],
        "hospitals": [("Medical Trust Kovalam", 2.0), ("Government Hospital", 3.0)],
        "restaurants": [("The Bait", 1.0, "Seafood", "High"), ("Sunshine", 1.5, "Continental", "Mid")],
        "transport": [("Trivandrum Intl Airport", 15.0), ("Trivandrum Central", 12.0), ("Kovalam Bus", 0.5)],
    },
}

# Hotel name templates by type
TYPES = ["Luxury", "Boutique", "Business", "Resort", "Heritage", "Budget"]
NAME_HINTS = {
    "Luxury": ["The Grand", "Imperial", "Royal Crown", "Serene", "Prestige"],
    "Boutique": ["The Nook", "Casa", "Haven", "Maison", "Villa"],
    "Business": ["Metro", "Corporate Inn", "The Gateway", "Executive Suite"],
    "Resort": ["The Palm", "Lakeside", "Valley View", "Oasis", "Riverside"],
    "Heritage": ["Mahal", "Palace", "Haveli", "Fort View", "Retreat"],
    "Budget": ["Comfort", "Stay Easy", "City Stay", "Lodging"],
}

# Fixed list of 50 hotel specs: (city, name, type, stars, base_price_inr, rating, description)
HOTELS = [
    ("New Delhi", "Imperial Delhi", "Luxury", 5, 12500, 4.8),
    ("New Delhi", "Heritage Haveli", "Heritage", 4, 6800, 4.6),
    ("Mumbai", "Marine Grand", "Luxury", 5, 14500, 4.7),
    ("Mumbai", "Tower Gateway", "Business", 4, 8200, 4.5),
    ("Bengaluru", "Tech Hub Suites", "Business", 4, 6500, 4.4),
    ("Bengaluru", "Cubbon Boutique", "Boutique", 4, 7800, 4.6),
    ("Hyderabad", "Charminar Palace", "Heritage", 4, 5600, 4.5),
    ("Hyderabad", "Pearl Centre", "Business", 4, 4800, 4.2),
    ("Chennai", "Marina Bay Resort", "Resort", 4, 7200, 4.6),
    ("Chennai", "Madras Executive", "Business", 3, 3900, 4.1),
    ("Kolkata", "Victoria Grand", "Luxury", 5, 8800, 4.6),
    ("Kolkata", "City Comfort Aroma", "Budget", 3, 2600, 4.0),
    ("Jaipur", "Amber Heritage", "Heritage", 5, 9200, 4.8),
    ("Jaipur", "Pink City Comfort", "Budget", 3, 2900, 4.1),
    ("Agra", "Taj View", "Luxury", 5, 7900, 4.7),
    ("Goa", "Beach Oasis", "Resort", 4, 8600, 4.6),
    ("Goa", "Palm Shore", "Resort", 4, 7400, 4.5),
    ("Udaipur", "Lake Pichola Palace", "Heritage", 5, 10800, 4.9),
    ("Varanasi", "Ganga Ghat Retreat", "Boutique", 4, 5200, 4.6),
    ("Kochi", "Fort Kochi Haven", "Boutique", 4, 4900, 4.4),
    ("Amritsar", "Golden Temple Inn", "Budget", 3, 2400, 4.3),
    ("Shimla", "Ridge Retreat", "Resort", 4, 6400, 4.5),
    ("Darjeeling", "Tea Valley Resort", "Resort", 4, 5800, 4.6),
    ("Pune", "Western Executive", "Business", 4, 4600, 4.3),
    ("Ahmedabad", "Sabarmati Grand", "Business", 4, 4300, 4.2),
    ("Mysuru", "Palace Courts", "Heritage", 4, 5100, 4.5),
    ("Rishikesh", "Ganga Riverside", "Resort", 4, 4700, 4.6),
    ("Shillong", "Cloud Nine", "Resort", 3, 3800, 4.4),
    ("Lucknow", "Awadhi Heritage", "Heritage", 4, 4500, 4.3),
    ("Jodhpur", "Blue City Palace", "Heritage", 4, 5900, 4.6),
    ("Gangtok", "Himalaya View", "Resort", 4, 5500, 4.6),
    ("Bhopal", "Lake View", "Business", 3, 3600, 4.2),
    ("Chandigarh", "City Green", "Business", 4, 4200, 4.3),
    ("Bhubaneswar", "Lingaraj Comfort", "Budget", 3, 3100, 4.1),
    ("Kaziranga", "Jungle Lodge", "Resort", 4, 7800, 4.7),
    ("Kanyakumari", "Ocean Point", "Resort", 3, 3400, 4.4),
    ("Coorg", "Coffee Valley Stay", "Resort", 4, 4900, 4.6),
    ("Ooty", "Nilgiri Heights", "Resort", 4, 5300, 4.5),
    ("Puri", "Sea Shore Resort", "Resort", 4, 4300, 4.4),
    ("Hampi", "Heritage Stones", "Heritage", 3, 3600, 4.5),
    ("Leh", "Ladakh Heights", "Resort", 3, 6200, 4.7),
    ("Tirupati", "Divine Stay", "Budget", 3, 2800, 4.3),
    ("Mount Abu", "Hilltop Hut", "Resort", 3, 4100, 4.4),
    ("Auroville", "Serenity Retreat", "Boutique", 4, 5400, 4.6),
    ("Manali", "Solang Valley", "Resort", 4, 5600, 4.5),
    ("Dharamshala", "Himalayan Calm", "Boutique", 3, 3800, 4.6),
    ("Alleppey", "Backwater Villa", "Resort", 4, 6000, 4.7),
    ("Munnar", "Tea Hills", "Resort", 4, 5200, 4.6),
    ("Siliguri", "Gateway North", "Business", 3, 3300, 4.2),
    ("Vadodara", "Gaekwad Grand", "Business", 4, 4000, 4.3),
    ("Nainital", "Lake Edge", "Resort", 4, 4800, 4.5),
    ("Ajmer", "Dargah View", "Budget", 3, 2700, 4.2),
    ("Port Blair", "Island Bay", "Resort", 4, 8800, 4.7),
    ("Kovalam", "Lighthouse Bay", "Resort", 4, 4900, 4.5),
    ("Panchgani", "Hill Station", "Budget", 3, 3000, 4.3),
    ("Visakhapatnam", "Bay View Grand", "Resort", 4, 6400, 4.6),
    ("Visakhapatnam", "Rushikonda Beach Resort", "Resort", 4, 7200, 4.7),
    ("Vijayawada", "Prakasam Palace", "Business", 4, 4600, 4.4),
    ("Vijayawada", "Krishna Executive", "Business", 3, 3400, 4.2),
    ("Agra", "Taj Gateway Grand", "Luxury", 5, 8900, 4.8),
    ("Ahmedabad", "Sabarmati Riverfront", "Business", 5, 6800, 4.5),
    ("Ajmer", "Ana Sagar Retreat", "Resort", 4, 4700, 4.4),
    ("Alleppey", "Backwater Haven", "Resort", 4, 6200, 4.7),
    ("Amritsar", "Harmandir View", "Heritage", 5, 7200, 4.6),
    ("Auroville", "Matrimandir Residency", "Resort", 4, 5600, 4.5),
    ("Bhopal", "Upper Lake Grand", "Business", 4, 4300, 4.3),
    ("Bhubaneswar", "Lingaraj Greens", "Resort", 4, 4000, 4.3),
    ("Chandigarh", "Sukhna Lake View", "Business", 4, 4900, 4.4),
    ("Coorg", "Coffee Estate Resort", "Resort", 5, 7600, 4.8),
    ("Darjeeling", "Kanchenjunga View", "Resort", 4, 6400, 4.7),
    ("Dharamshala", "Kangra Hills Retreat", "Resort", 4, 5200, 4.6),
    ("Gangtok", "Tsomgo Heights", "Resort", 4, 6100, 4.6),
    ("Hampi", "Boulder Heritage Stay", "Heritage", 4, 4200, 4.5),
    ("Jodhpur", "Mehrangarh Palace", "Heritage", 5, 8500, 4.8),
    ("Kanyakumari", "Vivekananda Bay Resort", "Resort", 4, 4600, 4.5),
    ("Kaziranga", "Wild Frontier Lodge", "Resort", 5, 9300, 4.8),
    ("Kochi", "Marine Drive Grand", "Business", 4, 5400, 4.5),
    ("Kovalam", "Lighthouse Beach Resort", "Resort", 4, 5800, 4.6),
    ("Leh", "Nubra Valley Heights", "Resort", 4, 6900, 4.7),
    ("Lucknow", "Gomti River Grand", "Heritage", 4, 5300, 4.4),
    ("Manali", "Himalayan Pines Resort", "Resort", 4, 6300, 4.6),
    ("Mount Abu", "Aravalli Heights", "Resort", 4, 5200, 4.5),
    ("Munnar", "Cardamom Hills Retreat", "Resort", 4, 5800, 4.6),
    ("Mysuru", "Mysore Palace Residency", "Heritage", 5, 7800, 4.7),
    ("Nainital", "Naini Lake View", "Resort", 4, 5400, 4.5),
    ("Ooty", "Botanical Bay Resort", "Resort", 4, 5600, 4.5),
    ("Panchgani", "Krishna Valley Resort", "Resort", 4, 4200, 4.3),
    ("Port Blair", "Corbyn Cove Resort", "Resort", 4, 9200, 4.7),
    ("Pune", "Koregaon Park Residency", "Business", 5, 7000, 4.6),
    ("Puri", "Jagannath Bay Resort", "Resort", 4, 4800, 4.4),
    ("Rishikesh", "Ganga Aarti Retreat", "Resort", 4, 5400, 4.6),
    ("Shillong", "Umiam Lake Heights", "Resort", 4, 4600, 4.4),
    ("Shimla", "Mall Road Grand", "Resort", 4, 7200, 4.6),
    ("Siliguri", "Mahananda Gateway", "Business", 4, 4000, 4.2),
    ("Tirupati", "Tirumala Hills Stay", "Resort", 4, 4200, 4.4),
    ("Udaipur", "Lake Fateh Palace", "Heritage", 5, 12500, 4.9),
    ("Vadodara", "Vishwamitri Grand", "Business", 4, 4800, 4.3),
    ("Varanasi", "Assi Ghat Heritage", "Heritage", 4, 5800, 4.6),
]

# ---------------------------------------------------------------------------
def build_amenities(hotel_type, stars):
    base = ["Free Wi-Fi", "24-hour Front Desk", "Daily Housekeeping"]
    if stars >= 4:
        base += ["Airport Shuttle", "In-room Dining", "Spa & Wellness", "Fitness Center", "Concierge"]
    if stars >= 5:
        base += ["Butler Service", "Infinity Pool", "Executive Lounge"]
    if hotel_type == "Resort":
        base += ["Pools", "Tours Desk", "Garden", "Kid's Zone"]
    if hotel_type == "Heritage":
        base += ["Guided Tours", "Courtyard", "Heritage Architecture"]
    if hotel_type == "Business":
        base += ["Meeting Rooms", "Business Centre", "Work Desks"]
    if hotel_type == "Budget":
        base += ["Luggage Storage", "Laundry"]
    # accessibility extras
    base += ["Wheelchair Accessible Entrance", "Accessible Parking", "Braille Signage"]
    return base


def build_rooms(base_price, stars):
    def price(mult):
        p = int(round(base_price * mult / 10) * 10)
        return p
    rooms = [
        {"type": "Accessible Room", "beds": "1 Queen", "guests": 2, "price_inr": price(1.05),
         "amenities": ["Wheelchair Turn Space", "Ramped Entrance", "Accessible Bathroom", "Roll-in Shower",
                       "Grab Bars", "Lowered Switches", "Visual Alarm"]},
        {"type": "Standard", "beds": "1 Queen", "guests": 2, "price_inr": price(1.0),
         "amenities": ["AC", "Wi-Fi", "TV", "Tea/Coffee", "Bathroom"]},
        {"type": "Deluxe", "beds": "1 King", "guests": 3, "price_inr": price(1.45),
         "amenities": ["City View", "AC", "Minibar", "Wi-Fi", "Balcony"]},
        {"type": "Suite", "beds": "1 King + Sofa", "guests": 4, "price_inr": price(2.1),
         "amenities": ["Living Room", "Bathtub", "Nespresso", "Panoramic View", "Dining Area"]},
    ]
    if stars <= 3:
        rooms = [r for r in rooms if r["type"] != "Suite"] or rooms[:3]
    return rooms


def build_menu(stars):
    menu = [
        {"category": "Breakfast", "items": [
            {"name": "Masala Dosa", "price_inr": 180, "veg": True},
            {"name": "Idli Sambar", "price_inr": 150, "veg": True},
            {"name": "Poha", "price_inr": 130, "veg": True},
            {"name": "Eggs Benedict", "price_inr": 320, "veg": False},
        ]},
        {"category": "Starters", "items": [
            {"name": "Paneer Tikka", "price_inr": 290, "veg": True},
            {"name": "Chicken 65", "price_inr": 320, "veg": False},
            {"name": "Hara Bhara Kebab", "price_inr": 240, "veg": True},
            {"name": "Samosa Platter", "price_inr": 160, "veg": True},
        ]},
        {"category": "Mains", "items": [
            {"name": "Butter Chicken", "price_inr": 390, "veg": False},
            {"name": "Dal Makhani", "price_inr": 280, "veg": True},
            {"name": "Biryani (Chicken)", "price_inr": 350, "veg": False},
            {"name": "Paneer Butter Masala", "price_inr": 300, "veg": True},
            {"name": "Veg Thali", "price_inr": 260, "veg": True},
        ]},
        {"category": "Desserts", "items": [
            {"name": "Gulab Jamun", "price_inr": 130, "veg": True},
            {"name": "Rasmalai", "price_inr": 160, "veg": True},
            {"name": "Gajar Ka Halwa", "price_inr": 180, "veg": True},
        ]},
        {"category": "Beverages", "items": [
            {"name": "Filter Coffee", "price_inr": 90, "veg": True},
            {"name": "Masala Chai", "price_inr": 70, "veg": True},
            {"name": "Fresh Lime Soda", "price_inr": 100, "veg": True},
            {"name": "Mocktail", "price_inr": 180, "veg": True},
        ]},
    ]
    if stars <= 3:
        # Trim some high-price items
        menu = [{"category": c["category"],
                 "items": [i for i in c["items"][:3] if i["price_inr"] <= 300]}
                for c in menu]
    return menu


def build_accessibility(stars):
    # Accessibility profile - all hotels are accessibility-aware
    return {
        "wheelchair_accessible": True,
        "elevator": True,
        "lifts_ramps": True,
        "accessible_bathrooms": True,
        "accessible_rooms": True,
        "staff_assistance": True,
        "accessible_parking": True,
        "braille_signage": True,
        "hearing_loop": stars >= 4,
        "visual_alarms": bool(stars >= 4),
        "service_animals_welcome": True,
        "guide_dog_friendly": True,
        "low_vision_support": bool(stars >= 4),
        "wheelchair_rental": bool(stars >= 4),
        "emergency_exit_ramp": True,
        "wide_corridors": True,
    }


def build_description(city, hotel_type, stars):
    c = CITY[city]
    place = c["places"][0][0]
    t = hotel_type.lower()
    if hotel_type == "Luxury":
        lead = "A five-star landmark of luxury"
    elif hotel_type == "Heritage":
        lead = "A restored heritage property full of character"
    elif hotel_type == "Resort":
        lead = "A serene resort surrounded by nature"
    elif hotel_type == "Business":
        lead = "A smart, comfortable base for work and travel"
    elif hotel_type == "Boutique":
        lead = "An intimate boutique stay with local artisan touches"
    else:
        lead = "A friendly, budget-friendly stay with everything you need"
    return (f"{lead} in {city}, {c['state']}. Minutes from {place} and other landmarks. "
            f"Committed to inclusive, accessible hospitality with ramps, lifts, accessible rooms and "
            f"trained staff assistance for guests with disabilities.")


def _slug(text):
    """Lowercase alphanumeric slug (keeps letters/digits, spaces become '-')."""
    s = ""
    for ch in str(text).lower():
        if ch.isalnum():
            s += ch
        elif ch in (" ", "-", "_", "&", "."):
            s += "-"
    s = "-".join(x for x in s.split("-") if x)
    return s


def build_contact(hotel_id, name, city):
    """Generate deterministic, demo (fictional) contact details for a hotel.

    These hotels are demo entries, so the phone / email / website are clearly
    fictional placeholders tied to the hotel name & city. They are NOT real,
    verified business contacts. Format:
      phone  : +91 9XXXX XXXXX (10-digit mobile derived from the id)
      email  : contact@<slug-name>-<slug-city>.in
      website: https://www.<slug-name>-<slug-city>.com
    """
    base = f"{_slug(name)}-{_slug(city)}"
    # Deterministic 10-digit Indian mobile number: 9 + 9 digits from the id.
    seed = (hotel_id * 2654435761) % 1000000000  # 9 digits
    mobile = "9" + str(seed).zfill(9)
    phone = f"+91 {mobile[:5]} {mobile[5:]}"
    email = f"contact@{base}.in"
    website = f"https://www.{base}.com"
    return phone, email, website


def build_hotels():
    hotels = []
    for i, (city, name, htype, stars, base_price, rating) in enumerate(HOTELS, start=1):
        c = CITY[city]
        desc = build_description(city, htype, stars)
        phone, email, website = build_contact(i, name, city)
        # derived fields
        if rating >= 4.8:
            badge = "Exceptional"
        elif rating >= 4.5:
            badge = "Excellent"
        elif rating >= 4.0:
            badge = "Good"
        else:
            badge = "Pleasant"
        hotels.append({
            "id": i,
            "name": name,
            "city": city,
            "state": c["state"],
            "region": c["region"],
            "latitude": round(c["lat"] + (i % 7) * 0.004, 5),
            "longitude": round(c["lon"] + (i % 5) * 0.004, 5),
            "type": htype,
            "stars": stars,
            "rating": rating,
            "badge": badge,
            "price_inr": base_price,
            "currency": "INR",
            "description": desc,
            "amenities": build_amenities(htype, stars),
            "accessibility": build_accessibility(stars),
            "nearest_place": c["places"][0][0],
            "rooms": build_rooms(base_price, stars),
            "food_menu": build_menu(stars),
            "nearby_places": [{"name": p[0], "distance_km": p[1], "category": p[2]} for p in c["places"]],
            "nearby_hospitals": [{"name": h[0], "distance_km": h[1]} for h in c["hospitals"]],
            "nearby_restaurants": [{"name": r[0], "distance_km": r[1], "cuisine": r[2], "price": r[3]} for r in c["restaurants"]],
            "nearby_transport": [{"type": "Airport", "name": t[0], "distance_km": t[1]} if "Airport" in t[0]
                                 else ({"type": "Railway", "name": t[0], "distance_km": t[1]} if "Station" in t[0] or "Junction" in t[0]
                                       else {"type": "Local Transport", "name": t[0], "distance_km": t[1]})
                                 for t in c["transport"]],
            "address": f"{name}, {city}, {c['state']}",
            "check_in": "14:00",
            "check_out": "12:00",
            "phone": phone,
            "email": email,
            "website": website,
        })
    return hotels


def create_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE hotels (
            id INTEGER PRIMARY KEY,
            name TEXT, city TEXT, state TEXT, region TEXT,
            latitude REAL, longitude REAL,
            type TEXT, stars INTEGER, rating REAL, badge TEXT,
            price_inr INTEGER, currency TEXT,
            description TEXT, amenities TEXT, accessibility TEXT,
            nearest_place TEXT, rooms TEXT, food_menu TEXT,
            nearby_places TEXT, nearby_hospitals TEXT,
            nearby_restaurants TEXT, nearby_transport TEXT,
            address TEXT, check_in TEXT, check_out TEXT,
            phone TEXT, email TEXT, website TEXT
        )
    """)
    hotels = build_hotels()
    for h in hotels:
        json_fields = ["amenities", "accessibility", "rooms", "food_menu",
                       "nearby_places", "nearby_hospitals", "nearby_restaurants", "nearby_transport"]
        vals = []
        for k, v in h.items():
            if k in json_fields:
                vals.append(json.dumps(v, ensure_ascii=False))
            else:
                vals.append(v)
        placeholders = ",".join("?" * len(vals))
        cur.execute(f"INSERT INTO hotels VALUES ({placeholders})", vals)
    conn.commit()
    conn.close()
    print(f"Seeded {len(hotels)} hotels into {DB_PATH}")


if __name__ == "__main__":
    create_db()
