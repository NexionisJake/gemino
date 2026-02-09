import os

class Config:
    # SECURE: Credentials fetched from environment variables
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    REGION = "us-west-2"