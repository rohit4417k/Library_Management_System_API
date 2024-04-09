import os

import bson.errors
from fastapi import FastAPI, HTTPException, Response
from pymongo import MongoClient, errors
from fastapi.responses import JSONResponse
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client = MongoClient(os.environ.get("MONGO_URL"))
print(os.environ.get("MONGO_URL"))
db = client['LibraryManagementSystem']

schema_validation = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "age", "address"],
        "properties": {
            "name": {
                "bsonType": "string"
            },
            "age": {
                "bsonType": "int",
                "minimum": 0
            },
            "address": {
                "bsonType": "object",
                "required": ["city", "country"],
                "properties": {
                    "city": {"bsonType": "string"},
                    "country": {"bsonType": "string"}
                }
            }
        }
    }
}

collection = db['students_data']


@app.get("/students")
async def root(country: str = None, age: int = None):
    query = {}
    if country:
        query["address.country"] = country
    if age:
        query["age"] = {"$gte": age}

    docs = collection.find(query, {"_id": 0, "address": 0})
    students = [student for student in docs]

    return JSONResponse(content={"data": students}, status_code=200)


@app.post("/students")
async def create_student(student_data: dict):
    required_fields = ['name', 'age', 'address']
    for field in required_fields:
        if field not in student_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    if 'address' in student_data:
        required_address_fields = ['city', 'country']
        for field in required_address_fields:
            if field not in student_data['address']:
                raise HTTPException(status_code=400, detail=f"Missing required address field: {field}")

    try:
        result = collection.insert_one(student_data)
        inserted_id = str(result.inserted_id)
        return JSONResponse(status_code=201, content={"id": inserted_id})
    except errors.WriteError as e:
        e = {
            "msg": e.details.get('errmsg'),
            "info": e.details.get('errInfo').get('details').get('schemaRulesNotSatisfied')[0]
        }

        raise HTTPException(status_code=400, detail=e)


@app.get("/students/{student_id}")
async def get_student_by_id(student_id: str):
    try:
        student_id_obj = ObjectId(student_id)
        student = collection.find_one({"_id": student_id_obj}, {"_id": 0})

        if student is None:
            raise HTTPException(status_code=404, detail="Student not found!")

        return JSONResponse(status_code=200, content=student)
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail="Student_id is invalid!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/students/{student_id}")
async def update_student(student_id: str, student_data: dict):
    try:
        student_id_obj = ObjectId(student_id)
        result = collection.update_one({"_id": student_id_obj}, {"$set": student_data})

        return Response(status_code=204)
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail="Student_id is invalid!")
    except errors.WriteError as e:
        e = {
            "msg": e.details.get('errmsg'),
            "info": e.details.get('errInfo').get('details').get('schemaRulesNotSatisfied')[0]
        }
        raise HTTPException(status_code=400, detail=e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/students/{student_id}")
async def delete_student(student_id: str):
    try:
        student_id_obj = ObjectId(student_id)
        result = collection.delete_one({"_id": student_id_obj})

        return Response(status_code=200)
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail="Student_id is invalid!")
    except Exception as e:
        # Handle invalid ObjectId error
        raise HTTPException(status_code=500, detail=str(e))



