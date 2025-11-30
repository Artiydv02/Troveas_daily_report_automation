import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from crewai.tools import BaseTool
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
import time

class UniwareAPITools(BaseTool):
    name: str = "Uniware Report Downloader"
    description: str = "Handles authentication, report creation, and downloading from Uniware API."
    
    def _get_access_token(self) -> str:
        username = os.getenv("UNIWARE_USERNAME")
        password = os.getenv("UNIWARE_PASSWORD")
        
        # Use the correct tenant name (independent of username)
        tenant = 'priyankdesigns'  # Correct tenant name
        
        # Correct API endpoint format from documentation
        url = f"https://{tenant}.unicommerce.com/oauth/token"
        params = {
            'grant_type': 'password',
            'client_id': 'my-trusted-client',
            'username': username,
            'password': password
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()['access_token']

    def _create_export_job(self, token: str) -> str:
        tenant = 'priyankdesigns'  # Correct tenant name
        url = f"https://{tenant}.unicommerce.com/services/rest/v1/export/job/create"
        headers = {
            'Content-Type': 'application/json', 
            'Authorization': f'bearer {token}',
            'facility': 'priyankdesigns'
        }
        # Include the full previous day in the export window
        yesterday = datetime.now() - timedelta(days=1)
        month_start = yesterday.replace(day=1)
        start_date = month_start.strftime('%Y-%m-%dT00:00:00Z')
        end_of_yesterday = (yesterday + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_of_yesterday.strftime('%Y-%m-%dT00:00:00Z')
        payload = {
            "exportJobTypeName": "Sale Orders",
            "exportColums": [
                "saleOrderCode", "totalPrice", "created", "channel", "status", 
                "subtotal", "tax", "discount", "currency",
                "SoiStatus", "shippingPackageStatusCode"
            ],
            # Use the documented string constant for one-time exports
            "frequency": "ONETIME",
            "exportFilters": [
                {
                    "id": "addedOn",
                    "dateRange": {
                        "start": start_date,
                        "end": end_date
                    }
                }
            ]
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()['jobCode']

    def _get_report_url(self, token: str, job_code: str) -> str:
        tenant = 'priyankdesigns'  # Correct tenant name
        url = f"https://{tenant}.unicommerce.com/services/rest/v1/export/job/status"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'bearer {token}'
        }
        payload = {"jobCode": job_code}
        
        for _ in range(10):
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            status = result.get('status')
            print(f"📊 Status check: {status}")
            
            if status in ['SUCCESSFUL', 'COMPLETE']:
                file_path = result.get('filePath')
                print(f"🔗 FilePath from API: {file_path}")
                if file_path:
                    return file_path
                else:
                    print("⚠️ Status is COMPLETE but filePath is missing!")
                    print(f"📋 Full response: {json.dumps(result, indent=2)}")
                    
            print("Report is still processing, waiting for 10 seconds...")
            time.sleep(10)
        raise Exception("Report generation timed out.")

    def _download_report(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        filename = f"uniware_sales_{datetime.now().strftime('%Y-%m-%d')}.csv"
        with open(filename, 'wb') as f:
            f.write(response.content)
        return filename

    def _run(self, **kwargs) -> str:
        try:
            # Check if credentials exist first
            username = os.getenv("UNIWARE_USERNAME")
            password = os.getenv("UNIWARE_PASSWORD")
            
            if not username or not password:
                return "Error: UNIWARE_USERNAME or UNIWARE_PASSWORD not found in .env file. Please add your Uniware credentials."
            
            print(f"🔐 Connecting to Uniware API with username: {username}")
            token = self._get_access_token()
            print("✅ Authentication successful")
            
            print("📋 Creating export job for previous day's sales...")
            job_code = self._create_export_job(token)
            print(f"📋 Job created with code: {job_code}")
            
            print("⏳ Waiting for report generation...")
            report_url = self._get_report_url(token, job_code)
            print("📥 Report ready, downloading...")
            
            downloaded_file = self._download_report(report_url)
            return f"Successfully downloaded report from Uniware. File saved as: {downloaded_file}"
        except Exception as e:
            return f"An error occurred with Uniware API: {str(e)}"

class DataAnalysisTools(BaseTool):
    name: str = "Data Analysis Tool"
    description: str = "Processes the downloaded CSV file to generate a formatted report."
    def _run(self, file_path: str = None, **kwargs) -> str:
        try:
            # If no file path provided, try to find the most recent CSV
            if not file_path:
                import glob
                csv_files = glob.glob('*.csv')
                if csv_files:
                    file_path = max(csv_files, key=os.path.getmtime)
                    print(f"No file path provided, using most recent: {file_path}")
                else:
                    return "Error: No CSV file path provided and no CSV files found"
            
            print(f"Processing file: {file_path}")
            df = pd.read_csv(file_path)
            
            # Fix column names to match actual CSV structure
            df['Order Date'] = pd.to_datetime(df['Created'], errors='coerce')
            df_filtered = df.dropna(subset=['Order Date'])
            # Normalize channel names to avoid mismatches (e.g., trailing spaces)
            if 'Channel Name' in df_filtered.columns:
                df_filtered['Channel Name'] = df_filtered['Channel Name'].astype(str).str.strip()
            # Exclude rows with blank/cancelled/unfulfillable statuses (case-insensitive)
            if 'Sale Order Status' in df_filtered.columns:
                normalized_status = (
                    df_filtered['Sale Order Status']
                    .fillna('')
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )
                df_filtered = df_filtered[~normalized_status.isin(['', 'cancelled', 'unfulfillable'])].copy()
            
            # Exclude rows where SOI Status (Sale Order Item Status) = cancelled (case-insensitive)
            # Check for multiple possible column name formats from Uniware CSV
            soi_status_col = None
            for col in df_filtered.columns:
                if 'soi' in col.lower() and 'status' in col.lower():
                    soi_status_col = col
                    break
            
            if soi_status_col:
                normalized_item_status = (
                    df_filtered[soi_status_col]
                    .fillna('')
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )
                df_filtered = df_filtered[~normalized_item_status.isin(['cancelled'])].copy()
            
            # Exclude rows where Shipping Package Status Code = returned (case-insensitive)
            # Check for multiple possible column name formats from Uniware CSV
            package_status_col = None
            for col in df_filtered.columns:
                if ('shipping' in col.lower() and 'package' in col.lower() and 'status' in col.lower()) or \
                   ('package' in col.lower() and 'status' in col.lower() and 'code' in col.lower()):
                    package_status_col = col
                    break
            
            if package_status_col:
                normalized_package_status = (
                    df_filtered[package_status_col]
                    .fillna('')
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )
                df_filtered = df_filtered[~normalized_package_status.isin(['returned'])].copy()
            
            today = datetime.now()
            previous_day = today - timedelta(days=1)
            start_of_month = today.replace(day=1)
            
            daily_df = df_filtered[df_filtered['Order Date'].dt.date == previous_day.date()]
            daily_summary = daily_df.groupby('Channel Name').agg(Qty=('Sale Order Code', 'count'), Amt=('Total Price', 'sum')).reset_index()
            
            mtd_df = df_filtered[(df_filtered['Order Date'].dt.date >= start_of_month.date()) & (df_filtered['Order Date'].dt.date <= previous_day.date())]
            mtd_summary = mtd_df.groupby('Channel Name').agg(Qty=('Sale Order Code', 'count'), Amt=('Total Price', 'sum')).reset_index()
            final_report = pd.merge(
                daily_summary,
                mtd_summary,
                on='Channel Name',
                how='outer',
                suffixes=(f'_{previous_day.strftime("%d-%m-%Y")}', '_MTD')
            ).fillna(0)

            # Append a Grand Total row across all numeric columns
            totals_row = {col: 0 for col in final_report.columns}
            totals_row['Channel Name'] = 'Grand Total'
            for col in final_report.columns:
                if col != 'Channel Name':
                    # Sum numeric columns; coerce non-numeric to 0
                    totals_row[col] = pd.to_numeric(final_report[col], errors='coerce').fillna(0).sum()
            final_report = pd.concat([final_report, pd.DataFrame([totals_row])], ignore_index=True)

            output_filename = f'Troveas_Report_{previous_day.strftime("%Y-%m-%d")}.xlsx'
            final_report.to_excel(output_filename, index=False)
            return f"Formatted report created: {output_filename}"
        except Exception as e:
            return f"Error in data analysis: {e}"

class EmailTools(BaseTool):
    name: str = "Email Sending Tool"
    description: str = "Sends an email with a file attachment."
    def _run(self, file_path: str) -> str:
        try:
            sender_email = os.getenv("EMAIL_ADDRESS")
            sender_password = os.getenv("EMAIL_PASSWORD")
            
            # Clean credentials to remove any non-ASCII characters
            if sender_email:
                sender_email = sender_email.strip().replace('\xa0', ' ')
            if sender_password:
                sender_password = sender_password.strip().replace('\xa0', ' ')

            # Determine recipients (To + CC) from knowledge file
            recipient_email = None
            cc_emails: list[str] = []
            potential_recipient_path = file_path if file_path else "knowledge/user_preference.txt"
            try:
                if potential_recipient_path and potential_recipient_path.lower().endswith('.txt') and os.path.exists(potential_recipient_path):
                    with open(potential_recipient_path, 'r', encoding='utf-8') as f:
                        raw = f.read()
                        parts = [p.strip() for p in re.split(r'[\n,;]+', raw) if p.strip()]
                        if parts:
                            recipient_email = parts[0]
                            cc_emails = parts[1:]
            except Exception:
                pass

            if not recipient_email and os.path.exists("knowledge/user_preference.txt"):
                with open("knowledge/user_preference.txt", 'r', encoding='utf-8') as f:
                    raw = f.read()
                    parts = [p.strip() for p in re.split(r'[\n,;]+', raw) if p.strip()]
                    if parts:
                        recipient_email = parts[0]
                        cc_emails = parts[1:]

            if not recipient_email:
                return "Error: Recipient email not found. Ensure 'knowledge/user_preference.txt' contains a valid email address."

            # Determine attachment path
            attachment_path = None
            if file_path and file_path.lower().endswith(('.xlsx', '.xls')) and os.path.exists(file_path):
                attachment_path = file_path
            else:
                import glob
                excel_files = glob.glob('Troveas_Report_*.xlsx')
                if excel_files:
                    attachment_path = max(excel_files, key=os.path.getmtime)

            if not attachment_path:
                return "Error: No Excel report found to attach. Expected a file like 'Troveas_Report_*.xlsx'."

            # Create message with explicit charset
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            if cc_emails:
                msg['Cc'] = ", ".join(cc_emails)
            msg['Subject'] = "Troveas Daily Business Report"
            
            # Simple ASCII-only email body
            email_body = "Dear Sir/Madam,\n\nPlease find attached the daily business report with month-to-date figures.\n\nBest regards,\nTroveas Reporting System"
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Attach file
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            filename = os.path.basename(attachment_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"',
            )
            msg.attach(part)
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            all_recipients = [recipient_email] + cc_emails
            server.sendmail(sender_email, all_recipients, msg.as_string())
            server.quit()
            
            return f"Email sent successfully to {recipient_email} with report: {filename}"
        except Exception as e:
            return f"Error sending email: {e}"

class CleanupTools(BaseTool):
    name: str = "File Cleanup Tool"
    description: str = "Deletes CSV and Excel report files from the folder after successful email delivery."
    
    def _run(self, **kwargs) -> str:
        try:
            import glob
            deleted_files = []
            
            # Find and delete CSV files (uniware_sales_*.csv)
            csv_files = glob.glob('uniware_sales_*.csv')
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    os.remove(csv_file)
                    deleted_files.append(csv_file)
                    print(f"✅ Deleted CSV file: {csv_file}")
            
            # Find and delete Excel files (Troveas_Report_*.xlsx)
            excel_files = glob.glob('Troveas_Report_*.xlsx')
            for excel_file in excel_files:
                if os.path.exists(excel_file):
                    os.remove(excel_file)
                    deleted_files.append(excel_file)
                    print(f"✅ Deleted Excel file: {excel_file}")
            
            if deleted_files:
                return f"Cleanup completed successfully. Deleted {len(deleted_files)} file(s): {', '.join(deleted_files)}"
            else:
                return "No files found to delete. Cleanup completed."
        except Exception as e:
            return f"Error during cleanup: {e}"
