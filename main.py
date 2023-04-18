import os
from flask import Flask, request, redirect, url_for,render_template
import boto3
from werkzeug.utils import secure_filename
from io import BytesIO
from PyPDF2 import PdfReader
import uuid

app = Flask(__name__)
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return open('templates/home.html').read()

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['pdf_file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            pdf_content = read_pdf_content(file)
            upload_to_s3(file, filename)
            save_content_to_dynamodb(pdf_content)
            return 'File uploaded successfully'
    return redirect(url_for('home'))

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')
  

def read_pdf_content(file):
    content = ""
    file.seek(0) 
    with BytesIO(file.read()) as pdf_data:
        pdf_reader = PdfReader(pdf_data)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            content += page.extract_text()
    file.seek(0) 
    return content.lower()

def upload_to_s3(file, filename):
    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
    S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
    s3 = boto3.client('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)
    s3.upload_fileobj(file, S3_BUCKET, filename)

def save_content_to_dynamodb(content):
  # Create a Session object with your credentials
  session = boto3.Session(aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)
  # Initialize the DynamoDB client using the session
  dynamodb = session.resource('dynamodb', region_name='eu-north-1')
  
  # dynamodb = boto3.resource('dynamodb', region_name='eu-west-3')
  table = dynamodb.Table('aws-file-upload-test')

  item = {
      'id': str(uuid.uuid4()),
       'content': content
  }

  table.put_item(Item=item)
  

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
