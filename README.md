# myPOS-Hackathon
# Installation Steps

# Clone the Repository

git clone https://github.com/arun-arcinsights/mypos_webapp.git
cd mypos-marketplace

# Create and Activate Virtual Environment
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt

# Create Environment Variables check the .env file in the project root with the following # variables and make sure those values are correct:

SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///quotepro.db
OPENAI_API_KEY=
MYPOS_OAUTH_API_URL=https://demo-api-gateway.mypos.com/api/v1/oauth/token
MYPOS_SESSION_API_URL=https://demo-api-gateway.mypos.com/api/v1/auth/session
MYPOS_PAYMENT_API_URL=https://demo-api-gateway.mypos.com/ecommerce/v1/pr
MYPOS_TRANSACTION_API_LIST_URL=https://demo-api-gateway.mypos.com/accounting/v1/transaction/list

PARTNER_ID=mps-p-10000349
APP_ANALYTICS_APPLICATION_ID=mps-app-30000784
ECOMMERCE_APPLICATION_ID=mps-app-30000855

APP_ANALYTICS_PARTNER_CLIENT_ID=client_ac3804d69bb34da2968f6d79c06d0964
APP_ANALYTICS_PARTNER_CLIENT_SECRET=secret_4c66ca2eac27085224a7cc4362ad9cf24b538a61ee34931ca65a62136d551c73
APP_ANALYTICS_MERCHANT_CLIENT_ID=cli_ndoGG70MDFLHTIbRCuOvCrIgXkYa
APP_ANALYTICS_MERCHANT_CLIENT_SECRET=sec_MTBExsNjQ4zkLUfZFLkpXnOt22w0c7VHURKCI2pVwWQJ9UykLsjVTequ4bpw

ECOMMERCE_PARTNER_CLIENT_ID=client_991f7dea8e1c41b2814a21444fec38e0
ECOMMERCE_PARTNER_CLIENT_SECRET=secret_37a4e7b0387b4841b5e7afc7195c1a1c1d4b3d4044daac475d0dca6cdba9a6d4
ECOMMERCE_MERCHANT_CLIENT_ID=cli_gzJqlrniaP4mVaQrGwtEFbXLSfsz
ECOMMERCE_MERCHANT_CLIENT_SECRET=sec_Ys8JAiUqx5o12y5CkJXhwVTV6DaBL8EMJS2XFajqepIt9TKFvjhh8fhkxY17



# Start the Application
python run.py

# Access the Application Open your browser and navigate to 
http://127.0.0.1:5001
