import streamlit as st
from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Initialize Flask app within Streamlit
app = Flask(__name__)

# Function to format postcode
def format_postcode(postcode):
    postcode = postcode.replace(" ", "").upper()  # Remove spaces and convert to uppercase
    if len(postcode) > 3:
        return postcode[:-3] + " " + postcode[-3:]  # Insert space before the last three characters
    return postcode

# Function to scrape addresses based on postcode
def scrape_addresses(postcode):
    url = f"https://www.192.com/places/b/{postcode[:3]}/{postcode}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        address_elements = soup.select('td.js-ont-full-address.ont-hidden-on-smaller-than-tablet')
        last_sold_dates = soup.select('td:nth-child(3)')
        last_sold_prices = soup.select('td:nth-child(4)')
        addresses = [elem.get_text(strip=True) for elem in address_elements]
        sold_dates = [date.get_text(strip=True) for date in last_sold_dates]
        sold_prices = [price.get_text(strip=True) for price in last_sold_prices]
        return list(zip(addresses, sold_dates, sold_prices))
    except requests.RequestException as e:
        return {"error": f"Failed to retrieve data: {e}"}

# Function to fetch energy rating
def fetch_energy_rating(postcode, house_number):
    url = f"https://find-energy-certificate.service.gov.uk/find-a-certificate/search-by-postcode?postcode={postcode.replace(' ', '+')}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        addresses = soup.select("a[href*='certificate']")
        for addr in addresses:
            if house_number in addr.text:
                parent_row = addr.find_parent("tr")
                energy_rating = parent_row.select_one("td:nth-child(2)").get_text(strip=True)
                valid_until = parent_row.select_one("td:nth-child(3)").get_text(strip=True)
                return energy_rating, valid_until
        return "Not found", "Not found"
    except requests.RequestException as e:
        st.error(f"Failed to retrieve energy rating: {e}")
        return "Error", "Error"

# API endpoint to get address data
@app.route('/get_address_data', methods=['GET'])
def get_address_data():
    postcode = request.args.get('postcode')
    if not postcode:
        return jsonify({"error": "Postcode not provided"}), 400

    # Process the postcode using your existing logic to get data
    formatted_postcode = format_postcode(postcode)
    addresses_data = scrape_addresses(formatted_postcode)

    if addresses_data:
        return jsonify({"addresses": addresses_data}), 200
    else:
        return jsonify({"error": "No addresses found"}), 404

# Streamlit UI Interface (Optional for Testing)
def main():
    st.title("Address Finder")

    # Part 1: User enters postcode and clicks "Find Address"
    postcode = st.text_input("Enter Postcode:", "")

    if st.button("Find Address"):
        if postcode:
            formatted_postcode = format_postcode(postcode)
            addresses_data = scrape_addresses(formatted_postcode)

            if addresses_data:
                st.session_state['addresses_data'] = addresses_data
                st.success("Addresses loaded. Please select one and click 'Show Details'")
            else:
                st.warning("No addresses found for the given postcode.")
        else:
            st.warning("Please enter a valid postcode.")

    # Part 2: User selects an address and clicks "Show Details"
    if 'addresses_data' in st.session_state:
        addresses_data = st.session_state['addresses_data']
        addresses = [address for address, _, _ in addresses_data]

        selected_address = st.selectbox("Select an Address", addresses)

        if st.button("Show Details") and selected_address:
            for address, date, price in addresses_data:
                if address == selected_address:
                    st.subheader("Address Details")

                    # Split address into its components
                    parts = address.split(", ")
                    house_number = parts[0].strip()
                    address_line_1 = parts[1].strip()
                    town = parts[2].strip()
                    county = parts[-2].strip()
                    postcode = parts[-1].strip()

                    # Display the details in text inputs
                    st.text_input("House Number", value=house_number, disabled=True)
                    st.text_input("Address Line 1", value=address_line_1, disabled=True)
                    st.text_input("Town", value=town, disabled=True)
                    st.text_input("County", value=county, disabled=True)
                    st.text_input("Postcode", value=postcode, disabled=True)
                    st.text_input("Last Sold Date", value=date, disabled=True)
                    st.text_input("Last Sold Price", value=f"£{price}", disabled=True)

                    # Fetch and display energy rating and valid until date
                    energy_rating, valid_until = fetch_energy_rating(postcode, house_number)
                    st.text_input("Energy Rating", value=energy_rating, disabled=True)
                    st.text_input("Valid Until Date", value=valid_until, disabled=True)
                    break

if __name__ == '__main__':
    # If running the Streamlit app
    st.experimental_set_query_params()  # Ensures Flask routes work alongside Streamlit
    main()
    app.run(host='0.0.0.0', port=8501, debug=True)
