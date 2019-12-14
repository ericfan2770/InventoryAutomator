from bs4 import BeautifulSoup
from datetime import datetime
import sys

#################################################
#                      ##########################
#     HELPER FUNCTIONS ##########################
#                      ##########################
#################################################
def parseDescriptionDiv(descriptionDiv):
    # This gets us Property 1 because its the first <p> tag
    itemNameString = descriptionDiv.p.get_text()
    # Confirms that itemNameString is valid by checking if "ct" is in the String
    assert "ct" in itemNameString, "Invalid String for item name. Please check itemNameString"
    # This gets us Property 2 because it is 2 siblings ahead of Property 1
    itemIDDivString = descriptionDiv.p.next_sibling.next_sibling.get_text().strip()
    # itemIDString will be a 3 element list: ["Item", "<ID>"], so we skip index 0
    itemIDString = itemIDDivString.split()
    #Confirms that itemNameString[0] is a valid item name by making sure it only contains alphabetical letters
    assert itemNameString[0].isalpha(), "Invalid item name. Please check itemNameString[0]"
    # Confirms that itemNameString[1] is a valid item ID by making sure it only contains numerical digits
    assert itemNameString[1].isdigit();

    print("Item Name: " + itemNameString)
    print("Item ID: " + itemIDString[1])

    # ID, Name
    return itemIDString[1], itemNameString

def parseQuantityDivs(quantityDivs):
    quantityOrderedTag = quantityDivs[0].p
    quantityShippedTag = quantityDivs[1].p

    quantityOrderedInt = int(quantityOrderedTag.get_text())
    quantityShippedInt = int(quantityShippedTag.get_text())

    print("Ordered: " + str(quantityOrderedInt)) 
    print("Shipped: " + str(quantityShippedInt)) # This is he value we care about

    # NumShipped, NumOrdered
    return quantityShippedInt, quantityOrderedInt

def getNameAndCount(long_name):
    name_data = long_name.split(", ")
    name = name_data[0]                            # The name is always first
    name = name.replace(" ", "_")                  # Replace spaces with "_"
    count_string = name_data[len(name_data) - 1]   # The count is always last
    count_array = count_string.split()             # Removing "ct" 
    count = count_array[0]
    return name, count

def writeToFile(id, quantity, name, file_name):
    with open(file_name + "-parsed.txt", "a+") as f:
        f.write(id + " " + str(quantity) + " " + name + "\n")

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

#################################################
#                      ##########################
#     Start of Script  ##########################
#                      ##########################
#################################################

# Gets the file input from the user
costco_html_file = get_file()

# Opens file and loads it into a BS html parser.
with open(costco_html_file) as fp:
    soup = BeautifulSoup(fp, "html.parser")
# Finds and filters all costco order item divs. Returns these item divs as a list of TAG
# objects.
itemDivs = soup.find_all("div", attrs={"class": "row invoice-item-detail-box"}, recursive=True)

for itemDiv in itemDivs:
    # Description div will contain Property 1 and Property 2
    descriptionDiv = itemDiv.find("div", attrs={"class": "col-lg-4 col-xl-4 text-left body-copy"})
    id, long_name = parseDescriptionDiv(descriptionDiv)

    # Gets the shorter name and count of each item
    name, count = getNameAndCount(long_name)

    # Quantiy div contains Property 3, but 2 divs will return (1 will be Quantity Ordered and 1 will
    # be Quantiy Shipped, which we want) so we care about quantityDivs[1] (Shipped)
    quantityDivs = itemDiv.findAll("div", attrs={"class": "col-lg-6 col-xl-6 text-center body-copy"})
    assert len(quantityDivs) == 2, "Invalid quantity. Please check quantityDivs"
    num_shipped, num_ordered = parseQuantityDivs(quantityDivs)
    print("\n")

    # Gets the quantity we need to update the inventory by
    quantity = num_shipped * int(count)

    # Removes the ".html" from the end of the file name
    file_name_arr = costco_html_file.split(".")
    file_name = file_name_arr[0]

    # Write output to a new text file
    writeToFile(id, quantity, name, file_name)

    # print(id + " " + str(num_shipped) + " " + name)
    # Print alert if Costco may not have had an item in stock
    if (num_shipped != num_ordered):
            print("Item " + name + " may have ran out of stock")

#
# Parsing information! Pay attn to The listed properties, those are the ones we need. 
# 
# Get all "row invoice-item-detail-box" tags. They willl correspond to # of items. 
# Example div:
#
# <div class="row invoice-item-detail-box">
#  <!-- Item Description -->
#  <div class="col-lg-4 col-xl-4 text-left body-copy">
#   <p>
#    Starbucks Frappuccino Coffee Drink, Mocha, 9.5 oz, 15 ct   <---- Property 1 (Name and ct)
#   </p>
#   <p class="">
#    Item 264266                                                <---- Property 2 (Item ID)
# 						 $20.99
#   </p>
#   <p class="invoice-btm-margin body-copy-green">
#    Discount
#    <span>
#     $8.00
#    </span>
#   </p>
#  </div>
#  <div class="col-lg-2 col-xl-2">
#   <!-- quantity ordered -->
#   <div class="col-lg-6 col-xl-6 text-center body-copy">
#    <p>
#     2
#    </p>
#   </div>
#   <!-- quantity shipped -->
#   <div class="col-lg-6 col-xl-6 text-center body-copy">
#    <p>
#     2                                                         <---- Property 3 (Quantity Shipped)
#    </p>
#   </div>
#  </div>
#  <!-- order status -->
#  <div class="col-lg-2 col-xl-2 text-center body-copy">
#   <p>
#    Shipped and Invoiced
#   </p>
#  </div>
#  <!-- Order Total -->
#  <div class="col-lg-2 col-xl-2 text-right body-copy">
#   $33.98
#  </div>
#  <!-- Invoice Total -->
#  <div class="col-lg-2 col-xl-2 text-right body-copy">
#   $33.98
#  </div>
#  <div class="col-xl-12 col-lg-12">
#   <div class="linerNew">
#   </div>
#  </div>
# </div>

