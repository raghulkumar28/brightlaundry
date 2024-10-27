# Laundry Management Admin Application

The Laundry Management Admin Application is a custom web solution designed specifically for laundry service administrators to help manage orders, track daily work, and generate useful data summaries. It offers a simple interface for adding orders, generating bills, and sending WhatsApp notifications. Additionally, it ensures data persistence by saving daily records in an Excel sheet and backing up monthly data via email.

*This application was developed by Raghul under the Warah Corporation umbrella.* 

## Purpose and Functionality

This application is intended for administrative use in laundry services, aiming to simplify and streamline order tracking, billing, and data management. It also includes features like daily reports, monthly summaries, and automatic backup, making it a comprehensive solution for laundry management.

### Core Features
- *Order Tracking*: Add, update, and manage orders within a single interface.
- *Billing Notifications*: Automatically send WhatsApp notifications with bill details to customers.
- *Daily Data Saving*: Every workday’s data is saved in a structured Excel file in the daily_files folder.
- *Monthly Summary Generation*: Generate monthly summaries for order tracking, stored in monthly_files.
- *Automatic Monthly Backup*: Email notifications and backups are automatically sent at the end of each month to ensure data security.
- *Customizable Reporting*: Daily and monthly data are saved in Excel format to allow for further analysis and customization as needed.

## Project Specifications and Structure

### Technologies and Dependencies
- *Python* (3.6+)
- *Flask* (Web Framework): Handles the web application and routing.
- *Pandas* (Data Manipulation): Manages and organizes order data for saving and reporting.
- *Openpyxl* (Excel Handling): Saves daily and monthly data to Excel files.
- *Twilio API or WhatsApp Business API* (optional): Sends WhatsApp messages for bill notifications.

### Project Directory Structure

- app.py: The main script to run the web application.
- templates/: Contains HTML files for each webpage used in the app.
- daily_files/: Folder where each day’s data is saved.
- monthly_files/: Folder where monthly data summaries are saved.
- laundry_data_main.xlsx: Main consolidated file that holds all order records.
  
### Endpoints and Usage

- **/ (Home Page): Displays options for managing the day and accessing order records.
- **/start_day**: Initializes a new workday, resetting daily data.
- **/order_page**: Allows adding new orders, including details like order ID, customer name, and items.
- **/manage_orders**: Manages existing orders, updates status, and sends billing details over WhatsApp.
- **/close_day**: Ends the current workday and generates a daily summary, saving it in daily_files/.

## Installation and Setup

### 1. System Requirements
Ensure you have Python 3.6 or higher installed on your system.

### 2. Clone the Repository
Clone this repository to your local system:
```bash
git clone https://github.com/your-repository/laundry-management-app.git
cd laundry-management-app
