import requests
from constants import BASE_ICOUNT_URL


class ICountConnector:

    def __init__(self, icount_account):
        """Initialize the iCount session."""
        self.icount_account = icount_account
        self.session_id = self.get_session_id()

    def get_session_id(self):
        """Authenticate and get a session ID."""
        url = f"{BASE_ICOUNT_URL}/auth/login"
        payload = self.build_auth_payload()
        response = requests.post(url, json=payload)
        data = response.json()

        if "sid" in data:
            print("Session ID obtained:", data["sid"])
            return data["sid"]
        else:
            raise Exception(f"Failed to authenticate: {data}")

    def renew_session(self):
        """Renew the session ID if it expires."""
        self.session_id = self.get_session_id()

    def build_auth_payload(self):
        """Builds the authentication payload."""
        return {
            "cid": self.icount_account["cid"],
            "pass": self.icount_account["password"],
            "user": self.icount_account["username"]
        }

    def send_post_request(self, url, payload, headers=None):
        """Helper method to send POST requests."""
        if headers is None:
            headers = {
                "Content-Type": "application/json"
            }
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def create_client(self, client_name, client_phone):
        """Create a client in iCount."""
        url = f"{BASE_ICOUNT_URL}/client/create"
        payload = self.build_auth_payload()
        payload.update({
            "client_name": client_name,
            "phone": client_phone
        })
        data = self.send_post_request(url, payload)

        if data.get('client_id'):
            print(f"Client created successfully: {data['client_id']}")
            return data['client_id']
        else:
            print(f"Failed to create client: {data}")
            return None

    def build_document_payload(self, order_number, client_address, client_name, client_id, description,
                               total_price=None):
        """Builds the document payload for both shipping document and invoice."""
        payload = self.build_auth_payload()
        payload.update({
            "doctype": "invrec",
            "description": order_number,
            "client_address": client_address,
            "client_name": client_name,
            "tax_exempt": 1,
            "client_id": client_id,
            "items": [
                {
                    "quantity": 1,
                    "unitprice": total_price if total_price else 1,
                    "description": description
                }
            ],
            "cash": {"sum": total_price if total_price else 1}
        })
        return payload

    def create_shipping_document(self, order_number, client_address, client_name, client_id):
        """Create a shipping document in iCount."""
        url = f"{BASE_ICOUNT_URL}/doc/create"
        payload = self.build_document_payload(order_number, client_address, client_name, client_id, "מסמך משלוח")
        data = self.send_post_request(url, payload)

        print(f"Shipping document created successfully: {data.get('doc_url')}")
        return data.get('doc_url')

    def create_invoice(self, order_number, total_price, client_address, client_name, client_id):
        """Create an invoice in iCount."""
        url = f"{BASE_ICOUNT_URL}/doc/create"
        payload = self.build_document_payload(order_number, client_address, client_name, client_id, "חשבונית מס",
                                              total_price)
        data = self.send_post_request(url, payload)

        print(f"Invoice created successfully: {data.get('doc_url')}")
        return data.get('doc_url')

    def process_order_in_icount(self, client_name, client_phone, order_number, total_price, address):
        """Process an order by creating a client, shipping document, and invoice."""
        client_id = self.create_client(client_name, client_phone)
        if not client_id:
            print("Client creation failed, stopping the test.")
            return

        shipping_doc_url = self.create_shipping_document(order_number, address, client_name, client_id)
        if not shipping_doc_url:
            print("Shipping document creation failed, stopping the test.")
            return

        invoice_url = self.create_invoice(order_number, total_price, address, client_name, client_id)
        if not invoice_url:
            print("Invoice creation failed, stopping the test.")
            return

        print(
            f"iCount Process successful! Client ID: {client_id}, Shipping Document URL: {shipping_doc_url}, Invoice URL: "
            f"{invoice_url}")

        return invoice_url
