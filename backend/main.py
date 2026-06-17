from database import SessionLocal
from models import Upload
from database import engine
from database import SessionLocal
from models import Base
from models import Upload
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import FastAPI, UploadFile, File
import pandas as pd
import re
import os
from datetime import datetime

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Transaction Validation Platform API Running"
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    # Read uploaded file
    contents = await file.read()

    # Save uploaded file
    file_path = f"../uploads/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(contents)

    # Read CSV
    df = pd.read_csv(file_path)

    # Statistics
    total_rows = len(df)
    total_columns = len(df.columns)

    # Required fields
    required_columns = [
        "order_id",
        "customer_name",
        "phone_number",
        "country",
        "product_name",
        "payment_mode",
        "payment_status",
        "transaction_id"
    ]

    # Phone rules
    phone_rules = {
        "IN": {"prefix": "91", "length": 12},
        "SG": {"prefix": "65", "length": 10},
        "US": {"prefix": "1", "length": 11}
    }

    # Payment rules
    valid_payment_modes = [
        "CARD",
        "COD",
        "PAYPAL",
        "NETBANKING",
        "WALLET",
        "UPI"
    ]

    valid_payment_status = [
        "FAILED",
        "COMPLETED",
        "PENDING",
        "REFUNDED"
    ]

    valid_rows = 0
    invalid_rows = 0

    clean_data = []
    error_data = []

    seen_order_ids = set()

    # Validate rows
    for index, row in df.iterrows():

        is_valid = True
        error_message = ""

        if "order_id" in df.columns:

            order_id = str(
                row["order_id"]
            ).strip()

            print(
    "Row:",
    index,
    "Order ID:",
    order_id,
    "Seen:",
    seen_order_ids
)

            if order_id in seen_order_ids:
                is_valid = False
                error_message = "Duplicate Order ID"

            else:
                seen_order_ids.add(order_id)

        # Required field validation
        for column in required_columns:
            if pd.isna(row[column]):
                is_valid = False
                break

        # Phone validation
        if is_valid:

            country = str(row["country"]).strip().upper()

            phone = re.sub(
                r"\D",
                "",
                str(row["phone_number"])
            )

            if country in phone_rules:

                rule = phone_rules[country]

                if (
                    len(phone) != rule["length"]
                    or not phone.startswith(rule["prefix"])
                ):
                    is_valid = False

        # Date validation
        if is_valid:
            try:
                datetime.strptime(
                    str(row["order_date"]),
                    "%d-%m-%Y"
                )
            except ValueError:
                is_valid = False

# Time validation
        if (
            is_valid
            and "order_time" in df.columns
        ):

            try:

                datetime.strptime(
                    str(row["order_time"]),
                    "%H:%M:%S"
             )

            except ValueError:

                is_valid = False
                error_message = "Invalid Time"


        # Numeric validation
        if is_valid:
            try:
                quantity = int(row["quantity"])
                unit_price = float(row["unit_price"])
                amount_paid = float(row["amount_paid"])

                if quantity <= 0:
                    is_valid = False

                if unit_price <= 0:
                    is_valid = False

                if amount_paid < 0:
                    is_valid = False

            except (ValueError, TypeError):
                is_valid = False

        # Payment validation
        if is_valid:

            payment_mode = str(
                row["payment_mode"]
            ).strip().upper()

            payment_status = str(
                row["payment_status"]
            ).strip().upper()

            if payment_mode not in valid_payment_modes:
                is_valid = False

            if payment_status not in valid_payment_status:
                is_valid = False

        # Count rows
        if is_valid:
            valid_rows += 1
            clean_data.append(row.to_dict())

        else:
            invalid_rows += 1

            error_data.append({
    "row_number": index + 2,
    "order_id": row["order_id"],
    "error":
        error_message
        if error_message
        else "Validation Failed"
})

    # Create DataFrames
    clean_df = pd.DataFrame(clean_data)

    error_df = pd.DataFrame(
        error_data,
        columns=[
            "row_number",
            "order_id",
            "error"
        ]
    )

    # File paths
    clean_path = "../outputs/clean_transactions.csv"
    error_path = "../errors/validation_errors.csv"

    # Remove old files
    if os.path.exists(clean_path):
        os.remove(clean_path)

    if os.path.exists(error_path):
        os.remove(error_path)

    # Save fresh files
    clean_df.to_csv(
        clean_path,
        index=False
    )

    error_df.to_csv(
        error_path,
        index=False
    )

    chunk_folder = "../chunks"

    if not os.path.exists(chunk_folder):
        os.makedirs(chunk_folder)

    # Delete old chunk files
    for old_file in os.listdir(chunk_folder):

        file_path = os.path.join(
        chunk_folder,
        old_file
        
        )

        if os.path.isfile(file_path):
            os.remove(file_path)

    # Split large CSV into chunks
    chunk_size = 50

    for i in range(0, total_rows, chunk_size):

        chunk_df = df.iloc[i:i + chunk_size]

        chunk_number = (i // chunk_size) + 1

        chunk_df.to_csv(
            f"../chunks/chunk_{chunk_number}.csv",
            index=False
        )


    db = SessionLocal()

    new_upload = Upload(
        filename=file.filename,
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows
    )

    db.add(new_upload)
    db.commit()
    db.close()

    # Response
    return {

        "message": "File processed successfully",
        "filename": file.filename,
        "total_rows": total_rows,
        "total_columns": total_columns,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "clean_file": "outputs/clean_transactions.csv",
        "error_file": "errors/validation_errors.csv",
        "chunks_folder": "chunks/"
    }


@app.get("/download/clean")
def download_clean():
    return FileResponse(
        "../outputs/clean_transactions.csv",
        filename="clean_transactions.csv"
    )


@app.get("/download/error")
def download_error():
    return FileResponse(
        "../errors/validation_errors.csv",
        filename="validation_errors.csv"
    )

@app.get("/uploads")
def get_uploads():

    db = SessionLocal()

    uploads = db.query(Upload).all()

    result = []

    for upload in uploads:
        result.append({
            "id": upload.id,
            "filename": upload.filename,
            "total_rows": upload.total_rows,
            "valid_rows": upload.valid_rows,
            "invalid_rows": upload.invalid_rows,
            "uploaded_at": upload.uploaded_at
        })

    db.close()

    return result
@app.get("/chunks")
def get_chunks():

    import os

    chunk_folder = "../chunks"

    if not os.path.exists(chunk_folder):
        return []

    chunk_files = []

    for file in os.listdir(chunk_folder):

        if file.endswith(".csv"):
            chunk_files.append(file)

    return chunk_files
@app.get("/download/chunk/{filename}")
def download_chunk(filename: str):

    file_path = f"../chunks/{filename}"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/csv"
    )
