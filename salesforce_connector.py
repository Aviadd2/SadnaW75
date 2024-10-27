from datetime import datetime

from simple_salesforce import Salesforce

from constants import ORDER_STAGES
from utils import format_order_name, get_time


class SalesforceConnector:
    def __init__(self, sales_force_account):
        """Initialize the Salesforce connection."""
        self.sf = Salesforce(
            username=sales_force_account['username'],
            password=sales_force_account['password'],
            consumer_key=sales_force_account['consumer_key'],
            consumer_secret=sales_force_account['consumer_secret'],
            security_token=sales_force_account['security_token'],
        )
        # Dictionary to keep track of Opportunities and their stages
        self.opportunities = {}

    def create_account(self, name, phone):
        """Create an account in Salesforce."""
        account_data = {
            'Name': name,
            'Phone': phone
        }
        response = self.sf.Account.create(account_data)
        print(f"Created Account: {response['id']}")
        return response['id']

    def get_account(self, phone):
        query = f"SELECT Id FROM Account WHERE Phone = '{phone}' LIMIT 1"
        result = self.sf.query(query)

        if result['totalSize'] > 0:
            return result['records'][0]['Id']
        return None

    def create_opportunity(self, account_id, amount, order_number, description, phone_number):
        """Create an opportunity associated with an account in Salesforce."""

        order_name = format_order_name(order_number, phone_number)

        opportunity_data = {
            'Name': order_name,
            'AccountId': account_id,
            'StageName': ORDER_STAGES['ACCEPTED'],
            'Amount': amount,
            'CloseDate': get_time(),
            'Description': description,
            'OrderNumber__c': order_number
        }

        print(opportunity_data)

        response = self.sf.Opportunity.create(opportunity_data)
        print(f"Created Opportunity: {response}")

        # Add the new opportunity to the dictionary with its initial stage
        self.opportunities[response['id']] = {'name': order_number, 'stage': 'Accepted'}
        return response

    def get_opportunity_stage(self, opportunity_id):
        """Get the stage of a specific opportunity by its ID."""
        opportunity = self.sf.Opportunity.get(opportunity_id)
        return opportunity['StageName']

    def update_opportunity_stage(self, opportunity_id, new_stage):
        """Update the stage of an existing opportunity."""
        response = self.sf.Opportunity.update(opportunity_id, {'StageName': new_stage})
        print(f"Updated Opportunity {opportunity_id} to Stage: {new_stage}")

        # Update the local dictionary with the new stage
        if opportunity_id in self.opportunities:
            self.opportunities[opportunity_id]['stage'] = new_stage
        else:
            print(f"Opportunity {opportunity_id} not found in local records.")
        return response

    def get_opportunity_stage_by_name(self, order_number):
        """Get the stage of an Opportunity by its ID."""
        query = f"SELECT StageName FROM Opportunity WHERE OrderNumber__c = '{order_number}' LIMIT 1"
        result = self.sf.query(query)

        if result['totalSize'] > 0:
            return result['records'][0]['StageName']
        return None
