import random
import os
from faker import Faker
from datetime import datetime
import pandas as pd

fake = Faker()

Faker.seed(42)
random.seed(42)

SITE_CSV_PATH = "data/raw/sites.csv"
USER_CSV_PATH = "data/raw/users.csv"

# Ensure directory exists
os.makedirs(os.path.dirname(SITE_CSV_PATH), exist_ok=True)

# County/Sub-county Mappings from your data
county_mapping = {
    "Makueni": 1, "Nyeri": 2, "Kakamega": 3, "Nakuru": 4, "Nyandarua": 5,
    "Meru": 6, "Kilifi": 7, "Mombasa": 8, "Nairobi": 9
}

sub_county_mapping = {
    "Makueni": {"Makueni": 1, "Mbooni": 2, "Kaiti": 3, "Kibwezi East": 4, "Kibwezi West": 5, "Kilome": 6},
    "Nyeri": {"Kieni East": 7, "Kieni West": 8, "Mathira East": 9, "Mathira West": 10, "Othaya": 11, "Mukurweini": 12, "Nyeri Town": 13, "Tetu": 14},
    "Kakamega": {"Lukuyani": 15, "Butere": 16, "Mumias": 17, "Shinyalu": 18, "Matete": 19, "Lugari": 20,
                 "Lurambi": 21, "Khwisero": 22, "Mutungu": 23, "Navakholo": 24, "Kakamega South": 25, "Kakamega Central": 26,
                 "Kakamega East": 27, "Kakamega North": 28},
    "Nakuru": {"Nakuru Town East": 29, "Nakuru Town West": 30, "Naivasha": 31, "Molo": 32, "Gilgil": 33, "Bahati": 34,
               "Kuresoi North": 35, "Kuresoi South": 36, "Njoro": 37, "Rongai": 38, "Subukia": 39},
    "Nyandarua": {"Ol Kalou": 40, "Kipipiri": 41, "Ndaragwa": 42, "Kinangop": 43, "Ol Joro Orok": 44},
    "Meru": {"Imenti Central": 45, "Imenti North": 46, "Imenti South": 47, "Tigania East": 48, "Tigania West": 49,
             "Buuri": 50, "Igembe Central": 51, "Igembe North": 52, "Igembe South": 53},
    "Kilifi": {"Kilifi North": 54, "Kilifi South": 55, "Malindi": 56, "Magarini": 57, "Ganze": 58, "Rabai": 59, "Kaloleni": 60},
    "Mombasa": {"Mvita": 61, "Kisauni": 62, "Changamwe": 63, "Likoni": 64, "Jomvu": 65, "Nyali": 66},
    "Nairobi": {"Dagoretti North": 67, "Dagoretti South": 68, "Embakasi Central": 69, "Embakasi East": 70, "Embakasi North": 71,
                "Embakasi South": 72, "Embakasi West": 73, "Kamukunji": 74, "Kasarani": 75, "Lang'ata": 76,
                "Westlands": 77, "Kibra": 78, "Makadara": 79, "Mathare": 80, "Ruaraka": 81, "Starehe": 82, "Roysambu": 83}
}

# Mapping site_name to county and sub-county
real_sites = {
    # Makueni
    "Makueni County Referral Hospital": ("Makueni", "Makueni"),
    "Kibwezi Sub-County Hospital": ("Makueni", "Kibwezi East"),
    "Kilungu Sub-County Hospital": ("Makueni", "Kaiti"),
    "Makindu Sub-County Hospital": ("Makueni", "Kibwezi West"),
    "Sultan Hamud Health Centre": ("Makueni", "Kilome"),
    "Wote Health Centre": ("Makueni", "Makueni"),
    "Matiliku Health Centre": ("Makueni", "Makueni"),
    "Kambu Health Centre": ("Makueni", "Kibwezi East"),
    "Kathonzweni Health Centre": ("Makueni", "Makueni"),
    "Emali Model Health Centre": ("Makueni", "Kibwezi West"),
    # Nyeri
    "Nyeri County Referral Hospital": ("Nyeri", "Nyeri Town"),
    "Karatina Sub-County Hospital": ("Nyeri", "Mathira East"),
    "Othaya Sub-County Hospital": ("Nyeri", "Nyeri Town"),
    "Mukurweini Sub-County Hospital": ("Nyeri", "Mukurweini"),
    "Naromoru Health Centre": ("Nyeri", "Kieni East"),
    "Tumutumu PCEA Hospital": ("Nyeri", "Mathira West"),
    "Wamagana Health Centre": ("Nyeri", "Tetu"),
    "Gichiche Health Centre": ("Nyeri", "Nyeri Town"),
    "Chaka Health Centre": ("Nyeri", "Kieni East"),
    "Mweiga Health Centre": ("Nyeri", "Kieni West"),
    # Kakamega
    "Kakamega County Referral Hospital": ("Kakamega", "Lurambi"),
    "Butere Sub-County Hospital": ("Kakamega", "Butere"),
    "Mumias County Hospital": ("Kakamega", "Mumias West"),
    "Malava Sub-County Hospital": ("Kakamega", "Malava"),
    "Mautuma County Hospital": ("Kakamega", "Lugari"),
    "Khwisero Sub-County Hospital": ("Kakamega", "Khwisero"),
    "Matungu Sub-County Hospital": ("Kakamega", "Matungu"),
    "Navakholo Sub-County Hospital": ("Kakamega", "Navakholo"),
    "Likuyani Sub-County Hospital": ("Kakamega", "Likuyani"),
    "Sheywe Community Hospital Limited": ("Kakamega", "Shinyalu"),
    # Nakuru
    "Nakuru Level 5 Hospital": ("Nakuru", "Nakuru Town West"),
    "Naivasha Sub-County Hospital": ("Nakuru", "Naivasha"),
    "Molo Sub-County Hospital": ("Nakuru", "Molo"),
    "Gilgil Sub-County Hospital": ("Nakuru", "Gilgil"),
    "Bahati Sub-County Hospital": ("Nakuru", "Bahati"),
    "Subukia Sub-County Hospital": ("Nakuru", "Subukia"),
    "Keringet Sub County Hospital": ("Nakuru", "Kuresoi South"),
    "Elburgon Sub-County Hospital": ("Nakuru", "Molo"),
    "Njoro Sub-County Hospital": ("Nakuru", "Njoro"),
    "Rongai Health Centre": ("Nakuru", "Rongai"),
    # Nyandarua
    "JM Kariuki Memorial Hospital": ("Nyandarua", "Ol Kalou"),
    "Engineer Sub-County Hospital": ("Nyandarua", "Kinangop"),
    "Ndaragwa Health Centre": ("Nyandarua", "Ndaragwa"),
    "Mirangine Health Centre": ("Nyandarua", "Ol Kalou"),
    "Kimathi Dispensary-Kipipiri Sub County": ("Nyandarua", "Kipipiri"),
    "Ol Joro Orok Medical Clinic": ("Nyandarua", "Ol Joro Orok"),
    "Amani Medical Clinic": ("Nyandarua", "Kinangop"),
    "Wanjohi Health Centre": ("Nyandarua", "Kipipiri"),
    "Shamata Health Centre": ("Nyandarua", "Ndaragwa"),
    "Leshau Pondo Health Centre": ("Nyandarua", "Ndaragwa"),
    # Nairobi
    "Kenyatta National Hospital": ("Nairobi", "Kibra"),
    "Mama Lucy Kibaki Hospital": ("Nairobi", "Embakasi Central"),
    "Mbagathi County Referral Hospital": ("Nairobi", "Kibra"),
    "Pumwani Maternity Hospital": ("Nairobi", "Kamukunji"),
    "Dagoretti Sub-County Hospital Mutuini": ("Nairobi", "Dagoretti South"),
    "Kangemi Health Centre": ("Nairobi", "Westlands"),
    "Riruta Health Centre": ("Nairobi", "Dagoretti North"),
    "Kayole II Sub County Hospital": ("Nairobi", "Embakasi Central"),
    "Kasarani Health Centre": ("Nairobi", "Kasarani"),
    "Dandora II Health Centre": ("Nairobi", "Embakasi North"),
    # Mombasa
    "Coast General Teaching and Referral Hospital Vikwatani Outreach Centre": ("Mombasa", "Kisauni"),
    "Port Reitz Sub-County Hospital": ("Mombasa", "Changamwe"),
    "Tudor District Hospital": ("Mombasa", "Mvita"),
    "Magongo (MCM) Dispensary": ("Mombasa", "Changamwe"),
    "Likoni Sub-County Hospital": ("Mombasa", "Likoni"),
    "Jomvu Model Health Centre": ("Mombasa", "Jomvu"),
    "Kisauni Health Centre": ("Mombasa", "Nyali"),
    "Bamburi Dispensary": ("Mombasa", "Nyali"),
    "Coast General Teaching Refferal Hospital - Mtongwe Outreach Centre": ("Mombasa", "Likoni"),
    "Diani Beach Hospital Limited - Shika Adabu": ("Mombasa", "Jomvu"),
    "Mikindani Medical Clinic": ("Mombasa", "Jomvu"),
    # Kilifi
    "Kilifi County Hospital": ("Kilifi", "Kilifi North"),
    "Malindi Sub-County Hospital": ("Kilifi", "Malindi"),
    "Mariakani Sub-County Hospital": ("Kilifi", "Kaloleni"),
    "Rabai Sub County Hospital": ("Kilifi", "Rabai"),
    "Ganze Health Centre": ("Kilifi", "Ganze"),
    "Bamba Sub County Hospital": ("Kilifi", "Ganze"),
    "Mtwapa Sub County Hospital": ("Kilifi", "Kilifi South"),
    "Chasimba Health Centre": ("Kilifi", "Kilifi South"),
    "Vipingo Rural Demonstration Health Centre": ("Kilifi", "Kilifi South"),
    "Matsangoni Model Health Centre": ("Kilifi", "Kilifi North"),
    # Meru
    "Meru Teaching & Referral Hospital": ("Meru", "Imenti North"),
    "Consolata Mission Hospital Nkubu": ("Meru", "Imenti South"),
    "Maua Methodist Hospital": ("Meru", "Igembe South"),
    "Muthara Sub-District Hospital": ("Meru", "Tigania East"),
    "Miathene Sub-County Hospital": ("Meru", "Tigania West"),
    "Laare Health Centre": ("Meru", "Igembe North"),
    "Kanyakine Sub County Hospital": ("Meru", "Imenti South"),
    "Kangeta Sub County Hospital": ("Meru", "Igembe Central"),
    "Timau Sub-County Hospital": ("Meru", "Buuri West"),
    "Gatimbi Health Centre": ("Meru", "Imenti Central"),
}

site_types = ['Dispensary', 'Health Centre', 'Hospital', 'Sub-County Hospital', 'County Referral Hospital']
user_roles = ['CHV', 'Nurse', 'Doctor', 'Data Officer', 'Lab Technician', 'Pharmacist']

def get_organization(site_name):
    """Determine organization based on site name patterns"""
    if "County Referral Hospital" in site_name or "Sub-County" in site_name or "Health Centre" in site_name:
        return "Ministry of Health"
    elif "PCEA" in site_name or "Methodist" in site_name or "Consolata" in site_name:
        return "Faith-Based Organization"
    elif "Medical Clinic" in site_name or "Dispensary" in site_name:
        return "Private Practice"
    elif "Diani Beach Hospital" in site_name:
        return "Private Hospital"
    else:
        return "Ministry of Health"

def generate_sites():
    """Generate site data matching the Site model"""
    sites = []
    # site_ids = []
    
    # Generate sequential site_ids starting from 1
    site_id = 1
    
    for site_name, (county_name, sub_county_name) in real_sites.items():
        # Get IDs from mappings
        county_id = county_mapping.get(county_name, 0)
        sub_county_id = sub_county_mapping.get(county_name, {}).get(sub_county_name, 0)
        
        # Determine site type from name
        site_type = next((t for t in site_types if t in site_name), "Health Centre")
        
        # Generate site data matching the Site model
        # Generate consistent coordinates based on site_name hash
        coord_hash = hash(site_name)
        latitude = -1.0 + (coord_hash % 2000) / 10000.0  # Kenya-appropriate range
        longitude = 36.5 + (coord_hash % 2000) / 10000.0  # Kenya-appropriate range
        # latitude = fake.latitude()
        # longitude = fake.longitude()
        is_active = random.choice([True, False])

        sites.append({
            "site_id": site_id,
            "name": site_name,
            "site_type": site_type,
            "county_id": county_id,
            "sub_county_id": sub_county_id,
            "latitude": latitude,
            "longitude": longitude,
            "is_active": is_active
        })
        site_id += 1
    
    # return pd.DataFrame(sites)
    df_sites = pd.DataFrame(sites)
    df_sites.to_csv(SITE_CSV_PATH, index=False)
    return df_sites

def generate_users(sites_df, n_users=240):
    """Generate user data matching the User model"""
    users = []

    # Mapping from site_id to name
    site_id_to_name = {row['site_id']: row['name'] for _, row in sites_df.iterrows()}

    site_ids = list(site_id_to_name.keys())
    
    # Role distribution weights
    role_distribution = ['CHV']*4 + ['Nurse']*3 + ['Doctor', 'Data Officer', 'Lab Technician', 'Pharmacist']
    # Generate sequential user ids starting from 1
    user_id = 1
    
    for _ in range(n_users):
        name = fake.name()
        # Create email by:
        # 1. Lowercasing the name
        # 2. Replacing spaces with nothing
        # 3. Adding @gmail.com
        email = name.lower().replace(" ", "") + "@gmail.com"
        password = fake.password()
        role = role_distribution[user_id % len(role_distribution)]
        site_id = random.choice(site_ids)
        # organization = get_organization(site_id_to_name[site_id])
        organization = get_organization(sites_df.loc[sites_df['site_id'] == site_ids[user_id % len(site_ids)], 'name'].iloc[0])
        is_active = random.choice([True, False])
        
        users.append({
            "id": user_id,
            "name": name,
            "email": email,
            "password": password,
            "role": role,
            "organisation": organization,
            "site_id": site_id,
            "is_active": is_active
        })
        user_id += 1
    
    # return pd.DataFrame(users)
    df_users = pd.DataFrame(users)
    df_users.to_csv(USER_CSV_PATH, index=False)
    return df_users

def generate_site_user_data(n_users_per_site=3):
    """Generate site and user data as DataFrames
    
    Args:
        n_users_per_site: Number of users to generate per site
        
    Returns:
        tuple: (sites_df, users_df) pandas DataFrames
    """
    sites_df = generate_sites()
    total_users = len(sites_df) * n_users_per_site
    users_df = generate_users(sites_df, total_users)    
    return sites_df, users_df

# Generate the data
sites_df, users_df = generate_site_user_data(n_users_per_site=3)

def calculate_active_summary(sites_df: pd.DataFrame, users_df: pd.DataFrame):
    total_sites = len(sites_df)
    active_sites = sites_df["is_active"].sum()
    inactive_sites = total_sites - active_sites

    total_users = len(users_df)
    active_users = users_df["is_active"].sum()
    inactive_users = total_users - active_users

    print("Site Summary:")
    print(f"  Total Sites: {total_sites}")
    print(f"  Active Sites: {active_sites}")
    print(f"  Inactive Sites: {inactive_sites}\n")

    print("User Summary:")
    print(f"  Total Users: {total_users}")
    print(f"  Active Users: {active_users}")
    print(f"  Inactive Users: {inactive_users}")


# # Example usage
# print(f"✅ Generated {len(sites_df)} sites and {len(users_df)} users")
# print("\nSites DataFrame Sample:")
# print(sites_df.head(3))
# print("\nUsers DataFrame Sample:")
# print(users_df.head(5))

# def generate_site_user_data(n_users=100):   
#     """Generate site and user data"""
#     sites = generate_sites()
#     site_ids = sites['site_id'].tolist()
    
#     users = generate_users(site_ids, sites, n_users)
    
#     return sites, users

# # Generate the data
# sites_df = generate_sites()
# users_df = generate_users(sites_df)

# # Example usage similar to your bp_logs example:
# print(f"✅ Generated {len(sites_df)} sites and {len(users_df)} users")
# print("\nSites DataFrame:")
# print(sites_df.head())
# print("\nUsers DataFrame:")
# print(users_df.head())
