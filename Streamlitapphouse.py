import streamlit as st
import requests
from bs4 import BeautifulSoup
from PIL import Image
import io
from urllib.parse import urljoin


def format_postcode(postcode):
    """
    Formats the postcode by inserting a space before the last three characters if missing.
    """
    postcode = postcode.replace(" ", "").upper()  # Remove any spaces and convert to uppercase
    if len(postcode) > 3:
        return postcode[:-3] + " " + postcode[-3:]  # Insert space before the last three characters
    return postcode  # Return the original postcode if it's not long enough


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
        st.error(f"Failed to retrieve the page: {e}")
        return None


# Streamlit User Interface
st.title("Address Finder")

postcode = st.text_input("Enter Postcode:", "")

if st.button("Find Address"):
    if postcode:
        formatted_postcode = format_postcode(postcode)
        addresses_data = scrape_addresses(formatted_postcode)

        if addresses_data:
            # Get list of just addresses for the dropdown
            addresses = [address for address, date, price in addresses_data]

            # Create a dropdown to select an address
            selected_address = st.selectbox("Select an Address", addresses)

            if selected_address:
                # Find the details of the selected address
                for address, date, price in addresses_data:
                    if address == selected_address:
                        st.write(f"**Address:** {address}")
                        st.write(f"**Last Sold Date:** {date}")
                        st.write(f"**Price:** £{price}")
                        break

        else:
            st.info("No addresses found for the given postcode.")
    else:
        st.warning("Please enter a valid postcode.")
