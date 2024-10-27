from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import pandas as pd
import os
from datetime import datetime
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# This will store the last 10 bills in memory (replace with a database for persistence)


# Constants
MAIN_EXCEL_FILE = 'laundry_data_main.xlsx'
DAILY_FILES_FOLDER = 'daily_files'
MONTHLY_FILES_FOLDER = 'monthly_files'
STATUS_OPTIONS = ['Order Placed', 'Arrived at Plant', 'Washed', 'Ironed', 'Ready for Pick-Up', 'Arrived at Shop']
MAX_DAILY_FILES = 50
MAX_MONTHLY_FILES = 4

# Email configuration
FROM_EMAIL = "brightlaundrytnj@gmail.com"
TO_EMAIL = "raghulsrk.2812@gmail.com"
APP_PASSWORD = "wfqo osvn gphf mbok"  # Your App Password

# Global variable to store the current date
current_date = None

# Initialize Excel files
def initialize_excel():
    if not os.path.exists(MAIN_EXCEL_FILE):
        df = pd.DataFrame(columns=['Date', 'Reference Number', 'Customer Name', 'Phone Number', 'Branch', 'Cloth Type', 'Quantity', 'Total Price', 'Status', 'Timestamp'])
        df.to_excel(MAIN_EXCEL_FILE, index=False)
    if not os.path.exists(DAILY_FILES_FOLDER):
        os.makedirs(DAILY_FILES_FOLDER)
    if not os.path.exists(MONTHLY_FILES_FOLDER):
        os.makedirs(MONTHLY_FILES_FOLDER)

def get_today_excel_file(date_str=None):
    date_str = date_str or datetime.now().strftime('%Y-%m-%d')
    return os.path.join(DAILY_FILES_FOLDER, f'laundry_data_{date_str}.xlsx')

def get_monthly_excel_file(month_str=None):
    month_str = month_str or datetime.now().strftime('%Y-%m')
    return os.path.join(MONTHLY_FILES_FOLDER, f'laundry_data_{month_str}.xlsx')

# Email sending function
def send_email(file_path, from_email, to_email, app_password):
    """Send an email with the selected file attached."""
    subject = "Monthly Laundry Data Backup"
    body = "Please find the attached monthly laundry data backup file."

    msg = EmailMessage()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    with open(file_path, 'rb') as file:
        file_data = file.read()
        file_name = file.name
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(from_email, app_password)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def manage_old_files():
    daily_files = sorted([f for f in os.listdir(DAILY_FILES_FOLDER) if f.endswith('.xlsx')])
    if len(daily_files) > MAX_DAILY_FILES:
        oldest_file = os.path.join(DAILY_FILES_FOLDER, daily_files[0])
        os.remove(oldest_file)
    
    monthly_files = sorted([f for f in os.listdir(MONTHLY_FILES_FOLDER) if f.endswith('.xlsx')])
    if len(monthly_files) > MAX_MONTHLY_FILES:
        oldest_file = os.path.join(MONTHLY_FILES_FOLDER, monthly_files[0])
        send_email(
            file_path=oldest_file,
            from_email=FROM_EMAIL,
            to_email=TO_EMAIL,
            app_password=APP_PASSWORD
        )
        os.remove(oldest_file)

# Home page route
@app.route('/')
def home():
    return render_template('index1.html')

# Start the day route
@app.route('/start_day', methods=['POST'])
def start_day():
    global current_date
    location = request.form['location']
    date_str = request.form['date'] if location != 'plant' else None

    if location != 'plant' and not date_str:
        return "Error: Date is required for the Store option."

    current_date = date_str

    if location == 'store':
        today_excel_file = get_today_excel_file(current_date)
        if not os.path.exists(today_excel_file):
            df_today = pd.DataFrame(columns=['Reference Number', 'Customer Name', 'Phone Number', 'Branch', 'Cloth Type', 'Quantity', 'Total Price', 'Status', 'Timestamp'])
            df_today.to_excel(today_excel_file, index=False)
    
        manage_old_files()
    
        current_month = current_date[:7]
        monthly_excel_file = get_monthly_excel_file(current_month)
        if not os.path.exists(monthly_excel_file):
            df_monthly = pd.DataFrame(columns=['Date', 'Reference Number', 'Customer Name', 'Phone Number', 'Branch', 'Cloth Type', 'Quantity', 'Total Price', 'Status', 'Timestamp'])
            df_monthly.to_excel(monthly_excel_file, index=False)

        return redirect(url_for('order_page'))
    
    return redirect(url_for('manage_orders'))

@app.route('/order_page', methods=['GET', 'POST'])
def order_page():
    # Summary totals for all laundry services
    summary_totals = {
        'Ironing - Shirts & Pants': 0,
        'Ironing - Dhothi & Sarees': 0,
        'Laundry - Shirts & Pants': 0,
        'Laundry - Dhothi & Sarees': 0,
        'Washing & Folding Only': 0,
        'Starch Treatment - Shirts & Dhothis': 0,
        'Starch Treatment - Sarees': 0,
        'Dry Wash - Blazer/Coat': 0,
        'Dry Wash - Silk Dhothi & Shirt': 0,
        'Dry Wash - Silk Sarees': 0,
        'Double Bedsheet': 0,
        'Single Bedsheet': 0,
        'Double Blanket': 0,
        'Single Blanket': 0,
        'Carpet Washing': 0,
    }

    total_items = 0
    order_details = []  # Initialize as an empty list by default
    whatsapp_message = ""  # Placeholder for WhatsApp message

    # Assuming you're reading data from some file
    today_excel_file = get_today_excel_file(current_date)
    
    if os.path.exists(today_excel_file):
        df_today = pd.read_excel(today_excel_file)

        # Loop through the cloth types to calculate the total quantity for each service
        for cloth_type in summary_totals.keys():
            total_quantity = df_today[df_today['Cloth Type'] == cloth_type]['Quantity'].sum()
            summary_totals[cloth_type] = total_quantity
            total_items += total_quantity

        # Populate order_details only if there is data
        order_details = []
        for _, row in df_today.iterrows():
            order_details.append({
                'Cloth Type': row['Cloth Type'],
                'Quantity': row['Quantity'],
                'Price per Piece': row['Total Price'] // row['Quantity'] if row['Quantity'] > 0 else 0,
                'Total': row['Total Price']
            })

        # Generate WhatsApp message from the order details
        if order_details:
            whatsapp_message = "Hello, here is your order summary:\n"
            for detail in order_details:
                whatsapp_message += f"{detail['Cloth Type']}: {detail['Quantity']} x ₹{detail['Price per Piece']} = ₹{detail['Total']}\n"
            whatsapp_message += f"\nTotal Items: {total_items}\n"
            whatsapp_message += "Thank you for choosing our service!"

    # Render the template with both the summary totals and order details
    return render_template(
        'order.html',
        ironing_shirts_pants_total=summary_totals['Ironing - Shirts & Pants'],
        ironing_dhothi_sarees_total=summary_totals['Ironing - Dhothi & Sarees'],
        laundry_shirts_pants_total=summary_totals['Laundry - Shirts & Pants'],
        laundry_dhothi_sarees_total=summary_totals['Laundry - Dhothi & Sarees'],
        washing_folding_total=summary_totals['Washing & Folding Only'],
        starch_shirts_dhothis_total=summary_totals['Starch Treatment - Shirts & Dhothis'],
        starch_sarees_total=summary_totals['Starch Treatment - Sarees'],
        drywash_blazer_coat_total=summary_totals['Dry Wash - Blazer/Coat'],
        drywash_silk_dhothi_shirt_total=summary_totals['Dry Wash - Silk Dhothi & Shirt'],
        drywash_silk_sarees_total=summary_totals['Dry Wash - Silk Sarees'],
        double_bedsheet_total=summary_totals['Double Bedsheet'],
        single_bedsheet_total=summary_totals['Single Bedsheet'],
        double_blanket_total=summary_totals['Double Blanket'],
        single_blanket_total=summary_totals['Single Blanket'],
        carpet_washing_total=summary_totals['Carpet Washing'],
        total_items=total_items,
        order_id=None,
        customer_name=None,
        phone_number=None,
        branch=None,
        total_amount=None,
        order_details=order_details if order_details else None,  # Only pass details if they exist
        whatsapp_message=whatsapp_message  # Pass the WhatsApp message to the template
    )


# Add order route
@app.route('/add_order', methods=['POST'])
def add_order_route():
    customer_name = request.form['customer_name']
    phone_number = request.form['phone_number']
    branch = request.form['branch']

    if len(phone_number) != 10 or not phone_number.isdigit():
        return "Error: Phone number must be exactly 10 digits."

    services = {
        'Ironing - Shirts & Pants': (int(request.form['iron_shirts_pants_quantity']), 10),
        'Ironing - Dhothi & Sarees': (int(request.form['iron_dhothi_sarees_quantity']), 20),
        'Laundry - Shirts & Pants': (int(request.form['laundry_shirts_pants_quantity']), 20),
        'Laundry - Dhothi & Sarees': (int(request.form['laundry_dhothi_sarees_quantity']), 40),
        'Washing & Folding Only': (int(request.form['washing_folding_only_quantity']), 50),
        'Starch Treatment - Shirts & Dhothis': (int(request.form['starch_shirts_dhothi_quantity']), 50),
        'Starch Treatment - Sarees': (int(request.form['starch_saree_quantity']), 50),
        'Dry Wash - Blazer/Coat': (int(request.form['blazer_coat_quantity']), 300),
        'Dry Wash - Silk Dhothi & Shirt': (int(request.form['silk_dhothi_shirt_quantity']), 300),
        'Dry Wash - Silk Sarees': (int(request.form['silk_saree_quantity']), 500),
        'Dry Wash - Lehanga': (int(request.form['lehanga_quantity']), 300),
        'Double Bedsheet': (int(request.form['double_bedsheet_quantity']), 50),
        'Single Bedsheet': (int(request.form['single_bedsheet_quantity']), 30),
        'Double Blanket': (int(request.form['double_blanket_quantity']), 100),
        'Single Blanket': (int(request.form['single_blanket_quantity']), 50),
        'Carpet Washing': (int(request.form['carpet_quantity']), 500),
    }

    total_price = 0
    order_details = []
    whatsapp_details = []

    for service, (quantity, price_per_piece) in services.items():
        if quantity > 0:
            total_price += quantity * price_per_piece
            order_details.append({
                'Service': service,
                'Quantity': quantity,
                'Price per Piece': price_per_piece,
                'Total': quantity * price_per_piece
            })
            whatsapp_details.append(f"{service}: {quantity} x ₹{price_per_piece} = ₹{quantity * price_per_piece}")

    branch_code = branch[-1]  # Assuming branch is like "Branch 1", "Branch 2", etc.
    branch_number = int(branch_code)

    # Generate Order ID
    df_main = pd.read_excel(MAIN_EXCEL_FILE)
    branch_orders = df_main[df_main['Reference Number'].str.startswith(f"BR0{branch_number}")]
    new_order_number = 1 if branch_orders.empty else branch_orders['Reference Number'].str[-6:].astype(int).max() + 1
    order_id = f"BR0{branch_number}{new_order_number:06d}"

    if current_date:
        today_excel_file = get_today_excel_file(current_date)
        df_today = pd.read_excel(today_excel_file)
        current_month = current_date[:7]
        monthly_excel_file = get_monthly_excel_file(current_month)
        df_monthly = pd.read_excel(monthly_excel_file)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for detail in order_details:
            new_order = {
                'Reference Number': order_id,
                'Customer Name': customer_name,
                'Phone Number': phone_number,
                'Branch': branch,
                'Cloth Type': detail['Service'],
                'Quantity': detail['Quantity'],
                'Total Price': detail['Total'],
                'Status': 'Order Placed',
                'Timestamp': timestamp
            }
            df_today = pd.concat([df_today, pd.DataFrame([new_order])], ignore_index=True)
            df_main = pd.concat([df_main, pd.DataFrame([new_order])], ignore_index=True)
            df_monthly = pd.concat([df_monthly, pd.DataFrame([new_order])], ignore_index=True)

        df_today.to_excel(today_excel_file, index=False)
        df_main.to_excel(MAIN_EXCEL_FILE, index=False)
        df_monthly.to_excel(monthly_excel_file, index=False)

        return redirect(url_for('order_page'))
    else:
        return "Error: No active day. Start a new day first."

# Search order route
@app.route('/search_order', methods=['GET', 'POST'])
def search_order():
    orders = []
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        customer_name = request.form.get('customer_name')
        phone_number = request.form.get('phone_number')
        selected_month = request.form.get('selected_month')

        if selected_month:
            monthly_excel_file = get_monthly_excel_file(selected_month)
            if os.path.exists(monthly_excel_file):
                df_main = pd.read_excel(monthly_excel_file)
            else:
                return f"No data found for the selected month: {selected_month}"
        else:
            return "Error: Please select a month."

        # Filter the data based on the search criteria
        if order_id:
            orders = df_main[df_main['Reference Number'].str.contains(order_id, case=False, na=False)].to_dict('records')
        elif customer_name:
            orders = df_main[df_main['Customer Name'].str.contains(customer_name, case=False, na=False)].to_dict('records')
        elif phone_number:
            orders = df_main[df_main['Phone Number'].str.contains(phone_number, case=False, na=False)].to_dict('records')

    return render_template('search_order.html', orders=orders)

# Mark order as arrived and notify
@app.route('/mark_arrival_and_notify', methods=['POST'])
def mark_arrival_and_notify():
    selected_orders = request.form.getlist('selected_orders')
    df_main = pd.read_excel(MAIN_EXCEL_FILE)

    for order_id in selected_orders:
        df_main.loc[df_main['Reference Number'] == order_id, 'Status'] = 'Arrived at Shop'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df_main.loc[df_main['Reference Number'] == order_id, 'Timestamp'] = timestamp

        customer_phone = df_main.loc[df_main['Reference Number'] == order_id, 'Phone Number'].values[0]
        print(f"Notification sent to customer {customer_phone} for order {order_id}")
        
    df_main.to_excel(MAIN_EXCEL_FILE, index=False)

    return redirect(url_for('search_order'))

# Download Excel file
@app.route('/open_excel/<file_name>')
def open_excel_file(file_name):
    file_path = os.path.join(DAILY_FILES_FOLDER, file_name)
    return send_file(file_path, as_attachment=True)

# Update status for all customers in a selected file
@app.route('/update_status', methods=['POST'])
def update_status_route():
    selected_file = request.form['file_name']
    selected_status = request.form.get('status')

    if selected_status and selected_file:
        file_path = os.path.join(DAILY_FILES_FOLDER, selected_file)
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            df['Status'] = selected_status
            df.to_excel(file_path, index=False)
            
            df_main = pd.read_excel(MAIN_EXCEL_FILE)
            df_main.loc[df_main['Reference Number'].isin(df['Reference Number']), 'Status'] = selected_status
            df_main.to_excel(MAIN_EXCEL_FILE, index=False)

    return redirect(url_for('manage_orders'))

# Fetch customers based on the selected file
@app.route('/find_customers', methods=['POST'])
def find_customers():
    file_name = request.form['file_name']
    file_path = os.path.join(DAILY_FILES_FOLDER, file_name)
    
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        customers = df['Customer Name'].dropna().tolist()
        return jsonify(customers)
    
    return jsonify([])

@app.route('/get_orders_by_day', methods=['POST'])
def get_orders_by_day():
    file_name = request.form['file_name']
    file_path = os.path.join(DAILY_FILES_FOLDER, file_name)

    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        orders = df.to_dict('records')  # Convert to a list of dictionaries
        return jsonify({
            'file_name': file_name,
            'orders': orders
        })

    return jsonify({
        'file_name': file_name,
        'orders': []
    })


# Update the status for selected customers
@app.route('/update_selected_customers_status', methods=['POST'])
def update_selected_customers_status():
    selected_customers = request.form.get('selected_customers', '').split(',')
    new_status = request.form['status']
    file_name = request.form['file_name']
    file_path = os.path.join(DAILY_FILES_FOLDER, file_name)
    
    if os.path.exists(file_path) and selected_customers:
        df = pd.read_excel(file_path)
        df.loc[df['Customer Name'].isin(selected_customers), 'Status'] = new_status
        df.to_excel(file_path, index=False)

        df_main = pd.read_excel(MAIN_EXCEL_FILE)
        df_main.loc[df_main['Customer Name'].isin(selected_customers), 'Status'] = new_status
        df_main.to_excel(MAIN_EXCEL_FILE, index=False)
    
    return redirect(url_for('manage_orders'))

# Close the day
@app.route('/close_day', methods=['POST'])
def close_day_route():
    global current_date
    current_date = None
    return redirect(url_for('home'))


# Manage orders and display the available files
@app.route('/manage_orders')
def manage_orders():
    excel_files = [f for f in os.listdir(DAILY_FILES_FOLDER) if f.endswith('.xlsx')]
    file_statuses = {}
    file_data = {}  # Store data for each file

    for file in excel_files:
        file_path = os.path.join(DAILY_FILES_FOLDER, file)
        df = pd.read_excel(file_path)
        if not df.empty:
            file_statuses[file] = df['Status'].iloc[0]
            file_data[file] = df  # Store the DataFrame for each file
        else:
            file_statuses[file] = "No Status"
    
    return render_template(
        'manage_orders.html',
        excel_files=excel_files,
        status_options=STATUS_OPTIONS,
        file_statuses=file_statuses,
        file_data=file_data  # Pass file data to the template
    )

# View the list of daily files
@app.route('/view_day_list')
def view_day_list():
    excel_files = [f for f in os.listdir(DAILY_FILES_FOLDER) if f.endswith('.xlsx')]
    return render_template('view_day_list.html', excel_files=excel_files)

    return render_template('order_page.html', order_id=order_id, customer_name=customer_name, phone_number=phone_number, branch=branch, total_amount=total_amount, order_details=order_details or [])  # Ensure order_details is a list



if __name__ == '__main__':
    initialize_excel()
    app.run(debug=True)
