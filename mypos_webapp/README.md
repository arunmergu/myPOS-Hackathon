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
DATABASE_URL=sqlite:///mypos_marketplace.db
OPENAI_API_KEY=your_openai_api_key_here
MYPOS_CLIENT_ID=your_mypos_client_id_here
MYPOS_CLIENT_SECRET=your_mypos_client_secret_here
MYPOS_MERCHANT_ID=your_mypos_merchant_id_here
MYPOS_OAUTH_API_URL=https://auth-api.mypos.com/oauth/token
MYPOS_TRANSACTION_API_URL=https://transactions-api.mypos.com/v1.1/online-payments/link

# Start the Application
python run.py

# Access the Application Open your browser and navigate to 
http://127.0.0.1:5001
