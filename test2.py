import streamlit as st
import json

# Function to format the postcode
def format_postcode(postcode):
    postcode = postcode.replace(" ", "").upper()  # Remove spaces and convert to uppercase
    if len(postcode) > 3:
        return postcode[:-3] + " " + postcode[-3:]  # Insert space before the last three characters
    return postcode

# Function to simulate address data scraping based on the postcode
def scrape_addresses(postcode):
    # Simulating data retrieval for the demonstration purposes
    addresses = [
        (f"{i} Chestnut Road, Oldbury, West Midlands, {postcode}", f"Date {i}", f"£{100000 + i * 1000}") for i in range(1, 10)
    ]
    return addresses

# Function to simulate fetching energy rating
def fetch_energy_rating(postcode, house_number):
    # Simulated data - in a real-world case, this would involve an external API
    return "D", "18 December 2028"

# Check for query parameters (API request simulation)
query_params = st.experimental_get_query_params()

# If the query parameter contains a postcode, return JSON data
if 'postcode' in query_params:
    postcode = query_params['postcode'][0]  # Extract the postcode from query parameters
    formatted_postcode = format_postcode(postcode)
    addresses_data = scrape_addresses(formatted_postcode)

    if addresses_data:
        # Return JSON response
        st.write(json.dumps({"addresses": addresses_data}))
    else:
        st.write(json.dumps({"error": "No addresses found"}))

# If no query parameters, show the normal Streamlit UI for user interaction
else:
    st.title("Address Finder")

    # User input for postcode
    postcode = st.text_input("Enter Postcode:", "")

    # Button to trigger search
    if st.button("Find Address"):
        if postcode:
            formatted_postcode = format_postcode(postcode)
            addresses_data = scrape_addresses(formatted_postcode)

            if addresses_data:
                # Display success message and the list of addresses
                st.success("Addresses loaded! Please select one below.")
                selected_address = st.selectbox("Select an Address", [address for address, _, _ in addresses_data])

                if selected_address:
                    for address, date, price in addresses_data:
                        if address == selected_address:
                            # Split address into its components
                            st.subheader("Address Details")

                            house_number = address.split(",")[0].strip()

                            # Show the individual components in non-editable text fields
                            st.text_input("Address", value=address, disabled=True)
                            st.text_input("Last Sold Date", value=date, disabled=True)
                            st.text_input("Last Sold Price", value=price, disabled=True)

                            # Fetch and show the energy rating and valid until date
                            energy_rating, valid_until = fetch_energy_rating(formatted_postcode, house_number)
                            st.text_input("Energy Rating", value=energy_rating, disabled=True)
                            st.text_input("Valid Until", value=valid_until, disabled=True)
            else:
                st.warning("No addresses found for the given postcode.")
        else:
            st.warning("Please enter a valid postcode.")
