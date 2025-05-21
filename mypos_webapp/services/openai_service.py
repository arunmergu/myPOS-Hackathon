import openai
from flask import current_app



def generate_sales_insight(question, sales_data):
    """
    Generate insights about sales data based on user questions using OpenAI
    """
    openai.api_key = current_app.config['OPENAI_API_KEY']
    
    # Convert sales data to a string context
    context = f"""
    Sales data for the past {len(sales_data['months'])} months:
    
    Months: {', '.join(sales_data['months'])}
    Revenue: {sales_data['actual_revenue']}
    Projected Revenue: {sales_data['projected_revenue']}
    Transactions: {sales_data['transactions']}
    Average Transaction Values: {sales_data['avg_values']}
    Monthly Growth Rates: {sales_data['growth']}
    
    Total Revenue: £{sales_data['total_revenue']}
    Average Monthly Revenue: £{sales_data['avg_monthly_revenue']}
    Current Month Revenue: £{sales_data['current_month_revenue']}
    Previous Month Revenue: £{sales_data['previous_month_revenue']}
    Monthly Change: {sales_data['monthly_change']}%
    
    Top Products:
    """
    
    for product in sales_data['top_products']:
        context += f"- {product['name']}: £{product['revenue']}, Growth: {product['growth']}%\n"
    
    prompt = f"""
    You are a sales analytics assistant helping a merchant understand their sales data.
    Answer the following question based on the sales data provided. Be concise and specific.
    If you can't answer the question based on the data, say so.
    
    Sales Data:
    {context}
    
    Question: {question}
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful sales analytics assistant. Provide concise, specific insights based only on the provided data."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        current_app.logger.error(f"OpenAI API error in sales insights: {str(e)}")
        return f"I'm unable to process that question right now. Please try again later."

def generate_quotation(product_type, description, budget=0):
    """
    Generate a professional quotation using OpenAI API with precise tabular format
    """
    openai.api_key = current_app.config['OPENAI_API_KEY']
    
    prompt = f"""
    Generate a professional quotation for the following:
    Product/Service Type: {product_type}
    Description: {description}
    
    The quotation should have the following format:
    
    1. A brief professional introduction (2-3 sentences maximum)
    
    2. A precise tabular breakdown of services and costs in this format:
       | Service/Item | Description | Estimated Cost |
       | ------------ | ----------- | -------------- |
       | [Service 1]  | [Brief description] | €X |
       | [Service 2]  | [Brief description] | €X |
       | [Service 3]  | [Brief description] | €X |
       | Total        |               | €TOTAL |
    
    3. A brief timeline for delivery (1-2 sentences)
    
    4. A brief closing note (1-2 sentences)
    
    IMPORTANT: 
    - Do not use placeholders like [Client's Name] or [Your Name]
    - Create realistic, market-appropriate cost estimates for each service
    - Make sure the table is properly formatted with markdown syntax
    - The services should be specific to the type of work requested
    - Include 3-5 service line items that would be typical for this type of work
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional quotation generator assistant that creates precise, tabular quotations with specific service items and costs. You format your response with proper markdown tables and structure."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        current_app.logger.error(f"OpenAI API error: {str(e)}")
        return f"Error generating quotation: {str(e)}"