# SnackOverflow Square Inventory Updater: Restricts max number of changes made at once to 100
from square.client import Client
from datetime import datetime
import uuid
import sys
import os
import config

# Create an instance of the API Client 
# and initialize it with the credentials 
# for the Square account whose assets you want to manage

client = Client(
    access_token = config.access_token,
    environment = config.environment,
)

# Get an instance of the Square API you want to call
inventory_api = client.inventory
catalog_api = client.catalog

# This function takes in a costco id and returns the corresponding Square object id
def get_object_id(costco_id):
    # The payload sent to the API
    body = {}
    body['object_types'] = ['ITEM']
    body['include_deleted_objects'] = False
    body['include_related_objects'] = False
    body['query'] = {}
    body['query']['prefix_query'] = {}
    body['query']['prefix_query']['attribute_name'] = 'description'
    body['query']['prefix_query']['attribute_prefix'] = costco_id
    body['limit'] = 1

    # GET request sent to the API to request object information with the given description
    result = catalog_api.search_catalog_objects(body)

    if result.is_success():
        # Return the corresponding Square object id
        item = result.body
        key = 'objects'
        if key in item:
            return item['objects'][0]['item_data']['variations'][0]['id']
        else:
            raise LookupError(costco_id + " doesn't have a corresponding catalog object id in the Square inventory.")
    elif result.is_error():
        # Returns errors from the API call
        print("Oops an error occured...")
        raise ValueError(result.errors)

# Builds a JSON request body containing all of the items you want to update and their quantities
def build_batch_request(costco_ids_to_quantities):
    # Get a unique ID
    unique_id = uuid.uuid1()

    # Get the current time-stamp
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # The payload sent to the API
    body = {}
    body['idempotency_key'] = str(unique_id)

    # List of inventory objects that need to be updated
    body['changes'] = []

    # Index for the list of changes
    current_index = 0

    for id, quantity in costco_ids_to_quantities.items():
        # Creates a list of dictionaries for each item we want to update 
        body['changes'].append({})
        body['changes'][current_index]['type'] = 'ADJUSTMENT'
        body['changes'][current_index]['adjustment'] = {}
        body['changes'][current_index]['adjustment']['catalog_object_id'] = get_object_id(id)
        body['changes'][current_index]['adjustment']['from_state'] = 'NONE'
        body['changes'][current_index]['adjustment']['to_state'] = 'IN_STOCK'
        body['changes'][current_index]['adjustment']['location_id'] = '6G4AZ96FQ6FRP'
        body['changes'][current_index]['adjustment']['quantity'] = quantity
        body['changes'][current_index]['adjustment']['employee_id'] = '123456789'
        body['changes'][current_index]['adjustment']['occurred_at'] = current_time
        current_index += 1

    body['ignore_unchanged_counts'] = True
    return body

# POST request sent to the API to update inventory
def send_update(body):
    result = inventory_api.batch_change_inventory(body)

    if result.is_success():
        print("Done!")
    elif result.is_error():
        print("Oops an error occured...")
        raise ValueError(result.errors)

# Reads the key value pairs on the same line, line by line into a dictionary
def read_file_into_dict(abs_file_path, costco_ids_to_quantities, product_to_quantities):
    with open(abs_file_path) as f:
        for line in f:
            if not line.strip(): continue  # skip the empty line
            item_attributes = line.split()
            if len(item_attributes) != 3: raise ValueError("The text file passed in needs the format 'ID Count Name'.")
            costco_ids_to_quantities[item_attributes[0]] = item_attributes[1]
            product_to_quantities[item_attributes[2]] = item_attributes[1]

# Grabs the file the user inputted and raises an error if too many arguments were passed in
def get_file():
    num_arguments = len(sys.argv) - 1 # Holds number of command line arguments passed

    # Checks that only one argument was passed in
    if num_arguments > 1:
        raise ValueError("Too many arguments passed in. Only pass in one file at a time.")
    elif num_arguments == 0:
        # If no argument was passed in prompt the user to input one
        return input("Enter a file name: ")
    else:
        # Set the input file to the first command line argument
        return sys.argv[1]

# Checks that the file passed in is a text file and returns its full path
def get_abs_file_path(input_file):
    script_dir = os.path.dirname(__file__) # Absolute directory the script is in

    # Checks if the file passed in is a text file
    if not input_file.endswith('.txt'):
        raise ValueError("The file passed in must be a text file.")

    # Set the absolute file path of the txt file containing the parsed HTML
    return os.path.join(script_dir, input_file)

# Prints a well formatted output of the product name and quantity change requested
# Prompts the user to confirm the inventory changes printed out
def confirm_update(product_to_quantities, body):
    confirmation = ""
    yes = frozenset(["yes", "YES", "Y", "y"])
    no = frozenset(["no", "NO", "N", "n"])

    print("{:<15} {:<15}".format('Name','Changes'))
    for name, quantity in product_to_quantities.items():
        print("{:<15} {:<15}".format(name, "  + " + quantity))

    confirmation = input("Are you sure you want to update the quantities of all of these items (y/n)?: ")
    while (confirmation not in yes) and (confirmation not in no):
        print("Invalid input please try again:")
        confirmation = input("Are you sure you want to update the quantities of all of these items (y/n)?: ") 
    if confirmation in yes:
        print("The request has beeen sent! Please wait while its processing...")
        # Send update inventory request
        send_update(body)
    elif confirmation in no:
        print("The update request has been cancelled.")

# Main function
def main():
    input_file = get_file()
    abs_file_path = get_abs_file_path(input_file)
    costco_ids_to_quantities = {}
    product_to_quantities = {}

    # Fills the key value pairs in costco_ids_to_quantities with the input file
    read_file_into_dict(abs_file_path, costco_ids_to_quantities, product_to_quantities)

    # build the batch update inventory request and send it to the API  
    body = build_batch_request(costco_ids_to_quantities)

    # Prompt user for confirmation and either send or cancel the inventory change
    confirm_update(product_to_quantities, body)

# Calls main function
if __name__ == "__main__":
    main()