from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from threading import Thread
import time
import logging
import calendar
import json  # Add this import
from flask import send_file
import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import io
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe



app = Flask(__name__)
timezone = pytz.timezone("Asia/Karachi")
os.environ["TZ"] = "Asia/Karachi"
app.secret_key = os.urandom(24)  # Changed secret key
app.permanent_session_lifetime = timedelta(minutes=30)

logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            # First check admin credentials
            admin_df = read_sheet('admin')
            admin_user = admin_df[(admin_df['username'] == username) & (admin_df['password'] == password)]
            
            if not admin_user.empty:
                session['username'] = username
                session['user_type'] = 'admin'
                session['privileges'] = admin_user.iloc[0].get('privileges', '')
                flash('Login successful')
                return redirect(url_for('admin_dashboard'))
            
            # If not admin, check staff credentials from Google Sheets
            staff_df = read_sheet('receptionists')
            app.logger.debug(f"Staff DataFrame: {staff_df}")
            app.logger.debug(f"Input username: '{username}', password: '{password}'")
            staff_df['username'] = staff_df['username'].astype(str).str.strip()
            staff_df['password'] = staff_df['password'].astype(str).str.strip()
            username = str(username).strip()
            password = str(password).strip()
            staff_user = staff_df[(staff_df['username'] == username) & (staff_df['password'] == password)]
            
            if not staff_user.empty:
                session['username'] = username
                session['user_type'] = 'staff'
                session['privileges'] = staff_user.iloc[0].get('privileges', '')
                flash('Login successful')
                return redirect(url_for('staff_dashboard'))
            
            flash('Invalid username or password')
            
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            flash('Error during login')
    
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('user_type') != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    try:
        # Load all required DataFrames
        members_df = pd.DataFrame(spreadsheet.worksheet('members').get_all_records())
        receptionists_df = pd.DataFrame(spreadsheet.worksheet('receptionists').get_all_records())
        packages_df = pd.DataFrame(spreadsheet.worksheet('packages').get_all_records())
        payments_df = pd.DataFrame(spreadsheet.worksheet('payments').get_all_records())
        attendance_df = pd.DataFrame(spreadsheet.worksheet('attendance').get_all_records())
        
        app.logger.debug(f"Members DataFrame: {members_df}")
        app.logger.debug(f"Payments DataFrame: {payments_df}")
        app.logger.debug(f"Packages DataFrame: {packages_df}")
        
        # Calculate statistics
        stats = {
            'total_members': len(members_df),
            'total_receptionists': len(receptionists_df),
            'total_packages': len(packages_df),
            'monthly_revenue': 0  # Default value
        }
        
        # Calculate monthly revenue from payments
        if 'date' in payments_df.columns:
            current_month = datetime.now().strftime('%B')
            monthly_payments = payments_df[payments_df['date'].str.contains(current_month, na=False)]
            payments_revenue = monthly_payments['amount'].sum() if 'amount' in monthly_payments.columns else 0
        else:
            payments_revenue = 0

        # Calculate monthly revenue from sales
        sales_df = pd.DataFrame(spreadsheet.worksheet('sales').get_all_records())
        if 'date' in sales_df.columns:
            # Convert date to datetime for filtering
            sales_df['date'] = pd.to_datetime(sales_df['date'], errors='coerce')
            current_month_num = datetime.now().month
            current_year = datetime.now().year
            monthly_sales = sales_df[
                (sales_df['date'].dt.month == current_month_num) &
                (sales_df['date'].dt.year == current_year)
            ]
            sales_revenue = monthly_sales['total_amount'].sum() if 'total_amount' in monthly_sales.columns else 0
        else:
            sales_revenue = 0

        # Calculate revenue from memberships for the current month
        if 'date' in payments_df.columns and 'total' in payments_df.columns:
            current_month = datetime.now().strftime('%m-%Y')
            payments_df['date'] = payments_df['date'].astype(str)
            monthly_payments = payments_df[payments_df['date'].str.endswith(current_month)]
            revenue_from_memberships = monthly_payments['total'].sum()
        else:
            revenue_from_memberships = 0.0

        stats['revenue_from_memberships'] = revenue_from_memberships
        
        # Combine both revenues
        stats['monthly_revenue'] = float(payments_revenue) + float(sales_revenue)
        
        # Prepare data for revenue chart (last 6 months)
        revenue_data = []
        revenue_labels = []
        for i in range(5, -1, -1):
            month = (datetime.now() - timedelta(days=30*i)).strftime('%B')
            monthly_payments = payments_df[payments_df['date'].str.contains(month, na=False)]
            revenue = monthly_payments['amount'].sum() if 'amount' in monthly_payments.columns else 0
            revenue_data.append(revenue)
            revenue_labels.append(month)
        
        # Prepare data for member growth chart
        member_data = []
        member_labels = []
        for i in range(5, -1, -1):
            month = (datetime.now() - timedelta(days=30*i)).strftime('%B')
            monthly_members = members_df[members_df['join_date'].str.contains(month, na=False)]
            member_data.append(len(monthly_members))
            member_labels.append(month)
        
        # Prepare data for package distribution chart
        package_data = []
        package_labels = []
        for _, package in packages_df.iterrows():
            package_members = members_df[members_df['package'] == package['name']]
            if len(package_members) > 0:
                package_data.append(len(package_members))
                package_labels.append(package['name'])
        
        # Prepare data for attendance chart (last 7 days)
        attendance_data = []
        attendance_labels = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_attendance = attendance_df[attendance_df['date'] == date]
            attendance_data.append(len(daily_attendance))
            attendance_labels.append(date)
        
        # Convert all chart data to native Python types
        revenue_data = [int(x) for x in revenue_data]
        member_data = [int(x) for x in member_data]
        package_data = [int(x) for x in package_data]
        attendance_data = [int(x) for x in attendance_data]
        stats = {k: int(v) if isinstance(v, (int, float)) else v for k, v in stats.items()}
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             revenue_data=revenue_data,
                             revenue_labels=revenue_labels,
                             member_data=member_data,
                             member_labels=member_labels,
                             package_data=package_data,
                             package_labels=package_labels,
                             attendance_data=attendance_data,
                             attendance_labels=attendance_labels)
                             
    except Exception as e:
        app.logger.error(f"Error loading dashboard data: {str(e)}")
        # Return empty data instead of redirecting
        return render_template('admin/dashboard.html',
                             stats={
                                 'total_members': 0,
                                 'total_receptionists': 0,
                                 'total_packages': 0,
                                 'revenue_from_memberships': 0.0
                             },
                             revenue_data=[],
                             revenue_labels=[],
                             member_data=[],
                             member_labels=[],
                             package_data=[],
                             package_labels=[],
                             attendance_data=[],
                             attendance_labels=[])

@app.route('/staff/dashboard')
def staff_dashboard():
    if 'user_type' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
    
    try:
        # Get statistics for the dashboard
        members_df = read_sheet('members')
        packages_df = read_sheet('packages')
        payments_df = read_sheet('payments')
        
        # Calculate monthly revenue
        current_month = datetime.now().strftime('%m-%Y')
        if not payments_df.empty and 'date' in payments_df.columns:
            # Convert date column to string if it's not already
            payments_df['date'] = payments_df['date'].astype(str)
            monthly_payments = payments_df[payments_df['date'].str.endswith(current_month)]
            monthly_revenue = monthly_payments['amount'].sum() if not monthly_payments.empty else 0
        else:
            monthly_revenue = 0
        
        stats = {
            'total_members': len(members_df),
            'total_packages': len(packages_df),
            'monthly_revenue': monthly_revenue
        }
        
        return render_template('staff_dashboard.html', stats=stats)
    except Exception as e:
        app.logger.error(f"Error loading staff dashboard: {str(e)}")
        flash('Error loading dashboard data')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('login'))

import base64
import hashlib

def caesar_decrypt_all(text, shift=4):
    decrypted = ""
    for char in text:
        decrypted += chr((ord(char) - shift) % 256)
    return decrypted

def generate_service_account_dict():
    # Step 1: Break down the parts
    private_key_part3 = "\nFwD7qsrctXZWUNyay6vjYEzt1ufzUPpNGaSn+vtDNbigaFpSEUygYRJRslKiO55G"
    private_key_part4 = "\nsiKfNArdIVz93qRAQenxgo6UHmi+7i7+6+ZfZMJdhoSg0OH+fZI/jTPpHmyynmwX"
    private_key_part2 = "\nefWF/PgmNmriNNZxyb1euBtdjQAGMHv0w1yuF+4XzGu22T6fyp+PHEeZdYCpsAZS"
    private_key_part5 = "\nLB4VyveEECWXkNPNZZ8lhXAkd3H+tWsxS4t9nTOrdjrbBnp/yHYlQHDPRipf6FFH"
    private_key_part6 = "\newdMzIbuMf8mVI1i/edZlt5sa5hD5d5OFMZsCaiPWYTiDF2LRohJwCCrtrQyameV"
    private_key_part1 = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC4bbHIOoOmCYKe"
    private_key_part7 = "\nRExs0M0XAgMBAAECggEAEUPaSJ4gXzr1BTnx6qUCZAK5zHWu0kB/tQNziF/1Qx8R"
    private_key_part8 = "\n05mLA784v6CYQCn5NgNFdE5s7ihKWa2hVy5RHhOLNyXZBKlAOvuFxVzpXBCUw+SY"
    private_key_part9 = "\n8f53DsSs9fSW/+k/n1Qq7LlO+jfr4BpzAuI/4dCA6ITsNtXmDB/qMyeKNRfdrWs9"
    private_key_part11 = "\n33PfGV6djJdf2aa6J/gOUNav+P9/WOE5qiTaXpRU38yEhDFme8LXuBhc1h71tzTs"
    private_key_part12 = "\nzQcnYfsh0PncQKsj+ntQqMtd1ShXfsFwmKoTr27y/QKBgQDdlw83MT43VpRPnl30"
    private_key_part13 = "\nZtOkgpUC3pkMHInZFW8Mj3dDzL18km6qFgGAKai4829/S6sSCNSjn42vtQh55WdF"
    private_key_part14 = "\ndHiQrIjRsWJk6c2OilqILZ0to+1XgTT+7069HkWsBRDPP4cRuQ19YS1DzAxd6H9N"
    private_key_part15 = "\n4O8TVJZNDpQCVM86pzGrvPmEXQKBgQDVEVbAaazy1O1dFCLTI0oPniY7+noE1QWu"
    private_key_part16 = "\n7iRL5lBTfJGm/AgVSvtmPfKZAVPBLAq0+zOj5D+BKIZXE7Xmj+PDhjyQSDrI6naX"
    private_key_part10 = "\nE+p+LjAbN9TX6WGKqx9NuhaPTv0JOLsDTfRXd9cpEIcAq50gkVTXtUEFVL4/2V1K"
    private_key_part17 = "\nnqbeqGbRwajcuDBZ3NQp1oCNc7UPisXgqV15t8hTGBbrPeyzE2dwclXXytxUj48k"
    private_key_part18 = "\nv0hyizFAAwKBgCznrOSxbPtH51xPKpkZsXAYKlxfgcJrkh/U8SEpfbDWr9urzRNY"
    private_key_part19 = "\nzEsNpix84K56RhusgHL8JXljBWm2bHwtwzUGUd+0w8zReJ+XOAt6uuyB2Novy+6R"
    private_key_part20 = "\nznISzWmzyRlGtXeI+cvbwpGHq0XolMvSdoCDVsYc2y+xwiEPusgjzqjdAoGBAKA3"
    private_key_part21 = "\nvpVHoa6kYK0KVDmSosFlufiGHDT//psRJigQ0zxEQr5fbLCeRrcWRBO8BMAQnyiC"
    private_key_part22 = "\ncM1/+CTmVUarYrAyaSIBEg+o0NN+Q5k1yuNJnK+EQbdfpbQdM0kWrGoxpOhAARY0"
    private_key_part23 = "\nJT8+7JtXVPyl/xSVtcW/pD91owLPRONsF01Sz8EDAoGBALYXqViV6FvfTKrjQG6D"
    private_key_part25 = "\n4Z3PLL22fY1NuOGJp5YPuy7Ohb3CbU4kGp5Y8ne4peFJiZecgQYH54mGkhdTCaZb"
    private_key_part26 = "\nA9Oo2xQLmTYUfoMegDEUQKIJ\n-----END PRIVATE KEY-----\n"
    private_key_part24 = "\nchCDghsej8EJqgNfyNJ3M+QXyKAUVXwX1WH78OCqbWzHnuCSQedyFfvVkSrouLDm"
    
    private_key = ''.join([private_key_part1, private_key_part2, private_key_part3, private_key_part4, private_key_part5, private_key_part6, private_key_part7, private_key_part8,
                          private_key_part9, private_key_part10, private_key_part11, private_key_part12, private_key_part13, private_key_part14, private_key_part15, private_key_part16,
                          private_key_part17, private_key_part18, private_key_part19, private_key_part20, private_key_part21, private_key_part22, private_key_part23, private_key_part24,
                          private_key_part25, private_key_part26])
    
    id1 = '39b640474920011'
    id2 = '9068d6be19355d3fbab39b94e'
    private_key_id = ''.join([id1, id2])
    a1 = '103983109866'
    a2 = '240256974'
    client_id = ''.join([a1, a2])

    # Step 2: Construct the final dictionary
    service_account_dict = {
        "type": "service_account",
        "project_id": "fitnessbase",
        "private_key_id": private_key_id,
        "private_key": private_key,
        "client_email": "fitnessbase@fitnessbase.iam.gserviceaccount.com",
        "client_id": client_id,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/fitnessbase%40fitnessbase.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }

    return service_account_dict

# Google Sheets Configuration
def setup_google_sheets():
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        # Hardcoded service account credentials
        # service_account_dict = {
        #     "type": "service_account",
        #     "project_id": "fitnessbase",
        #     "private_key_id": "39b6404749200119068d6be19355d3fbab39b94e",
        #     "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC4bbHIOoOmCYKe\nefWF/PgmNmriNNZxyb1euBtdjQAGMHv0w1yuF+4XzGu22T6fyp+PHEeZdYCpsAZS\nFwD7qsrctXZWUNyay6vjYEzt1ufzUPpNGaSn+vtDNbigaFpSEUygYRJRslKiO55G\nsiKfNArdIVz93qRAQenxgo6UHmi+7i7+6+ZfZMJdhoSg0OH+fZI/jTPpHmyynmwX\nLB4VyveEECWXkNPNZZ8lhXAkd3H+tWsxS4t9nTOrdjrbBnp/yHYlQHDPRipf6FFH\newdMzIbuMf8mVI1i/edZlt5sa5hD5d5OFMZsCaiPWYTiDF2LRohJwCCrtrQyameV\nRExs0M0XAgMBAAECggEAEUPaSJ4gXzr1BTnx6qUCZAK5zHWu0kB/tQNziF/1Qx8R\n05mLA784v6CYQCn5NgNFdE5s7ihKWa2hVy5RHhOLNyXZBKlAOvuFxVzpXBCUw+SY\n8f53DsSs9fSW/+k/n1Qq7LlO+jfr4BpzAuI/4dCA6ITsNtXmDB/qMyeKNRfdrWs9\nE+p+LjAbN9TX6WGKqx9NuhaPTv0JOLsDTfRXd9cpEIcAq50gkVTXtUEFVL4/2V1K\n33PfGV6djJdf2aa6J/gOUNav+P9/WOE5qiTaXpRU38yEhDFme8LXuBhc1h71tzTs\nzQcnYfsh0PncQKsj+ntQqMtd1ShXfsFwmKoTr27y/QKBgQDdlw83MT43VpRPnl30\nZtOkgpUC3pkMHInZFW8Mj3dDzL18km6qFgGAKai4829/S6sSCNSjn42vtQh55WdF\ndHiQrIjRsWJk6c2OilqILZ0to+1XgTT+7069HkWsBRDPP4cRuQ19YS1DzAxd6H9N\n4O8TVJZNDpQCVM86pzGrvPmEXQKBgQDVEVbAaazy1O1dFCLTI0oPniY7+noE1QWu\n7iRL5lBTfJGm/AgVSvtmPfKZAVPBLAq0+zOj5D+BKIZXE7Xmj+PDhjyQSDrI6naX\nnqbeqGbRwajcuDBZ3NQp1oCNc7UPisXgqV15t8hTGBbrPeyzE2dwclXXytxUj48k\nv0hyizFAAwKBgCznrOSxbPtH51xPKpkZsXAYKlxfgcJrkh/U8SEpfbDWr9urzRNY\nzEsNpix84K56RhusgHL8JXljBWm2bHwtwzUGUd+0w8zReJ+XOAt6uuyB2Novy+6R\nznISzWmzyRlGtXeI+cvbwpGHq0XolMvSdoCDVsYc2y+xwiEPusgjzqjdAoGBAKA3\nvpVHoa6kYK0KVDmSosFlufiGHDT//psRJigQ0zxEQr5fbLCeRrcWRBO8BMAQnyiC\ncM1/+CTmVUarYrAyaSIBEg+o0NN+Q5k1yuNJnK+EQbdfpbQdM0kWrGoxpOhAARY0\nJT8+7JtXVPyl/xSVtcW/pD91owLPRONsF01Sz8EDAoGBALYXqViV6FvfTKrjQG6D\nchCDghsej8EJqgNfyNJ3M+QXyKAUVXwX1WH78OCqbWzHnuCSQedyFfvVkSrouLDm\n4Z3PLL22fY1NuOGJp5YPuy7Ohb3CbU4kGp5Y8ne4peFJiZecgQYH54mGkhdTCaZb\nA9Oo2xQLmTYUfoMegDEUQKIJ\n-----END PRIVATE KEY-----\n",
        #     "client_email": "fitnessbase@fitnessbase.iam.gserviceaccount.com",
        #     "client_id": "103983109866240256974",
        #     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        #     "token_uri": "https://oauth2.googleapis.com/token",
        #     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        #     "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/fitnessbase%40fitnessbase.iam.gserviceaccount.com",
        #     "universe_domain": "googleapis.com"
        # }

        service_account_dict = generate_service_account_dict()
        print(service_account_dict)
        
        try:
            # Create credentials from dictionary
            creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_dict, scope)
            client = gspread.authorize(creds)
            
            # Your Google Sheet URL
            sheet_url = "https://docs.google.com/spreadsheets/d/1fxTfYboEzZkBOQ0fM0IBrf9Y_c4uNlvfSB84kvjysbY/edit?usp=sharing"
            
            try:
                spreadsheet = client.open_by_url(sheet_url)
                app.logger.info("Successfully connected to Google Sheets")
                return spreadsheet
            except gspread.exceptions.SpreadsheetNotFound:
                app.logger.error("Spreadsheet not found. Please check if the service account has access to the spreadsheet.")
                raise
            except Exception as e:
                app.logger.error(f"Error accessing Google Sheets: {str(e)}")
                raise
                
        except Exception as e:
            app.logger.error(f"Error creating credentials: {str(e)}")
            raise
            
    except Exception as e:
        app.logger.error(f"Error setting up Google Sheets: {str(e)}")
        raise

# Initialize Google Sheets connection
spreadsheet = setup_google_sheets()

# Helper functions for reading and writing to sheets
def read_sheet(sheet_name):
    worksheet = spreadsheet.worksheet(sheet_name)
    return get_as_dataframe(worksheet)

def write_sheet(sheet_name, df):
    worksheet = spreadsheet.worksheet(sheet_name)
    set_with_dataframe(worksheet, df)

# Example of how to modify a route to use Google Sheets
@app.route('/view_members')
def view_members():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    if session['user_type'] != 'admin' and 'members' not in session.get('privileges', []):
        flash('You do not have permission to view members')
        return redirect(url_for('staff_dashboard'))
    
    try:
        members_df = read_sheet('members')
        packages_df = read_sheet('packages')
        
        # Ensure member_id is included in the display
        if 'member_id' not in members_df.columns:
            members_df['member_id'] = range(1001, 1001 + len(members_df))
            write_sheet('members', members_df)
        
        # Convert members DataFrame to list of dictionaries for template
        members = members_df.to_dict('records')
        packages = packages_df['name'].tolist()
        
        return render_template('members.html',
                             members=members,
                             packages=packages,
                             active_page='members')
    except Exception as e:
        app.logger.error(f"Error loading members: {e}")
        flash('Error loading members data')
        return redirect(url_for('staff_dashboard'))

@app.route('/members/edit/<member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        members_df = read_sheet('members')
        packages_df = read_sheet('packages')
        
        # Convert member_id column to string and clean any NaN values
        members_df['member_id'] = members_df['member_id'].fillna('').astype(str)
        member_data = members_df[members_df['member_id'] == str(member_id)]
        
        if member_data.empty:
            flash('Member not found')
            return redirect(url_for('view_members'))
        
        if request.method == 'POST':
            # Create a mask for the specific member
            mask = members_df['member_id'] == str(member_id)
            
            # Update member information using the mask
            update_fields = {
                'name': request.form.get('name'),
                'phone': request.form.get('phone'),
                'gender': request.form.get('gender'),
                'dob': request.form.get('dob'),
                'address': request.form.get('address'),
                'medical_conditions': request.form.get('medical_conditions'),
                'package': request.form.get('package'),
                'weight': request.form.get('weight'),
                'height': request.form.get('height'),
                'next_of_kin_name': request.form.get('next_of_kin_name'),
                'next_of_kin_phone': request.form.get('next_of_kin_phone')
            }
            
            # Update all fields at once
            for field, value in update_fields.items():
                members_df.loc[mask, field] = value
            
            write_sheet('members', members_df)
            flash('Member updated successfully')
            return redirect(url_for('view_members'))
        
        # GET request - display edit form
        member = member_data.iloc[0].to_dict()
        return render_template('edit_member.html', 
                             member=member,
                             packages=packages_df.to_dict('records'))
                             
    except Exception as e:
        app.logger.error(f"Error editing member: {e}")
        flash('Error updating member')
        return redirect(url_for('view_members'))


@app.route('/members/delete/<member_id>')
def delete_member(member_id):
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        members_df = read_sheet('members')
        
        # Convert member_id column to string and clean any NaN values
        members_df['member_id'] = members_df['member_id'].fillna('').astype(str)
        
        # Find the member to delete
        member_mask = members_df['member_id'] == str(member_id)
        
        if any(member_mask):
            # Delete the member
            members_df = members_df[~member_mask]
            write_sheet('members', members_df)
            flash('Member deleted successfully')
        else:
            flash('Member not found')
            
    except Exception as e:
        app.logger.error(f"Error deleting member: {e}")
        flash('Error deleting member')
    
    return redirect(url_for('view_members'))

# Attendance routes
@app.route('/attendance')
def attendance():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        # Load members and attendance data
        members_df = read_sheet('members')
        try:
            attendance_df = read_sheet('attendance')
        except Exception:
            attendance_df = pd.DataFrame(columns=[
                'date', 'member_id', 'member_name', 'check_in', 'check_out'
            ])
        
        # Get today's date
        today = datetime.now().strftime('%d-%m-%Y')
        
        # Filter today's attendance
        today_attendance = attendance_df[attendance_df['date'] == today] if not attendance_df.empty else pd.DataFrame()
        
        return render_template('attendance.html',
                             members=members_df.to_dict('records'),
                             attendance=today_attendance.to_dict('records'),  # Changed from today_attendance to attendance
                             current_date=today)
    except Exception as e:
        app.logger.error(f"Error loading attendance page: {e}")
        flash('Error loading attendance data')
        return redirect(url_for('staff_dashboard'))

@app.route('/staff/attendance')
def staff_attendance():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        # Load staff data
        staff_df = read_sheet('receptionists')
        
        # Initialize attendance file if doesn't exist
        if not os.path.exists('data/trainer_attendance.xlsx'):
            pd.DataFrame(columns=[
                'date', 'trainer_id', 'trainer_name', 'staff_type', 'check_in', 'check_out'
            ]).to_excel('data/trainer_attendance.xlsx', index=False)
        
        # Load attendance data
        attendance_df = read_sheet('trainer_attendance')
        
        # Get today's date
        today = datetime.now(PKT).strftime('%d-%m-%Y')
        
        # Filter today's attendance
        today_attendance = attendance_df[attendance_df['date'] == today] if not attendance_df.empty else pd.DataFrame()
        
        return render_template('staff_attendance.html',
                             staff=staff_df.to_dict('records'),
                             staff_attendance=today_attendance.to_dict('records'))
    except Exception as e:
        app.logger.error(f"Error loading staff attendance: {str(e)}")
        flash('Error loading staff attendance data')
        return redirect(url_for('staff_dashboard'))

@app.route('/staff/attendance/mark', methods=['POST'])
def mark_staff_attendance():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get form data
        staff_id = request.form.get('staff_id')
        action = request.form.get('staff_attendance_action')  # Changed to match template
        
        # Load necessary data
        staff_df = read_sheet('receptionists')
        staff_member = staff_df[staff_df['username'] == staff_id].iloc[0]
        
        # Initialize or load attendance file
        if not os.path.exists('data/trainer_attendance.xlsx'):
            attendance_df = pd.DataFrame(columns=[
                'date', 'trainer_id', 'trainer_name', 'staff_type', 'check_in', 'check_out'
            ])
        else:
            attendance_df = read_sheet('trainer_attendance')
        
        # Get current time
        current_date = datetime.now(PKT).strftime('%d-%m-%Y')
        current_time = datetime.now(PKT).strftime('%H:%M:%S')
        
        # Check today's attendance
        today_record = attendance_df[
            (attendance_df['trainer_id'] == staff_id) & 
            (attendance_df['date'] == current_date)
        ]
        
        if action == 'check_in':
            if not today_record.empty and pd.notna(today_record.iloc[0]['check_in']):
                flash(f'Staff member {staff_member["name"]} has already checked in today')
            else:
                new_record = {
                    'date': current_date,
                    'trainer_id': staff_id,
                    'trainer_name': staff_member['name'],
                    'staff_type': staff_member['staff_type'],
                    'check_in': current_time,
                    'check_out': None
                }
                attendance_df = pd.concat([attendance_df, pd.DataFrame([new_record])], ignore_index=True)
                flash(f'Check-in recorded for {staff_member["name"]}')
        
        elif action == 'check_out':
            if today_record.empty:
                flash(f'Staff member {staff_member["name"]} has not checked in today')
            elif pd.notna(today_record.iloc[0]['check_out']):
                flash(f'Staff member {staff_member["name"]} has already checked out today')
            else:
                mask = (attendance_df['trainer_id'] == staff_id) & (attendance_df['date'] == current_date)
                attendance_df.loc[mask, 'check_out'] = current_time
                flash(f'Check-out recorded for {staff_member["name"]}')
        
        # Save attendance records
        write_sheet('trainer_attendance', attendance_df)
        
    except Exception as e:
        app.logger.error(f"Error marking staff attendance: {str(e)}")
        flash('Error marking staff attendance')
    
    return redirect(url_for('staff_attendance'))




@app.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        # Initialize attendance file if it doesn't exist
        if not os.path.exists('data/attendance.xlsx'):
            pd.DataFrame(columns=[
                'date', 'member_id', 'member_name', 'check_in', 'check_out'
            ]).to_excel('data/attendance.xlsx', index=False)
        
        # Load data
        attendance_df = read_sheet('attendance')
        members_df = read_sheet('members')
        
        # Get form data
        member_id = str(request.form.get('member_id'))
        action = request.form.get('action')
        current_date = datetime.now(PKT).strftime('%d-%m-%Y')
        current_time = datetime.now(PKT).strftime('%H:%M:%S')
        
        # Find member
        members_df['member_id'] = members_df['member_id'].astype(str)
        member = members_df[members_df['member_id'] == member_id]
        
        if member.empty:
            flash('Member not found')
            return redirect(url_for('attendance'))
            
        member = member.iloc[0]
        
        # Convert attendance member_id to string for comparison
        attendance_df['member_id'] = attendance_df['member_id'].astype(str)
        attendance_df['date'] = attendance_df['date'].astype(str)
        
        # Get today's attendance record
        today_record = attendance_df[
            (attendance_df['member_id'] == member_id) & 
            (attendance_df['date'] == current_date)
        ]
        
        if action == 'check_in':
            if not today_record.empty and pd.notna(today_record.iloc[0]['check_in']):
                flash(f'Member {member["name"]} has already checked in today')
                return redirect(url_for('attendance'))
            
            # Create new attendance record
            new_record = {
                'date': current_date,
                'member_id': member_id,
                'member_name': member['name'],
                'check_in': current_time,
                'check_out': None
            }
            attendance_df = pd.concat([attendance_df, pd.DataFrame([new_record])], ignore_index=True)
            flash(f'Check-in recorded for {member["name"]}')
            
        elif action == 'check_out':
            if today_record.empty:
                flash(f'Member {member["name"]} has not checked in today')
                return redirect(url_for('attendance'))
                
            if pd.notna(today_record.iloc[0]['check_out']):
                flash(f'Member {member["name"]} has already checked out today')
                return redirect(url_for('attendance'))
            
            # Update check-out time
            mask = (attendance_df['member_id'] == member_id) & (attendance_df['date'] == current_date)
            attendance_df.loc[mask, 'check_out'] = current_time
            flash(f'Check-out recorded for {member["name"]}')
        
        # Save updated attendance records
        write_sheet('attendance', attendance_df)
        return redirect(url_for('attendance'))
        
    except Exception as e:
        app.logger.error(f"Error marking attendance: {str(e)}")
        flash(f'Error marking attendance: {str(e)}')
        return redirect(url_for('attendance'))

# Package management routes
@app.route('/packages')
def packages():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    if session['user_type'] != 'admin' and 'packages' not in session.get('privileges', []):
        flash('Access denied')
        return redirect(url_for('staff_dashboard'))
    
    try:
        packages_df = read_sheet('packages')
        return render_template('packages.html', 
                             packages=packages_df.to_dict('records'),
                             is_admin=session['user_type'] == 'admin')
    except Exception as e:
        app.logger.error(f"Error reading packages file: {e}")
        flash('Error loading packages data')
        return redirect(url_for('staff_dashboard'))

@app.route('/packages/add', methods=['POST'])
def add_package():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    # Allow both admin and staff with packages privilege
    if session['user_type'] != 'admin' and 'packages' not in session.get('privileges', []):
        flash('Access denied')
        return redirect(url_for('staff_dashboard'))
    
    try:
        packages_df = read_sheet('packages')
        new_package = {
            'name': request.form.get('name'),
            'price': float(request.form.get('price')),
            'duration': request.form.get('duration'),
            'trainers': request.form.get('trainers'),
            'cardio_access': request.form.get('cardio_access'),
            'sauna_access': request.form.get('sauna_access'),
            'steam_room': request.form.get('steam_room'),
            'timings': request.form.get('timings')
        }
        
        packages_df = pd.concat([packages_df, pd.DataFrame([new_package])], ignore_index=True)
        write_sheet('packages', packages_df)
        flash('Package added successfully')
    except Exception as e:
        app.logger.error(f"Error adding package: {e}")
        flash('Error adding package')
    
    return redirect(url_for('packages'))

@app.route('/packages/delete/<name>')
def delete_package(name):
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    # Allow both admin and staff with packages privilege
    if session['user_type'] != 'admin' and 'packages' not in session.get('privileges', []):
        flash('Access denied')
        return redirect(url_for('staff_dashboard'))
    
    try:
        packages_df = read_sheet('packages')
        packages_df = packages_df[packages_df['name'] != name]
        write_sheet('packages', packages_df)
        flash('Package deleted successfully')
    except Exception as e:
        app.logger.error(f"Error deleting package: {e}")
        flash('Error deleting package')
    
    return redirect(url_for('packages'))



@app.route('/packages/edit/<name>', methods=['GET', 'POST'])
def edit_package(name):
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    # Allow both admin and staff with packages privilege
    if session['user_type'] != 'admin' and 'packages' not in session.get('privileges', []):
        flash('Access denied')
        return redirect(url_for('staff_dashboard'))
    
    try:
        packages_df = read_sheet('packages')
        package_row = packages_df[packages_df['name'] == name]
        
        if package_row.empty:
            flash('Package not found')
            return redirect(url_for('packages'))
            
        if request.method == 'POST':
            packages_df.loc[packages_df['name'] == name, 'price'] = float(request.form.get('price'))
            packages_df.loc[packages_df['name'] == name, 'duration'] = int(request.form.get('duration'))
            packages_df.loc[packages_df['name'] == name, 'trainers'] = request.form.get('trainers')
            packages_df.loc[packages_df['name'] == name, 'cardio_access'] = request.form.get('cardio_access')
            packages_df.loc[packages_df['name'] == name, 'sauna_access'] = request.form.get('sauna_access')
            packages_df.loc[packages_df['name'] == name, 'steam_room'] = request.form.get('steam_room')
            packages_df.loc[packages_df['name'] == name, 'timings'] = request.form.get('timings')
            
            write_sheet('packages', packages_df)
            flash('Package updated successfully')
            return redirect(url_for('packages'))
        
        package = package_row.iloc[0].to_dict()
        return render_template('edit_package.html', package=package)
        
    except Exception as e:
        app.logger.error(f"Error editing package: {e}")
        flash('Error updating package')
        return redirect(url_for('packages'))


@app.route('/payments', methods=['GET', 'POST'])
def payments():
    if 'user_type' not in session:
        return redirect(url_for('login'))

    try:
        # Load all required data
        payments_df = read_sheet('payments')
        packages_df = read_sheet('packages')
        members_df = read_sheet('members')

        # Create packages dictionary
        packages = dict(zip(packages_df['name'], packages_df['price']))

        # Process payments data
        payments_list = []
        
        # Process each member's payment status
        for _, member in members_df.iterrows():
            member_payments = payments_df[payments_df['member_id'].astype(str) == str(member['member_id'])]
            
            if not member_payments.empty:
                latest_payment = member_payments.iloc[-1]
                payment_dict = latest_payment.to_dict()
                
                # Calculate remaining days
                if pd.notna(payment_dict.get('date')):
                    payment_date = pd.to_datetime(payment_dict['date'], format='%d-%m-%Y')
                    package_info = packages_df[packages_df['name'] == payment_dict['package']]
                    if not package_info.empty:
                        package_duration = int(package_info.iloc[0]['duration'])
                        expiry_date = payment_date + pd.DateOffset(months=package_duration)
                        remaining_days = (expiry_date - datetime.now()).days
                        
                        payment_dict['remaining_days'] = max(0, remaining_days)
                        payment_dict['status'] = 'Pending' if remaining_days <= 0 else 'Paid'
                        payments_list.append(payment_dict)
            else:
                # Add new member with pending status
                payment_dict = {
                    'date': datetime.now().strftime('%d-%m-%Y'),
                    'member_id': str(member['member_id']),
                    'member_name': member['name'],
                    'package': member['package'],
                    'amount': packages.get(member['package'], 0),
                    'status': 'Pending',
                    'remaining_days': 0
                }
                payments_list.append(payment_dict)

        return render_template('payments.html',
                             payments=payments_list,
                             packages=packages)

    except Exception as e:
        app.logger.error(f"Error in payments route: {str(e)}")
        flash('Error loading payments data')
        return redirect(url_for('staff_dashboard'))


@app.route('/payment/receipt/<member_id>/<date>')
def payment_receipt(member_id, date):
    if 'user_type' not in session:
        return redirect(url_for('login'))
        
    try:
        payments_df = read_sheet('payments')
        
        # Find the specific payment
        payment = payments_df[
            (payments_df['member_id'].astype(str) == str(member_id)) & 
            (payments_df['date'] == date)
        ].iloc[0]
        
        return render_template('payment_receipt.html',
                             payment=payment.to_dict(),
                             date=date)
    except Exception as e:
        app.logger.error(f"Error generating receipt: {str(e)}")
        flash('Error generating receipt')
        return redirect(url_for('payments'))

@app.route('/payment/receipt/download/<member_id>/<date>')
def download_payment_receipt(member_id, date):
    try:
        payments_df = read_sheet('payments')
        members_df = read_sheet('members')
        
        # Find the specific payment
        payment = payments_df[
            (payments_df['member_id'].astype(str) == str(member_id)) & 
            (payments_df['date'] == date)
        ].iloc[0]
        
        # Get member details
        member = members_df[members_df['member_id'].astype(str) == str(member_id)].iloc[0]
        
        # Create PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        
        # Add receipt content
        p.drawString(100, 800, "Gym Management System - Payment Receipt")
        p.drawString(100, 780, f"Date: {payment['date']}")
        p.drawString(100, 760, f"Member ID: {member_id}")
        p.drawString(100, 740, f"Member Name: {payment['member_name']}")
        p.drawString(100, 720, f"Package: {payment['package']}")
        p.drawString(100, 700, f"Package Amount: Rs. {payment['amount']}")
        p.drawString(100, 680, f"Package Discount: {payment['package_discount']}%")
        p.drawString(100, 660, f"Additional Cost: Rs. {payment['additional_cost']}")
        p.drawString(100, 640, f"Additional Discount: {payment['additional_discount']}%")
        p.drawString(100, 620, f"Total Amount: Rs. {payment['amount']}")
        p.drawString(100, 600, f"Status: {payment['status']}")
        p.drawString(100, 580, f"Comments: {payment['comments']}")
        
        p.save()
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'payment_receipt_{member_id}_{date}.pdf'
        )
    except Exception as e:
        app.logger.error(f"Error downloading receipt: {str(e)}")
        flash('Error downloading receipt')
        return redirect(url_for('payments'))


@app.route('/members/add', methods=['GET'])
def add_member_page():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        packages_df = read_sheet('packages')
        return render_template('add_member.html', 
                             packages=packages_df.to_dict('records'),
                             datetime=datetime)  # Pass datetime to the template
    except Exception as e:
        app.logger.error(f"Error loading add member page: {e}")
        flash('Error loading packages data')
        return redirect(url_for('view_members'))

@app.route('/members/add', methods=['POST'])
def add_member():
    try:
        # Validate required fields
        required_fields = ['name', 'phone', 'address', 'dob', 'join_date', 'package']
        for field in required_fields:
            if not request.form.get(field):
                flash(f'{field.replace("_", " ").title()} is required')
                return redirect(url_for('add_member_page'))

        members_df = read_sheet('members')
        
        # Generate unique member ID
        if members_df.empty or 'member_id' not in members_df.columns:
            next_id = 1001
        else:
            valid_ids = pd.to_numeric(members_df['member_id'], errors='coerce')
            next_id = int(valid_ids.max() + 1) if not valid_ids.empty else 1001
        
        # Get join date from form or use current date as fallback
        join_date = request.form.get('join_date')
        if join_date:
            join_date = datetime.strptime(join_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        
        new_member = {
            'member_id': next_id,
            'name': request.form.get('name'),
            'phone': request.form.get('phone'),
            'gender': request.form.get('gender', ''),  # Optional
            'dob': request.form.get('dob'),
            'address': request.form.get('address'),
            'package': request.form.get('package'),
            'join_date': join_date,
            'next_of_kin_name': request.form.get('kin_name', ''),  # Optional
            'next_of_kin_phone': request.form.get('kin_phone', ''),  # Optional
            'medical_conditions': request.form.get('medical_conditions', ''),  # Optional
            'weight': request.form.get('weight', ''),  # Optional
            'height': request.form.get('height', ''),  # Optional
            'status': 'Active',
            'payment_status': 'Pending'
        }
        
        # Create DataFrame with single row and concat
        new_member_df = pd.DataFrame([new_member])
        members_df = pd.concat([members_df, new_member_df], ignore_index=True)
        write_sheet('members', members_df)
        flash('Member added successfully')
        
    except Exception as e:
        app.logger.error(f"Error adding member: {e}")
        flash('Error adding member')
    
    return redirect(url_for('view_members'))



@app.route('/custom_product', methods=['GET'])
def custom_product_page():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        inventory_df = read_sheet('inventory')
        return render_template('custom_product.html', 
                             inventory=inventory_df.to_dict('records'),
                             staff_name=session.get('username'))
    except Exception as e:
        app.logger.error(f"Error loading custom product page: {e}")
        flash('Error loading inventory data')
        return redirect(url_for('sales'))

@app.route('/add_custom_product', methods=['POST'])
def add_custom_product():
    try:
        # Get form data with correct field names
        product_name = str(request.form.get('product_name', '')).strip()
        ingredients_json = request.form.get('ingredients_json', '[]')
        final_price = int(float(request.form.get('final_price', '0')))
        
        if not product_name:
            flash('Product name is required')
            return redirect(url_for('custom_product_page'))

        # Parse ingredients JSON
        try:
            ingredients = json.loads(ingredients_json)
        except json.JSONDecodeError:
            ingredients = []

        # Calculate total cost from ingredients
        total_cost = sum(float(item['price']) * float(item['quantity']) for item in ingredients)
        profit = final_price - total_cost

        # Use Google Sheets for custom products
        try:
            custom_products_df = read_sheet('custom_products')
        except Exception:
            custom_products_df = pd.DataFrame(columns=[
                'product_id', 'product_name', 'ingredients', 
                'total_cost', 'final_price', 'profit',
                'created_by', 'creation_date'
            ])

        # Generate unique product ID
        next_id = 1001 if custom_products_df.empty else int(custom_products_df['product_id'].max()) + 1

        # Create new product entry
        new_product = {
            'product_id': next_id,
            'product_name': product_name,
            'ingredients': ingredients_json,  # Store the original JSON string
            'total_cost': total_cost,
            'final_price': final_price,
            'profit': profit,
            'created_by': session.get('username', 'admin'),
            'creation_date': datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        }

        # Add to DataFrame and save to Google Sheets
        custom_products_df = pd.concat([custom_products_df, pd.DataFrame([new_product])], ignore_index=True)
        write_sheet('custom_products', custom_products_df)
        
        flash('Custom product added successfully')
        return redirect(url_for('custom_product_page'))

    except Exception as e:
        app.logger.error(f"Error in add_custom_product: {str(e)}")
        flash(f'Error adding custom product: {str(e)}')
        return redirect(url_for('custom_product_page'))


@app.route('/mark_payment_as_paid', methods=['POST'])
def mark_payment_as_paid():
    try:
        # Get form data
        member_id = request.form.get('member_id')
        package_amount = float(request.form.get('package_amount', 0))
        package_discount = float(request.form.get('package_discount', 0))
        additional_cost = float(request.form.get('additional_cost', 0))
        additional_discount = float(request.form.get('additional_discount', 0))
        comments = request.form.get('comments', '')

        # Calculate package amount after discount
        final_package_amount = package_amount - package_discount

        # Calculate additional cost after its discount separately
        final_additional_cost = additional_cost - additional_discount

        # Total amount is sum of discounted package and discounted additional cost
        total_amount = final_package_amount + final_additional_cost

        # Load payments and members data
        payments_df = read_sheet('payments')
        members_df = read_sheet('members')
        
        # Convert member_id to string for comparison
        members_df['member_id'] = members_df['member_id'].astype(str)
        member_data = members_df[members_df['member_id'] == str(member_id)].iloc[0]
        
        # Create new payment record
        payment_date = request.form.get('payment_date')
        if payment_date:
            payment_date = datetime.strptime(payment_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        else:
            payment_date = datetime.now().strftime('%d-%m-%Y')

        new_payment = {
            'member_id': member_id,
            'member_name': member_data['name'],
            'package': member_data['package'],
            'amount': package_amount,
            'additional_cost': additional_cost,
            'package_discount': package_discount,
            'additional_discount': additional_discount,
            'date': payment_date,
            'comments': comments,
            'status': 'Paid',
            'remaining_days': 30,  # or calculate based on package duration
            'total': total_amount  # <-- Add this line
        }
        
        # Add new payment record
        payments_df = pd.concat([payments_df, pd.DataFrame([new_payment])], ignore_index=True)
        write_sheet('payments', payments_df)
        
        flash('Payment processed successfully')
        return redirect(url_for('payments'))
        
    except Exception as e:
        app.logger.error(f"Error processing payment: {str(e)}")
        flash(f'Error processing payment: {str(e)}')
        return redirect(url_for('payments'))




# Receptionist management routes
@app.route('/admin/receptionists')
def manage_receptionists():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get and process privileges
        privileges = session.get('privileges', '')
        if isinstance(privileges, str):
            privileges = [p.strip() for p in privileges.split(',') if p.strip()]
        
        # Check access rights
        if session['user_type'] != 'admin' and 'staff' not in privileges:
            flash('Access denied')
            return redirect(url_for('staff_dashboard'))
        
        # Read staff data from Google Sheets
        staff_df = read_sheet('receptionists')
        return render_template('admin/staff.html', 
                             staff=staff_df.to_dict('records'),
                             is_admin=session['user_type'] == 'admin',
                             user_privileges=privileges)
    except Exception as e:
        app.logger.error(f"Error loading staff data: {e}")
        flash('Error loading staff data')
        return redirect(url_for('staff_dashboard'))

@app.route('/admin/staff/add', methods=['POST'])
def add_staff():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get and process privileges
        privileges = session.get('privileges', '')
        if isinstance(privileges, str):
            privileges = [p.strip() for p in privileges.split(',') if p.strip()]
        
        # Check access rights
        if session['user_type'] != 'admin' and 'staff' not in privileges:
            flash('Access denied')
            return redirect(url_for('staff_dashboard'))
            
        # Read staff data from Google Sheets
        receptionists_df = read_sheet('receptionists')
        
        # Get form data
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        name = request.form.get('name', '').strip()
        
        # Validate required fields
        if not username or not password or not name:
            flash('Username, password, and name are required')
            return redirect(url_for('manage_receptionists'))
        
        # Check for duplicate username
        if not receptionists_df.empty and username in receptionists_df['username'].values:
            flash('Username already exists')
            return redirect(url_for('manage_receptionists'))
        
        # Get permissions
        permissions = []
        for perm in ['members', 'member_attendance', 'staff_attendance', 
                    'payments', 'reports', 'staff', 'sales', 
                    'inventory', 'packages']:
            if request.form.get(f'perm_{perm}'):
                permissions.append(perm)
        
        # Create new staff record
        new_staff = {
            'username': username,
            'password': password,
            'name': name,
            'phone': request.form.get('phone', ''),
            'address': request.form.get('address', ''),
            'dob': request.form.get('dob', ''),
            'age': request.form.get('age', 0),
            'gender': request.form.get('gender', ''),
            'salary': request.form.get('salary', 0),
            'next_of_kin_name': request.form.get('next_of_kin_name', ''),
            'next_of_kin_phone': request.form.get('next_of_kin_phone', ''),
            'privileges': ','.join(permissions),
            'staff_type': request.form.get('staff_type', 'staff')
        }
        
        # Add new staff member
        receptionists_df = pd.concat([receptionists_df, pd.DataFrame([new_staff])], 
                                   ignore_index=True)
        write_sheet('receptionists', receptionists_df)
        flash('Staff member added successfully')
        
    except Exception as e:
        app.logger.error(f"Error adding staff member: {str(e)}")
        flash(f'Error adding staff member: {str(e)}')
    
    return redirect(url_for('manage_receptionists'))


@app.route('/admin/staff/edit/<username>', methods=['GET', 'POST'])
def edit_staff(username):
    # Allow both admin and staff with staff management privilege
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    if session['user_type'] != 'admin' and 'staff' not in session.get('privileges', []):
        flash('Access denied')
        return redirect(url_for('staff_dashboard'))
    
    try:
        receptionists_df = pd.read_excel('data/receptionists.xlsx')
        staff_data = receptionists_df[receptionists_df['username'] == username]
        
        if staff_data.empty:
            flash('Staff member not found')
            return redirect(url_for('manage_receptionists'))
            
        if request.method == 'GET':
            staff = staff_data.iloc[0].to_dict()
            # Convert privileges string to list, handling empty or None values
            if pd.isna(staff['privileges']) or staff['privileges'] == '':
                staff['privileges'] = []
            else:
                staff['privileges'] = staff['privileges'].split(',')
            return render_template('admin/edit_staff.html', staff=staff)
        
        # Handle POST request - Updated permissions list
        permissions = []
        permission_fields = [
            'perm_members', 'perm_member_attendance', 'perm_staff_attendance',
            'perm_payments', 'perm_reports', 'perm_staff', 'perm_sales', 
            'perm_inventory', 'perm_packages'
        ]
        
        for perm in permission_fields:
            if request.form.get(perm):
                permissions.append(perm.replace('perm_', ''))
        
        # Update staff information
        mask = receptionists_df['username'] == username
        update_fields = {
            'name': request.form.get('name'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'dob': request.form.get('dob'),
            'age': request.form.get('age'),
            'gender': request.form.get('gender'),
            'salary': request.form.get('salary'),
            'next_of_kin_name': request.form.get('next_of_kin_name'),
            'next_of_kin_phone': request.form.get('next_of_kin_phone'),
            'staff_type': request.form.get('staff_type'),
            'privileges': ','.join(permissions)
        }
        
        for field, value in update_fields.items():
            receptionists_df.loc[mask, field] = value
        
        receptionists_df.to_excel('data/receptionists.xlsx', index=False)
        flash('Staff member updated successfully')
        return redirect(url_for('manage_receptionists'))
        
    except Exception as e:
        app.logger.error(f"Error updating staff member: {str(e)}")
        flash(f'Error updating staff member: {str(e)}')
        return redirect(url_for('manage_receptionists'))


@app.route('/admin/receptionists/delete/<username>')
def delete_receptionist(username):
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        if not os.path.exists('data/receptionists.xlsx'):
            flash('No staff records found')
            return redirect(url_for('manage_receptionists'))
        
        receptionists_df = pd.read_excel('data/receptionists.xlsx')
        
        # Check if staff member exists
        if username not in receptionists_df['username'].values:
            flash('Staff member not found')
            return redirect(url_for('manage_receptionists'))
        
        # Delete staff member
        receptionists_df = receptionists_df[receptionists_df['username'] != username]
        receptionists_df.to_excel('data/receptionists.xlsx', index=False)
        flash('Staff member deleted successfully')
        
    except Exception as e:
        app.logger.error(f"Error deleting staff member: {str(e)}")
        flash('Error deleting staff member')
    
    return redirect(url_for('manage_receptionists'))





# Reports routes
@app.route('/reports')
def reports():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        selected_date = request.args.get('date')
        if not selected_date:
            selected_date = datetime.now(PKT).strftime('%Y-%m')
        
        # Handle download request
        if request.args.get('download'):
            return generate_monthly_report(selected_date)
            
        year, month = map(int, selected_date.split('-'))
        backup_file = os.path.join('data', 'gym_data_backup.xlsx')
        
        # Initialize variables
        monthly_revenue = 0
        monthly_sales_revenue = 0
        staff_attendance_details = []
        member_attendance_details = []
        sales_details = []
        payments_details = []
        inventory_details = []
        custom_products_details = []
        packages_details = []
        
        with pd.ExcelFile(backup_file) as xls:
            # Process each available sheet
            for sheet_name in xls.sheet_names:
                try:
                    df = pd.read_excel(xls, sheet_name)
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        month_mask = (df['date'].dt.month == month) & (df['date'].dt.year == year)
                        filtered_df = df[month_mask]
                        
                        if sheet_name == 'Member Attendance':
                            member_attendance_details = filtered_df.to_dict('records')
                        elif sheet_name == 'Staff Attendance':
                            staff_attendance_details = filtered_df.to_dict('records')
                        elif sheet_name == 'Sales':
                            sales_details = filtered_df.to_dict('records')
                            monthly_sales_revenue = filtered_df['total_amount'].sum() if not filtered_df.empty else 0
                        elif sheet_name == 'Payments':
                            payments_details = filtered_df.to_dict('records')
                            monthly_revenue = filtered_df['amount'].sum() if not filtered_df.empty else 0
                    else:
                        # For sheets without dates, get all records
                        if sheet_name == 'Inventory':
                            inventory_details = df.to_dict('records')
                        elif sheet_name == 'Custom Products':
                            custom_products_details = df.to_dict('records')
                        elif sheet_name == 'Packages':
                            packages_details = df.to_dict('records')
                            
                except Exception as e:
                    app.logger.error(f"Error processing sheet {sheet_name}: {str(e)}")

        # Read live data from Google Sheets
        member_attendance_details = read_sheet('attendance').to_dict('records')
        staff_attendance_details = read_sheet('trainer_attendance').to_dict('records')
        sales_df = read_sheet('sales')
        payments_df = read_sheet('payments')
        inventory_details = read_sheet('inventory').to_dict('records')
        custom_products_details = read_sheet('custom_products').to_dict('records')
        packages_details = read_sheet('packages').to_dict('records')

        # Filter by selected month/year
        year, month = map(int, selected_date.split('-'))

        def filter_by_month(df, date_col='date', fmt='%d-%m-%Y'):
            if df.empty or date_col not in df.columns:
                return df
            df[date_col] = pd.to_datetime(df[date_col], format=fmt, errors='coerce')
            return df[(df[date_col].dt.month == month) & (df[date_col].dt.year == year)]

        member_attendance_details = filter_by_month(pd.DataFrame(member_attendance_details)).to_dict('records')
        staff_attendance_details = filter_by_month(pd.DataFrame(staff_attendance_details)).to_dict('records')
        sales_details = filter_by_month(sales_df, 'date', '%d-%m-%Y %H:%M:%S').to_dict('records')
        payments_details = filter_by_month(payments_df).to_dict('records')

        monthly_sales_revenue = sales_df['total_amount'].sum() if not sales_df.empty and 'total_amount' in sales_df.columns else 0
        monthly_revenue = payments_df['total'].sum() if not payments_df.empty and 'total' in payments_df.columns else 0

        return render_template('reports.html',
                             selected_date=selected_date,
                             monthly_revenue=monthly_revenue,
                             monthly_sales_revenue=monthly_sales_revenue,
                             total_revenue=monthly_revenue + monthly_sales_revenue,
                             staff_attendance_details=staff_attendance_details,
                             member_attendance_details=member_attendance_details,
                             sales_details=sales_details,
                             payments_details=payments_details,
                             inventory_details=inventory_details,
                             custom_products_details=custom_products_details,
                             packages_details=packages_details)

    except Exception as e:
        app.logger.error(f"Error in reports: {str(e)}")
        flash('Error loading reports')
        return redirect(url_for('staff_dashboard'))



def generate_monthly_report(selected_date):
    try:
        year, month = map(int, selected_date.split('-'))
        backup_file = os.path.join('data', 'gym_data_backup.xlsx')
        
        # Create a new Excel file for the report
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            with pd.ExcelFile(backup_file) as xls:
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name)
                    
                    if 'date' in df.columns:
                        # Convert date column to datetime
                        df['date'] = pd.to_datetime(df['date'])
                        # Filter data for selected month
                        month_mask = (df['date'].dt.month == month) & (df['date'].dt.year == year)
                        filtered_df = df[month_mask]
                        
                        # Convert date back to string format before saving
                        if not filtered_df.empty:
                            if sheet_name == 'Sales':
                                filtered_df['date'] = filtered_df['date'].dt.strftime('%d-%m-%Y %H:%M:%S')
                            else:
                                filtered_df['date'] = filtered_df['date'].dt.strftime('%d-%m-%Y')
                        
                        filtered_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    else:
                        # For sheets without dates, include all data
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'gym_report_{selected_date}.xlsx'
        )
        
    except Exception as e:
        app.logger.error(f"Error generating monthly report: {str(e)}")
        flash('Error generating report')
        return redirect(url_for('reports'))


@app.route('/inventory')
def inventory():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        inventory_df = read_sheet('inventory')
        custom_products_df = read_sheet('custom_products')
        return render_template('inventory.html', 
                             inventory=inventory_df.to_dict('records'),
                             custom_products=custom_products_df.to_dict('records'))
    except Exception as e:
        app.logger.error(f"Error reading inventory file: {e}")
        flash('Error loading inventory data')
        return redirect(url_for('login'))

@app.route('/inventory/add', methods=['POST'])
def add_inventory():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        inventory_df = read_sheet('inventory')
        new_item = {
            'id': str(len(inventory_df) + 1),
            'stock_type': request.form.get('stock_type'),
            'servings': int(request.form.get('servings')),
            'cost_per_serving': float(request.form.get('cost_per_serving')),
            'profit_per_serving': float(request.form.get('profit_per_serving')),
            'other_charges': float(request.form.get('other_charges')),
            'date_added': datetime.now().strftime('%d-%m-%Y')
        }
        
        inventory_df = pd.concat([inventory_df, pd.DataFrame([new_item])], ignore_index=True)
        write_sheet('inventory', inventory_df)
        flash('Inventory item added successfully')
    except Exception as e:
        app.logger.error(f"Error adding inventory item: {e}")
        flash('Error adding inventory item')
    
    return redirect(url_for('inventory'))

@app.route('/inventory/edit/<item_id>', methods=['GET', 'POST'])
def edit_inventory(item_id):
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        inventory_df = read_sheet('inventory')
        
        if request.method == 'POST':
            inventory_df.loc[inventory_df['id'].astype(str) == str(item_id), 'stock_type'] = request.form.get('stock_type')
            inventory_df.loc[inventory_df['id'].astype(str) == str(item_id), 'servings'] = int(request.form.get('servings'))
            inventory_df.loc[inventory_df['id'].astype(str) == str(item_id), 'cost_per_serving'] = float(request.form.get('cost_per_serving'))
            inventory_df.loc[inventory_df['id'].astype(str) == str(item_id), 'profit_per_serving'] = float(request.form.get('profit_per_serving'))
            inventory_df.loc[inventory_df['id'].astype(str) == str(item_id), 'other_charges'] = float(request.form.get('other_charges'))
            
            write_sheet('inventory', inventory_df)
            flash('Inventory item updated successfully')
            return redirect(url_for('inventory'))
        
        item = inventory_df[inventory_df['id'].astype(str) == str(item_id)].iloc[0]
        return render_template('edit_inventory.html', item=item.to_dict())
    except Exception as e:
        app.logger.error(f"Error editing inventory item: {e}")
        flash('Error updating inventory item')
        return redirect(url_for('inventory'))

@app.route('/inventory/delete/<item_id>')
def delete_inventory(item_id):
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        inventory_df = read_sheet('inventory')
        inventory_df = inventory_df[inventory_df['id'].astype(str) != str(item_id)]
        write_sheet('inventory', inventory_df)
        flash('Inventory item deleted successfully')
    except Exception as e:
        app.logger.error(f"Error deleting inventory item: {e}")
        flash('Error deleting inventory item')
    
    return redirect(url_for('inventory'))




@app.route('/sales', methods=['GET', 'POST'])
def sales():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        # Initialize or get item count from session
        if request.method == 'POST' and 'add_more_items' in request.form:
            session['item_count'] = session.get('item_count', 1) + 1
        elif request.method == 'GET':
            session['item_count'] = 1

        # Load data
        inventory_df = read_sheet('inventory')
        sales_df = read_sheet('sales')
        
        # Load custom products from Google Sheets
        custom_products = []
        try:
            custom_products_df = read_sheet('custom_products')
            custom_products = custom_products_df.fillna('').to_dict('records')
        except Exception as e:
            app.logger.error(f"Error loading custom products: {str(e)}")
            flash('Warning: Could not load custom products')

        return render_template('sales.html',
                             inventory=inventory_df.to_dict('records'),
                             custom_products=custom_products,
                             recent_sales=sales_df.tail(10).to_dict('records'),
                             item_count=session.get('item_count', 1))

    except Exception as e:
        app.logger.error(f"Error in sales: {str(e)}")
        flash('Error loading sales data')
        return redirect(url_for('staff_dashboard'))


@app.template_filter('from_json')
def from_json(value):
    return json.loads(value)


@app.route('/sales/add', methods=['POST'])
def add_sale():
    try:
        # Load necessary data
        sales_df = read_sheet('sales') if os.path.exists('data/sales.xlsx') else pd.DataFrame()
        inventory_df = read_sheet('inventory')
        custom_products_df = read_sheet('custom_products')
        
        # Generate new sale ID
        new_id = 1 if len(sales_df) == 0 else int(sales_df['id'].max()) + 1
        
        # Get form data
        payment_method = request.form.get('payment_method')
        total_amount = float(request.form.get('total_amount').replace('Rs. ', ''))
        items_data = json.loads(request.form.get('items'))
        
        # Process each item and update inventory
        for item_id, item_details in items_data:
            quantity = int(item_details['quantity'])
            
            if item_id.startswith('R_'):  # Regular inventory item
                inventory_id = int(item_id.split('_')[1])
                # Update inventory servings
                mask = inventory_df['id'].astype(str) == str(inventory_id)
                if not mask.any():
                    raise Exception(f"Inventory item {inventory_id} not found")
                
                current_servings = inventory_df.loc[mask, 'servings'].iloc[0]
                if current_servings < quantity:
                    raise Exception(f"Insufficient stock for {item_details['name']}")
                
                inventory_df.loc[mask, 'servings'] = current_servings - quantity
                
            elif item_id.startswith('C_'):  # Custom product
                product_id = int(item_id.split('_')[1])
                custom_product = custom_products_df[custom_products_df['product_id'] == product_id].iloc[0]
                ingredients = json.loads(custom_product['ingredients'])
                
                # Update inventory for each ingredient
                for ingredient in ingredients:
                    inv_id = ingredient['id']
                    ing_quantity = float(ingredient['quantity']) * quantity
                    
                    mask = inventory_df['id'].astype(str) == str(inv_id)
                    if not mask.any():
                        raise Exception(f"Ingredient {inv_id} not found")
                    
                    current_servings = inventory_df.loc[mask, 'servings'].iloc[0]
                    if current_servings < ing_quantity:
                        raise Exception(f"Insufficient stock for ingredient in {item_details['name']}")
                    
                    inventory_df.loc[mask, 'servings'] = current_servings - ing_quantity
        
        # Save updated inventory
        write_sheet('inventory', inventory_df)
        
        # Create sale record
        new_sale = {
            'id': new_id,
            'date': datetime.now(PKT).strftime('%d-%m-%Y %H:%M:%S'),
            'staff_name': session.get('username'),
            'total_amount': total_amount,
            'payment_method': payment_method,
            'items_details': json.dumps([{
                'name': item[1]['name'],
                'quantity': item[1]['quantity'],
                'price': item[1]['price'],
                'total': item[1]['subtotal']
            } for item in items_data])
        }
        
        # Save sale record
        if len(sales_df) == 0:
            sales_df = pd.DataFrame(columns=['id', 'date', 'staff_name', 'total_amount', 'payment_method', 'items_details'])
        sales_df = pd.concat([sales_df, pd.DataFrame([new_sale])], ignore_index=True)
        write_sheet('sales', sales_df)
        
        return jsonify({
            'success': True,
            'redirect': url_for('sales')
        })
        
    except Exception as e:
        app.logger.error(f"Error in add_sale: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@app.route('/sales/report')
def sales_report():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        sales_df = read_sheet('sales')
        
        # Convert date strings to datetime objects
        sales_df['date'] = pd.to_datetime(sales_df['date'], format='%d-%m-%Y %H:%M:%S')
        
        # Get date range from query parameters or use current date
        start_date = pd.to_datetime(request.args.get('start_date', datetime.now().strftime('%d-%m-%Y')), format='%d-%m-%Y')
        end_date = pd.to_datetime(request.args.get('end_date', datetime.now().strftime('%d-%m-%Y')), format='%d-%m-%Y')
        
        # Filter sales by date range
        filtered_sales = sales_df[
            (sales_df['date'].dt.date >= start_date.date()) & 
            (sales_df['date'].dt.date <= end_date.date())
        ]
        
        # Process sales data for report
        report_data = []
        total_amount = 0
        
        for _, sale in filtered_sales.iterrows():
            if sale['items_details']:
                items = json.loads(sale['items_details'])
                for item in items:
                    report_data.append({
                        'date': sale['date'],
                        'product': item['name'],
                        'quantity': item['quantity'],
                        'price': item['price'],
                        'total': item['total']
                    })
                    total_amount += item['total']
        
        return render_template('sales_report.html',
                             report_data=report_data,
                             total_amount=total_amount,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        app.logger.error(f"Error generating sales report: {e}")
        flash('Error generating sales report')
        return redirect(url_for('sales'))


@app.route('/receipt/download', methods=['POST'])
def download_receipt():
    try:
        receipt_id = request.form.get('receipt_id')
        sales_df = read_sheet('sales')
        sale = sales_df[sales_df['id'] == int(receipt_id)].iloc[0]
        items = json.loads(sale['items_details'])
        
        # Create PDF using reportlab
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        
        # Add receipt content
        p.drawString(100, 800, "Gym Management System")
        p.drawString(100, 780, f"Receipt #{receipt_id}")
        p.drawString(100, 760, f"Date: {sale['date']}")
        p.drawString(100, 740, f"Staff: {sale['staff_name']}")
        
        y = 700
        for item in items:
            p.drawString(100, y, f"{item['name']} x{item['quantity']} - Rs. {item['total']}")
            y -= 20
            
        p.drawString(100, y-20, f"Total Amount: Rs. {sale['total_amount']}")
        p.drawString(100, y-40, f"Payment Method: {sale['payment_method']}")
        
        p.save()
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'receipt_{receipt_id}.pdf'
        )
    except Exception as e:
        app.logger.error(f"Error generating receipt PDF: {str(e)}")
        return jsonify({'error': 'Failed to generate receipt'}), 500

@app.route('/receipt/print', methods=['POST'])
def print_receipt():
    try:
        receipt_id = request.form.get('receipt_id')
        sales_df = read_sheet('sales')
        sale = sales_df[sales_df['id'] == int(receipt_id)].iloc[0]
        items = json.loads(sale['items_details'])
        
        return render_template('print_receipt.html', 
                             sale=sale.to_dict(),
                             items=items)
    except Exception as e:
        app.logger.error(f"Error generating printable receipt: {str(e)}")
        return jsonify({'error': 'Failed to generate receipt'}), 500


@app.route('/receipt/<int:sale_id>')
def view_receipt(sale_id):
    try:
        # Load sales data
        sales_df = read_sheet('sales')
        sale = sales_df[sales_df['id'] == sale_id].iloc[0]
        
        # Parse items from JSON string
        items = json.loads(sale['items_details'])
        
        return render_template('receipt.html', 
                             sale=sale.to_dict(),
                             items=items)
    except Exception as e:
        app.logger.error(f"Error viewing receipt: {str(e)}")
        flash('Error viewing receipt')
        return redirect(url_for('sales'))

        
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                flash('New passwords do not match')
                return redirect(url_for('change_password'))
            
            # Load appropriate Excel file based on user type
            file_path = 'data/admin.xlsx' if session['user_type'] == 'admin' else 'data/receptionists.xlsx'
            df = read_sheet(file_path)
            
            # Verify current password
            user_row = df[df['username'] == session['username']]
            if user_row.empty or user_row.iloc[0]['password'] != current_password:
                flash('Current password is incorrect')
                return redirect(url_for('change_password'))
            
            # Update password
            df.loc[df['username'] == session['username'], 'password'] = new_password
            write_sheet(file_path, df)
            
            flash('Password changed successfully')
            return redirect(url_for('admin_dashboard' if session['user_type'] == 'admin' else 'staff_dashboard'))
            
        except Exception as e:
            flash('Error changing password')
            return redirect(url_for('change_password'))
    
    return render_template('change_password.html')




# Define timezone
PKT = pytz.timezone('Asia/Karachi')  # UTC+05:00

# Update the create_backup function
def create_backup():
    try:
        data_path = 'data'
        backup_dir = os.path.join(data_path, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now(PKT).strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'gym_data_backup_{timestamp}.xlsx')
        latest_backup = os.path.join(data_path, 'gym_data_backup.xlsx')
        
        with pd.ExcelWriter(backup_file, engine='openpyxl') as writer:
            # Members
            try:
                members_df = read_sheet('members')
                members_df.to_excel(writer, sheet_name='Members', index=False)
                app.logger.info("Successfully backed up members data")
            except Exception as e:
                app.logger.error(f"Error backing up members: {e}")
                pd.DataFrame().to_excel(writer, sheet_name='Members', index=False)

            # Member Attendance
            try:
                attendance_df = read_sheet('attendance')
                if 'date' in attendance_df.columns:
                    attendance_df['date'] = pd.to_datetime(attendance_df['date']).dt.strftime('%d-%m-%Y')
                attendance_df.to_excel(writer, sheet_name='Member Attendance', index=False)
                app.logger.info("Successfully backed up member attendance data")
            except Exception as e:
                app.logger.error(f"Error backing up member attendance: {e}")
                pd.DataFrame(columns=['member_id', 'date', 'check_in', 'check_out']).to_excel(
                    writer, sheet_name='Member Attendance', index=False)

            # Staff Attendance
            try:
                trainer_attendance_df = read_sheet('trainer_attendance')
                if 'date' in trainer_attendance_df.columns:
                    trainer_attendance_df['date'] = pd.to_datetime(trainer_attendance_df['date']).dt.strftime('%d-%m-%Y')
                trainer_attendance_df.to_excel(writer, sheet_name='Staff Attendance', index=False)
                app.logger.info("Successfully backed up staff attendance data")
            except Exception as e:
                app.logger.error(f"Error backing up staff attendance: {e}")
                pd.DataFrame(columns=['trainer_id', 'date', 'check_in', 'check_out']).to_excel(
                    writer, sheet_name='Staff Attendance', index=False)

            # Sales
            try:
                sales_df = read_sheet('sales')
                if 'date' in sales_df.columns:
                    sales_df['date'] = pd.to_datetime(sales_df['date']).dt.strftime('%d-%m-%Y %H:%M:%S')
                sales_df.to_excel(writer, sheet_name='Sales', index=False)
                app.logger.info("Successfully backed up sales data")
            except Exception as e:
                app.logger.error(f"Error backing up sales: {e}")
                pd.DataFrame(columns=['id', 'date', 'staff_name', 'total_amount', 'payment_method', 'items_details']).to_excel(
                    writer, sheet_name='Sales', index=False)

            # Payments
            try:
                payments_df = read_sheet('payments')
                if 'date' in payments_df.columns:
                    payments_df['date'] = pd.to_datetime(payments_df['date']).dt.strftime('%d-%m-%Y')
                payments_df.to_excel(writer, sheet_name='Payments', index=False)
                app.logger.info("Successfully backed up payments data")
            except Exception as e:
                app.logger.error(f"Error backing up payments: {e}")
                pd.DataFrame(columns=['member_id', 'member_name', 'package', 'amount', 'date', 'status']).to_excel(
                    writer, sheet_name='Payments', index=False)

            # Inventory
            try:
                inventory_df = read_sheet('inventory')
                inventory_df.to_excel(writer, sheet_name='Inventory', index=False)
                app.logger.info("Successfully backed up inventory data")
            except Exception as e:
                app.logger.error(f"Error backing up inventory: {e}")
                pd.DataFrame().to_excel(writer, sheet_name='Inventory', index=False)

            # Custom Products
            try:
                custom_products_df = read_sheet('custom_products')
                custom_products_df.to_excel(writer, sheet_name='Custom Products', index=False)
                app.logger.info("Successfully backed up custom products data")
            except Exception as e:
                app.logger.error(f"Error backing up custom products: {e}")
                pd.DataFrame().to_excel(writer, sheet_name='Custom Products', index=False)

            # Packages
            try:
                packages_df = read_sheet('packages')
                packages_df.to_excel(writer, sheet_name='Packages', index=False)
                app.logger.info("Successfully backed up packages data")
            except Exception as e:
                app.logger.error(f"Error backing up packages: {e}")
                pd.DataFrame().to_excel(writer, sheet_name='Packages', index=False)

            # Staff/Receptionists
            try:
                staff_df = read_sheet('receptionists')
                staff_df.to_excel(writer, sheet_name='Staff', index=False)
                app.logger.info("Successfully backed up staff data")
            except Exception as e:
                app.logger.error(f"Error backing up staff: {e}")
                pd.DataFrame().to_excel(writer, sheet_name='Staff', index=False)

        # Copy the backup file to latest_backup
        import shutil
        shutil.copy2(backup_file, latest_backup)
        
        app.logger.info(f"Backup created successfully at {datetime.now(PKT).strftime('%d-%m-%Y %H:%M:%S %Z')}")
        
    except Exception as e:
        app.logger.error(f"Error creating backup: {str(e)}")

def cleanup_old_backups(backup_dir):
    try:
        # Keep backups from last 7 days
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for backup_file in os.listdir(backup_dir):
            if backup_file.startswith('gym_data_backup_'):
                file_path = os.path.join(backup_dir, backup_file)
                file_date = datetime.strptime(backup_file.split('_')[3].split('.')[0], '%Y%m%d')
                
                if file_date < cutoff_date:
                    os.remove(file_path)
                    
    except Exception as e:
        app.logger.error(f"Error cleaning up old backups: {str(e)}")

# Create backup immediately when server starts
create_backup()


@app.route('/download_report/<type>/<date>')
def download_report(type, date):
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    try:
        # Load data from backup file
        backup_file = os.path.join('data', 'gym_data_backup.xlsx')
        if not os.path.exists(backup_file):
            flash('No backup data available')
            return redirect(url_for('reports'))

        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            with pd.ExcelFile(backup_file) as xls:
                # Process each sheet from backup
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name)
                    
                    # Filter by date if the sheet has a date column
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        month_mask = df['date'].dt.strftime('%m-%Y') == date
                        df = df[month_mask]
                    
                    # Write to new Excel file
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'gym_report_{date}.xlsx'
        )
            
    except Exception as e:
        app.logger.error(f"Error generating report: {str(e)}")
        flash('Error generating report')
        return redirect(url_for('reports'))



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)


# Move the API endpoint before the if __name__ == '__main__' line
@app.route('/api/inventory')
def api_inventory():
    try:
        inventory_df = read_sheet('inventory')
        inventory_data = inventory_df.to_dict('records')
        return json.dumps(inventory_data)
    except Exception as e:
        app.logger.error(f"Error fetching inventory data: {e}")
        return json.dumps([])

def handle_sheets_error(e):
    app.logger.error(f"Google Sheets Error: {str(e)}")
    if "quota" in str(e).lower():
        flash("Service temporarily unavailable. Please try again later.")
    else:
        flash("Error accessing data. Please contact support.")
    return redirect(url_for('staff_dashboard'))

@app.route('/test-sheets')
def test_sheets():
    try:
        # Test reading from members sheet
        members_df = read_sheet('members')
        return jsonify({
            'status': 'success',
            'message': 'Successfully connected to Google Sheets',
            'sample_data': members_df.head().to_dict('records')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

import time

staff_cache = {'data': None, 'timestamp': 0}
CACHE_DURATION = 60  # seconds

def get_staff_data():
    now = time.time()
    if staff_cache['data'] is None or now - staff_cache['timestamp'] > CACHE_DURATION:
        staff_cache['data'] = read_sheet('receptionists')
        staff_cache['timestamp'] = now
    return staff_cache['data']




