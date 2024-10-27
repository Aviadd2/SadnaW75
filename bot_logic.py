import time
from threading import Thread

from salesforce_connector import SalesforceConnector
from icount_connector import ICountConnector
from utils import fetch_messages, send_message, get_time, calculate_price, validate_address, validate_name, \
    generate_order_number, get_message_from_stage
from constants import OPTIONS_DETAILS, SALES_FORCE_ACCOUNT, ICOUNT_ACCOUNT, STORE_NAME, CHECK_INTERVAL


class Bot:
    def __init__(self):
        """Initialize the bot with Salesforce and iCount connectors and user orders."""
        self.sf_connector = SalesforceConnector(SALES_FORCE_ACCOUNT)
        self.icount_connector = ICountConnector(ICOUNT_ACCOUNT)
        self.user_orders = {}
        self.last_timestamp = get_time() - 10  # Start 10 seconds before the current time

    def ask_question(self, user_id, question, options):
        """Send a question to the user with numbered options."""
        options_text = "\n".join([f"{num}. {desc[0]}" for num, desc in options.items() if num != 'restart'])
        message = f"{question}\n{options_text}\n0. חזרה להתחלה"
        send_message(user_id, message)

    def check_if_restart(self, user_id, message):
        """Check if the message is '0' and handle resetting the order."""
        if message == '0':
            self.reset_order(user_id)
            return True
        return False

    def process_order(self, user_id):
        """Process the complete order and ask for the address."""
        order = self.user_orders[user_id]
        total_price = calculate_price(order)

        send_message(user_id,
                     f"תודה רבה על ההזמנה! המחיר הכולל יהיה: {total_price:.2f} שקלים"
                     f" אנא הכנס את הכתובת למשלוח (דוגמה: סמולנסקין 9 ירושלים)")

    def confirm_order(self, user_id):
        """Confirm the order details with the user and create Salesforce and iCount records."""
        order = self.user_orders[user_id]
        total_price = calculate_price(order)
        order_type = OPTIONS_DETAILS['type'][order['type']][0]
        amount = OPTIONS_DETAILS['amount'][order['amount']][0]
        size = OPTIONS_DETAILS['size'][order['size']][0]
        pack_description = OPTIONS_DETAILS['pack'][order['pack']][0]
        pack_quantity = order['pack_quantity']
        address = order['address']
        phone_number = order.get('phone', user_id)

        order_number = generate_order_number()

        order_summary = (
            f"Order Summary for user {user_id}:\n"
            f"Size: {size}\n"
            f"Amount: {amount}\n"
            f"Pack: {pack_description}\n"
            f"Number of Packs: {pack_quantity}\n"
            f"Type: {order_type}\n"
            f"Address: {address}\n"
            f"Phone: +{phone_number}\n"
            f"Order number: {order_number}\n"
            f"Total Price: {total_price:.2f} שקלים\n"
        )
        print(order_summary)

        send_message(user_id,
                     f"תודה רבה על ההזמנה {order['name']}! המחיר הכולל יהיה: {total_price:.2f} שקלים"
                     f". ההזמנה תישלח לכתובת: {address}."
                     f"מספר ההזמנה: {order_number}")

        # Create Salesforce records
        sf_account_id = self.sf_connector.get_account(phone_number)
        if sf_account_id is None:
            sf_account_id = self.sf_connector.create_account(order['name'], phone_number)
        is_packed = order['pack'] == '1'
        pack_description_hebrew = "ארוז" if is_packed else "לא ארוז"
        description = (f"פרטי הזמנה: סוג: {order_type}, גודל: {size}, כמות: {amount}, "
                       f"אריזה: {pack_description_hebrew}, מספר חבילות: {pack_quantity}")

        print(description)

        self.sf_connector.create_opportunity(sf_account_id, total_price,
                                             order_number, description, phone_number)

        # Process order in iCount
        invoice_url = self.icount_connector.process_order_in_icount(order['name'], phone_number, order_number,
                                                                    total_price, address)

        send_message(phone_number, invoice_url)

        # Remove the user from the order list
        self.user_orders.pop(user_id, None)

    def reset_order(self, user_id):
        """Reset the user's order and ask the first question."""
        self.user_orders[user_id] = {}
        self.ask_for_inquiry_or_order(user_id)

    def ask_for_inquiry_or_order(self, user_id):
        """Ask the user if they want to inquire about an existing order or make a new one."""
        message = (
            f"ברוך הבא ל{STORE_NAME}! נשמח לעמוד לשירותכם עם המשק האיכותי במדינה!\n"
            "האם אתה כותב לברר לגבי הזמנה קיימת או מעוניין לבצע הזמנה חדשה?\n"
            "1. לברר לגבי הזמנה קיימת\n"
            "2. לבצע הזמנה חדשה"
        )
        send_message(user_id, message)

    def ask_for_name(self, user_id):
        """Ask the user for their name in Hebrew."""
        send_message(user_id, "על שם מי ההזמנה?\n0. חזרה לתפריט הראשי.")

    def process_message(self, user_id, message):
        """Process an incoming message from a user."""
        if user_id not in ['972523265851', '972544446986',
                           '972525058586', '972528722464']:  # Todo: remove, this is to restrict to specific users for testing
            return

        if self.check_if_restart(user_id, message):
            return  # If the user wants to restart, stop further processing

        if user_id not in self.user_orders:
            self.user_orders[user_id] = {}
            self.ask_for_inquiry_or_order(user_id)  # First question: Inquire or new order
            return

        order = self.user_orders[user_id]

        # Handle the user's choice to inquire or make a new order
        if 'inquiry_or_order' not in order:
            if message == '1':
                order['inquiry_or_order'] = 'inquiry'
                send_message(user_id, "אנא הכנס את מספר ההזמנה שלך או לחץ 0 לחזרה לתפריט הראשי.")
            elif message == '2':
                order['inquiry_or_order'] = 'new_order'
                self.ask_for_name(user_id)  # Proceed with the existing order flow
            else:
                send_message(user_id, "אפשרות לא תקינה. אנא הכנס 1 לברר הזמנה קיימת או 2 לבצע הזמנה חדשה.")
                self.ask_for_inquiry_or_order(user_id)
            return

        # Handle inquiry flow
        if order['inquiry_or_order'] == 'inquiry' and 'opportunity_id' not in order:
            if message == '0':
                self.reset_order(user_id)
            else:
                opportunity_stage = self.sf_connector.get_opportunity_stage_by_name(message)
                if opportunity_stage:
                    send_message(user_id, get_message_from_stage(opportunity_stage))
                    self.user_orders.pop(user_id, None)  # End communication
                else:
                    send_message(user_id, "מספר הזמנה לא תקין. אנא נסה שוב או לחץ 0 לחזרה לתפריט הראשי.")
            return

        # Handle new order flow
        if 'name' not in order:
            if validate_name(message):
                order['name'] = message
                self.ask_question(user_id, "איזה גודל יחידה תרצה?", OPTIONS_DETAILS['size'])
            else:
                send_message(user_id, "שם לא תקין. אנא הכנס שם ללא מספרים.")
                self.ask_for_name(user_id)
        elif 'size' not in order:
            if message in OPTIONS_DETAILS['size']:
                order['size'] = message
                self.ask_question(user_id, "כמה יחידות תרצה?", OPTIONS_DETAILS['amount'])
            else:
                self.send_invalid_input_message(user_id, "איזה גודל יחידה תרצה?", OPTIONS_DETAILS['size'])
        elif 'amount' not in order:
            if message in OPTIONS_DETAILS['amount']:
                order['amount'] = message
                self.ask_question(user_id, "ארוז או לא ארוז?", OPTIONS_DETAILS['pack'])
            else:
                self.send_invalid_input_message(user_id, "כמה יחידות תרצה?", OPTIONS_DETAILS['amount'])
        elif 'pack' not in order:
            if message in OPTIONS_DETAILS['pack']:
                order['pack'] = message
                # **Modified Code: Include option to return to main menu**
                send_message(user_id, "כמה תבניות תרצה?\n0. חזרה לתפריט הראשי.")
            else:
                self.send_invalid_input_message(user_id, "ארוז או לא ארוז?", OPTIONS_DETAILS['pack'])
        elif 'pack_quantity' not in order:
            # **Modified Code: Handle '0' input for returning to main menu**
            if self.check_if_restart(user_id, message):
                return
            elif message.isdigit() and int(message) > 0:
                order['pack_quantity'] = int(message)
                self.ask_question(user_id, "איזה סוג תרצה?", OPTIONS_DETAILS['type'])
            else:
                send_message(user_id, "אנא הכנס מספר תבניות תקין (מספר שלם חיובי). או לחץ 0 לחזרה לתפריט הראשי.")
        elif 'type' not in order:
            if message in OPTIONS_DETAILS['type']:
                order['type'] = message
                self.process_order(user_id)
            else:
                self.send_invalid_input_message(user_id, "איזה סוג תרצה?", OPTIONS_DETAILS['type'])
        elif 'address' not in order:
            if validate_address(message):
                order['address'] = message
                self.confirm_order(user_id)
            else:
                send_message(user_id, "פורמט לא תקין. אנא הכנס כתובת תקינה (דוגמה: סמולנסקין 9 ירושלים).")

    def send_invalid_input_message(self, user_id, last_question, options):
        """Send a message about the invalid input and repeat the last question."""
        send_message(user_id, "תשובה לא תקינה. אנא הכנס את מספר האופציה הרלוונטי בלבד.")
        self.ask_question(user_id, last_question, options)

    def check_messages(self):
        """Continuously check for new messages and process them."""
        self.last_timestamp = get_time() - 60

        while True:
            seen_conversations = ['120363309946680980@g.us']
            messages = fetch_messages(self.last_timestamp)
            for msg in messages.get('messages', []):
                chat_id = msg['chat_id']
                if chat_id not in seen_conversations:
                    seen_conversations.append(chat_id)
                    self.handle_last_message_in_chat(msg)
            if messages.get('messages'):
                self.last_timestamp = messages['messages'][0]['timestamp']
            time.sleep(CHECK_INTERVAL)

    def handle_last_message_in_chat(self, msg):
        """Handle the last message in a chat."""
        if msg['from_me'] is False and msg.get('text'):
            message = msg['text']['body'].strip()
            user_id = msg['from']
            self.process_message(user_id, message)
    def run_message_checker(self):
        """Start a background thread to check messages."""
        Thread(target=self.check_messages).start()
