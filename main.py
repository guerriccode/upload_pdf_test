import os
from flask import Flask, request, redirect, url_for,render_template,jsonify
import boto3
from boto3.dynamodb.conditions import Attr

from werkzeug.utils import secure_filename
from io import BytesIO
from PyPDF2 import PdfReader
import uuid
import openai

app = Flask(__name__)
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')

MY_API_KEY = os.environ['MY_API_KEY']
openai.api_key = os.environ.get('OPENAI_API_KEY', MY_API_KEY)
session = boto3.Session(aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)
# Initialize the DynamoDB client using the session
dynamodb = session.resource('dynamodb', region_name='eu-north-1')
# dynamodb = boto3.resource('dynamodb', region_name='eu-west-3')
table = dynamodb.Table('aws-file-upload-test')

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
  
@app.route('/ask', methods=['POST'])
def ask():
  user_input = request.form['user_input']

  # Scan DynamoDB for a relevant answer
  response = table.scan(
        FilterExpression=Attr('content').contains(user_input.lower())
    )
  if response['Count']>0:
  # if True:
    content_from_db = response['Items'][0]['content']
    # content_from_db="Meet Mr Monkey, a fun-loving character full of surprises! He loves bananas, and eats at least two every day. Mr Monkey has a pet parrot named Polly, who he talks to in monkey language. He's a great dancer and loves to move to the rhythm of reggae music, especially Bob Marley's songs. Mr Monkey has a collection of over 100 different types of hats, from baseball caps to top hats. Once, he won a hotdog eating contest by devouring 25 hotdogs in under 10 minutes! Mr Monkey is also an excellent climber and can scale a tree faster than most monkeys in the jungle. However, he has a fear of spiders and will scream if he sees one. He's a mischievous monkey who loves to play pranks on his friends, like putting a fake spider in his friend's bed. Mr Monkey is a big fan of martial arts movies and can imitate Bruce Lee's famous moves"
    chatbot_prompt = f"Answer this question: {user_input} using this content: {content_from_db}"
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=chatbot_prompt,
      max_tokens=100,
      n=1,
      stop=None,
      temperature=0.5,
    )
    chatbot_response = response.choices[0].text.strip()
  else:
    chatbot_response = "I do not have this information"
  #chatbot_response = 'Sample chatbot response'
  return jsonify({'chatbot_response': chatbot_response})


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
