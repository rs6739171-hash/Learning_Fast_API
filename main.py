from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, field_validator, computed_field, Field, EmailStr
import json

app = FastAPI()

class Student(BaseModel):
    id      : str = Field(..., examples=["S001"])
    name    : str = Field(..., min_length=2,max_length=50)
    age     : int = Field(...,gt=1,le=100)
    course  : str = Field(...,max_length=50)
    marks   : int = Field(...,ge=0,le=100)
    email   : EmailStr

    # Custom rules name must contain only letters and spaces
    @field_validator("name")
    @classmethod
    def check_name(cls,value):
        if not value.replace(" ","").isalpha():
            raise ValueError("Name must contains only letters and spaces")

        return value.title()

    @computed_field
    @property
    def grade(self):
        if self.marks >=90:
            return "A+"

        elif self.marks >=80:
            return "A"

        elif self.marks >= 70:
            return "B"
        
        elif self.marks >=60:
            return "C"

        else:
            return "F"

@app.post('/create', status_code = 201)
def create_student(student:Student):
    pass