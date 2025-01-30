import re
import os
import json
import streamlit as st
from collections import defaultdict
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

working_dir = os.path.dirname(os.path.abspath(__file__))
config_data = json.load(open(f"{working_dir}/config.json"))
API_KEY = config_data["openai_api_key"]
os.environ["openai_api_key"] = API_KEY
# Parse the markdown file and store data
def parse_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    data = defaultdict(lambda: defaultdict(list))  # {district: {taluka: [villages]}}
    current_district = None
    current_taluka = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('# '):  # District
            current_district = line[2:].strip()
            data[current_district] = defaultdict(list)
        elif line.startswith('## '):  # Taluka
            current_taluka = line[3:].strip()
            if current_district:
                data[current_district][current_taluka] = []
        elif line.startswith('- '):  # Village
            village = line[2:].strip()
            if current_district and current_taluka:
                data[current_district][current_taluka].append(village)
    
    return data

def search_village(data, query):
    query = query.lower().strip()
    for district, talukas in data.items():
        for taluka, villages in talukas.items():
            if query in (village.lower() for village in villages):
                return district, taluka
    return None, None  # Always return a tuple

# Load data once and keep it in memory
file_path = "data.md"  # Update this if the path is different
delhi_housing_data = parse_markdown(file_path)

# Set up LangChain prompt
llm = ChatOpenAI(temperature=0.7,openai_api_key=API_KEY)
prompt_template = PromptTemplate.from_template(
    "You are a helpful assistant that provides district and taluka information for villages in Delhi. Answer based on the provided dataset: {query}"
)

def get_response(query):
    district, taluka = search_village(delhi_housing_data, query)
    if district and taluka:
        return f"Village '{query}' is in Taluka '{taluka}', District '{district}'."
    return f"Sorry, I couldn't find a match for '{query}'."
# Streamlit UI
st.title("Delhi Housing Chatbot")
st.write("Enter a village name, and I'll tell you its Taluka and District!")

user_input = st.text_input("Enter a village name:")
if user_input:
    response = get_response(user_input)
    st.write(response)

# Run Streamlit with: `streamlit run stream.py`


