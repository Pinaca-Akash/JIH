from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from typing import List, Optional
import math
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from typing import List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import json
import math
import numpy as np
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

client = AsyncIOMotorClient('mongodb://localhost:27017')
db = client["JIH"]
db2 = client["JIH_Profiles"]

db3 = client["Cases"]
Profiles_collection = db3["Combine"]


collections = {
    "jamaateislamihind": db["jamaateislamihind"],
    "JIH_Goa": db["JIH_Goa"],
    "JIH_Haharashtra": db["JIH_Maharashtra"],
    "JIHMaharashtra_Youtube": db["JIHMaharashtra_Youtube"],
    "JIH_karnataka": db["JIH_karnataka"],
    "JIH_West_Bengal": db["JIH_West_Bengal"],
    "JIH_Bihar": db["JIH_Bihar"],
    "sio-india": db["sio-india"],
    "sbfindia": db["sbfindia"],
    "hwfindia": db["hwfindia"],
    "JIH_markazitaleemiboardindia_Youtube": db["JIH_markazitaleemiboardindia_Youtube"],
    "JIH_Kerala_Andaman": db["JIH_Kerala_Andaman"],
    "JIH_hTamil_Puducherry": db["JIH_hTamil_Puducherry"],
    "JIH_Madhya_Pradesh": db["JIH_Madhya_Pradesh"],
    "JIH_Rajasthan": db["JIH_Rajasthan"],
    "JIHTelangana_youtube_youtube": db["JIHTelangana_youtube_youtube"]
}


collections2 = {
    "JIH_Madhya_Pradesh_Profile": db2["JIH_Madhya_Pradesh_Profile"],
    "JIH_Bihar": db2["JIH_Bihar"],
    "JIH_Tamil_Nadu": db2["JIH_Tamil_Nadu"],
    "JIH_Maharashtra_Profile": db2["JIH_Maharashtra_Profile"],
    "JIH_Rajasthan": db2["JIH_Rajasthan"]
    
}

def basename_filter(value: str) -> str:
    return os.path.basename(value)

templates.env.filters['basename'] = basename_filter


def objectid_converter(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError("Type not serializable")

class Card(BaseModel):
    date: str
    heading: str
    content: str
    picture: List[str]  
    video_source: Optional[str]  

class ProfileCard(BaseModel):
    name: str
    position: str
    about: str
    source: str
    part: str
    description: str 
    picture: List[str] 

class CaseCard(BaseModel):
    name: str
    Alias:str
    Gender:str
    DateBirth:str
    Age:str
    Nationality:str
    ContactNumber:str
    EmailId:str
    Marital_Status:str
    cdr: List[str]
    ipdr: List[str]
    case_files: List[str]
    picture: Optional[str]
    Facebook: Optional[str]
    Instagram:Optional[str]
    Twitter:Optional[str]


async def get_data_from_mongo():
    data = []
    for collection_name, collection in collections.items():
        cursor = collection.find()
        async for document in cursor:
            picture = document.get("Picture", [])
            if isinstance(picture, str):
                picture = [picture]  
            elif isinstance(picture, float) and math.isnan(picture):
                picture = [] 

            video_source = document.get("Video", "")
            if isinstance(video_source, list):
                video_source = video_source[0] if video_source else ""  
            elif isinstance(video_source, float) and math.isnan(video_source):
                video_source = ""  
            content = document.get("Content", "")
            if isinstance(content, float) and math.isnan(content):
                content = ""  
            elif not isinstance(content, str):
                content = str(content)  

            card = Card(
                date = document["Date"] if "Date" in document else "NAN",
                heading=document["Heading"],
                content=content,  
                picture=picture,  
                video_source=video_source  
            )
            data.append(card)
    
    return data
  
async def get_cases_from_mongo():
    cases = []
    cursor = Profiles_collection.find()
    async for document in cursor:
        case = CaseCard(
            name=document.get("Name", "NAN"),
            Alias=document.get("Alias","NAN"),
            Gender=document.get("Gender","NAN"),
            DateBirth=document.get("Date of Birth","NAN"),
            Age=document.get("Age","NAN"),
            Nationality=document.get("Nationality","NAN"),
            ContactNumber=document.get("Contact Number","NAN"),
            EmailId=document.get("Email ID","NAN"),
            Marital_Status=document.get("Marital Status","NAN"),
            cdr=document.get("CDR", []),
            ipdr=document.get("IPDR", []),
            case_files=document.get("Case Files", []),
            picture=document.get("Picture", ""),
            Facebook=document.get("Facebook ", "NAN"),
            Instagram=document.get("Instagram", "NAN"),
            Twitter=document.get("Twitter", "NAN")
        )

        cases.append(case)
    return cases

def sanitize_field(value, field_name=""):
    if field_name == "Picture":
        if isinstance(value, str) and value == "":
            return []  
        elif isinstance(value, float) and math.isnan(value):
            return []  
        elif isinstance(value, list):
            return value  
        else:
            return []  
    elif isinstance(value, str):
        return value
    elif isinstance(value, float) and math.isnan(value):
        return ""  
    else:
        return str(value) if value is not None else "" 

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, query: str = '', page: int = 1):
    data = await get_data_from_mongo()
    
    if query:
        data = [card for card in data if query.lower() in card.heading.lower() or query.lower() in card.content.lower()]

    total_documents = len(data)

    items_per_page = 10
    total_pages = math.ceil(total_documents / items_per_page)

    page = max(1, min(page, total_pages))

    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    paginated_data = data[start_index:end_index]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "cards": paginated_data,
        "search_query": query,
        "total_documents": total_documents,
        "page": page,
        "total_pages": total_pages
    })


@app.get("/profiles", response_class=HTMLResponse)
async def read_profiles(request: Request, query: str = '', page: int = 1):
    profiles_list = []

    for collection_name, collection in collections2.items():
        profiles_cursor = collection.find()

        async for profile in profiles_cursor:
            name = sanitize_field(profile.get("Name"))
            position = sanitize_field(profile.get("Position"))
            about = sanitize_field(profile.get("About"))
            source = sanitize_field(profile.get("Source"))
            part = sanitize_field(profile.get("Part"))
            picture = sanitize_field(profile.get("Picture", []), field_name="Picture")  
            description = sanitize_field(profile.get("Description", "NAN"))  

            profile_card = ProfileCard(
                name=name,
                position=position,
                about=about,
                source=source,
                part=part,
                picture=picture, 
                description=description 
            )
            profiles_list.append(profile_card)

    if query:
        profiles_list = [profile for profile in profiles_list if query.lower() in profile.name.lower() or query.lower() in profile.about.lower()]

    total_profiles = len(profiles_list)
    items_per_page = 10
    total_pages = math.ceil(total_profiles / items_per_page)

    page = max(1, min(page, total_pages))
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    paginated_profiles = profiles_list[start_index:end_index]

    return templates.TemplateResponse("profiles_dashboard.html", {
        "request": request,
        "profiles": paginated_profiles,
        "search_query": query,
        "total_profiles": total_profiles,
        "page": page,
        "total_pages": total_pages
    })


@app.get("/cases", response_class=HTMLResponse)
async def read_cases(request: Request, query: str = '', page: int = 1):
    cases_list = await get_cases_from_mongo()

    network_graph_data = await get_network_graph_data(query)

    if query:
        cases_list = [case for case in cases_list if query.lower() in case.name.lower()]

    total_cases = len(cases_list)
    items_per_page = 1
    total_pages = (total_cases // items_per_page) + (1 if total_cases % items_per_page != 0 else 0)

    page = max(1, min(page, total_pages))
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    paginated_cases = cases_list[start_index:end_index]

    return templates.TemplateResponse("cases_dashboard.html", {
        "request": request,
        "cases": paginated_cases,
        "network_graph_data": network_graph_data,
        "search_query": query,
        "total_cases": total_cases,
        "page": page,
        "total_pages": total_pages
    })


async def get_network_graph_data(query: str):
    cursor = Profiles_collection.find()
    documents = await cursor.to_list(length=None)

    graph_data_list = []

    for doc in documents:
        if query.lower() in doc.get("Name", "").lower():
            nodes = []
            edges = []

            name = doc.get("Name", "Unknown")
            nodes.append({
                "id": name,
                "label": f"Name: {name}",
                "shape": "box",
                "size": 50,
                "font": {"size": 14, "color": "#FFFFFF"},
                "color": "#4CAF50",
                "borderWidth": 3,
            })

            for key, value in doc.items():
                if key == "Name":
                    continue

                if value in [np.nan, None]:
                    continue 

                if isinstance(value, str) and value.strip() and key != "Picture" and key != "Instagram" and key!= "Facebook " and key!= "Alias" and key!="Gender" and key!="Date of Birth" and key!="Age" and key!="Nationality" and key!="Contact Number" and key!="Marital Status" and key!="Email ID":
                    node_label = f"{key}: {value}"
                    node_id = f"{key}_{value[:10]}"
                    
                    nodes.append({
                        "id": node_id,
                        "label": node_label,
                        "shape": "box",
                        "size": 40,
                        "font": {"size": 12, "color": "#FFFFFF"},
                        "color": "#4CAF50",
                        "borderWidth": 3,
                    })
                    
                    edges.append({"from": name, "to": node_id})

                elif isinstance(value, list):
                    for idx, item in enumerate(value):
                        if item.strip() and key != "Picture":
                            node_id = f"{key}_{idx}"
                            nodes.append({
                                "id": node_id,
                                "label": f"{key}: {item}",
                                "shape": "box",
                                "size": 40,
                                "font": {"size": 12, "color": "#FFFFFF"},
                                "color": "#4CAF50",
                                "borderWidth": 3,
                            })
                            edges.append({"from": name, "to": node_id})

            facebook_url = doc.get("Facebook ", "https://default-facebook-url.com")
            instagram_url = doc.get("Instagram", "https://default-instagram-url.com")
            Twitter_url = doc.get("Twitter", "https://default-twitter-url.com")
            
            nodes.append({
                "id": "Facebook",
                "label": "Facebook", 
                "shape": "box",
                "size": 40,
                "font": {"size": 12, "color": "#FFFFFF"},
                "color": "#4CAF50",
                "borderWidth": 3,
                "url": facebook_url  
            })
            nodes.append({
                "id": "Instagram",
                "label": "Instagram",  
                "shape": "box",
                "size": 40,
                "font": {"size": 12, "color": "#FFFFFF"},
                "color": "#4CAF50",
                "borderWidth": 3,
                "url": instagram_url  
            })
            nodes.append({
                "id": "Twitter",
                "label": "Twitter",  
                "shape": "box",
                "size": 40,
                "font": {"size": 12, "color": "#FFFFFF"},
                "color": "#4CAF50",
                "borderWidth": 3,
                "url": Twitter_url  
            })

            edges.append({"from": name, "to": "Facebook"})
            edges.append({"from": name, "to": "Instagram"})
            edges.append({"from": name, "to": "Twitter"})

            graph_data = {
                "nodes": nodes,
                "edges": edges
            }

            graph_data_list.append({
                "graph_data_json": json.dumps(graph_data, default=objectid_converter),
                "name": name,
                "facebook_url": facebook_url,
                "instagram_url": instagram_url
            })

    return graph_data_list
