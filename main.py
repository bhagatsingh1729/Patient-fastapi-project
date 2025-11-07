from fastapi import FastAPI,Path,HTTPException,Query
from fastapi.responses import JSONResponse
import json
from pydantic import BaseModel,Field,computed_field
from typing import Literal,Annotated, List # Added List for type hinting

# Initialize the application
app = FastAPI(title="Patient Management System API")

class Patient(BaseModel):
    id:Annotated[str,Field(...,description="Patient ID",examples=["P001"])]
    name:Annotated[str,Field(...,description="Name of the patient",examples=["Dev das"],max_length=50)]
    city:Annotated[str,Field(...,description="City of the patient")]
    age:Annotated[int,Field(...,description="Age of the patient",gt=0,lt=100)]
    gender:Annotated[Literal['male','female','other'],Field(...,description="Gender of the patient")]
    height:Annotated[float,Field(...,description="Height of the patient in meters")]
    weight:Annotated[float,Field(...,description="weight of the patient in kgs",gt=0)]

    @computed_field
    def bmi(self) -> float:
        """Calculates Body Mass Index (BMI)."""
        try:
            bmi_value = round(self.weight / (self.height**2), 2)
            return bmi_value
        except (ZeroDivisionError, TypeError):
            return 0.0
    
    @computed_field
    def verdict(self) -> str:
        """Provides a BMI classification verdict."""
        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'
        

def load_data():
    """Loads patient data from a JSON file."""
    try:
        with open('patients.json','r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("Error decoding patients.json. Starting with empty data.")
        return {}
    return data

def save_data(data):
    """Saves patient data to a JSON file."""
    try:
        with open("patients.json",'w') as f:
            json.dump(data,f, indent=4)
    except IOError as e:
        print(f"Error saving data to patients.json: {e}")

# --- API Endpoints ---

@app.get("/")
def Greeting():
    return {"message":"Patient Management System API"}

@app.get("/about")
def about():
    return {"detail":"Fully functional API to view Patient details"}

@app.get("/add")
def add(a:int=1,b:int=2) -> int:
    return a+b

@app.get("/view", response_model=List[Patient])
def view() -> List[Patient]:
    """Retrieves all patients, ensuring the schema includes computed fields."""
    data = load_data()
    
    # FIX: Convert raw JSON data to Pydantic models for explicit schema definition
    patients_list = []
    for patient_dict in data.values():
        # Ensure 'id' is present for Patient model instantiation
        if 'id' in patient_dict:
            patients_list.append(Patient(**patient_dict))
    
    return patients_list

@app.get("/patient/{patient_id}", response_model=Patient)
def view_patient(patient_id: str = Path(...,description="ID of patients",example="P001")) -> Patient:
    """Retrieves a single patient by ID."""
    data = load_data()

    if patient_id in data:
        # FIX: Explicitly convert the dict to a Patient model
        patient_data = data[patient_id]
        if 'id' not in patient_data:
            patient_data['id'] = patient_id # Ensure ID is set for model validation
            
        return Patient(**patient_data)
        
    raise HTTPException(status_code=404,detail="Patient not found")

@app.get("/sort", response_model=List[Patient])
def sort_data(sort_by : str = Query(...,description="sort by height, bmi, or weight"), order:str=Query('asc',description="sort by 'asc' or 'desc'")) -> List[Patient]:
    """Sorts patient data based on specified field."""
    valid_entries = ['height','bmi','weight']

    if sort_by not in valid_entries:
        raise HTTPException(status_code=400,detail=f"Invalid field: '{sort_by}'. Must be one of {', '.join(valid_entries)}")
    if order not in ['asc','desc']:
        raise HTTPException(status_code=400,detail="Order must be 'asc' or 'desc'")
    
    data = load_data()
    sort_order = True if order == 'desc' else False 

    # Sort the raw dictionary values
    sorted_data_dicts = sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=sort_order)

    # FIX: Convert sorted dictionaries to Pydantic models for consistent response schema
    sorted_patients = []
    for patient_dict in sorted_data_dicts:
        if 'id' in patient_dict:
            sorted_patients.append(Patient(**patient_dict))
            
    return sorted_patients

@app.post("/create", response_model=dict)
def create_patient(patient:Patient):
    # Load existing data
    data = load_data()

    # Check if the data already exist
    if patient.id in data:
        raise HTTPException(status_code=400,detail=f"Patient with ID {patient.id} already exists")
    
    # Store the patient data using ID as key (excluding computed fields from storage is often best)
    patient_data = patient.model_dump(exclude={'bmi', 'verdict'})
    
    data[patient.id] = patient_data

    save_data(data)

    return JSONResponse(status_code=201,content={"message":f"Patient successfully created with ID {patient.id}"})