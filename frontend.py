import streamlit as st
import requests 
import pandas as pd
from main import load_data
st.title('FastApi frontend')
st.markdown("hello")
API_URL = "http://127.0.0.1:8000/create"

id = st.text_input("Enter Patient ID")
name = st.text_input("name:")
age = st.number_input("age")
weight = st.number_input("weight:")
height = st.number_input("height")
gender = st.text_input("Gender")
city = st.text_input("city")

if st.button('click'):
    input_data = {
        "id":id,
        "name":name,
        "age":age,
        "weight":weight,
        "height":height,
        "gender":gender,
        "city":city
    }
    response = requests.post(API_URL,json=input_data)
    res = response.json()
    if response.status_code == 201 or response.status_code == 200 and "response" in res:
        st.text("Success")
        data = load_data()
        df = pd.DataFrame(data)
        
        st.write(df)
        st.write(res)
        st.write(data)
    else:
        st.text("error")