import requests

def search_nearby_hospitals(api_key, latitude, longitude, radius=10000):
    base_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = {
        'key': api_key,
        'location': f'{latitude},{longitude}',
        'radius': radius,
        'type': 'university'
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print('Failed to retrieve data:', response.status_code)
        return []

api_key = 'AIzaSyBmhJ8FVHqiluHu4iNog2ooc-hNaOpHul0'
latitude = -23.647778
longitude = -46.573333
results = search_nearby_hospitals(api_key, latitude, longitude)
for hospital in results['results']:
    name = hospital['name']
    address = hospital['vicinity']
    rating = hospital.get('rating', 'N/A')
    num_ratings = hospital.get('user_ratings_total', 'N/A')
    types = ', '.join(hospital['types'])
    latitude = hospital['geometry']['location']['lat']
    longitude = hospital['geometry']['location']['lng']
    
    print(f"Name: {name}")
    print(f"Address: {address}")
    print(f"Rating: {rating}")
    print(f"Number of ratings: {num_ratings}")
    print(f"Types: {types}")
    print(f"Latitude: {latitude}, Longitude: {longitude}")
    print()
