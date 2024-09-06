import streamlit as st
import requests
from bs4 import BeautifulSoup
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


def fetch_energy_rating(postcode, house_number):
    url = f"https://find-energy-certificate.service.gov.uk/find-a-certificate/search-by-postcode?postcode={postcode.replace(' ', '+')}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

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
        st.error(f"Failed to retrieve the energy rating: {e}")
        return "Error", "Error"


# Streamlit User Interface
st.title("Address Finder")

postcode = st.text_input("Enter Postcode:", "")

if st.button("Find Address"):
    if postcode:
        formatted_postcode = format_postcode(postcode)
        addresses_data = scrape_addresses(formatted_postcode)

        if addresses_data:
            # Extract only the addresses for the dropdown
            addresses = [address for address, _, _ in addresses_data]

            # Dropdown to select an address
            selected_address = st.selectbox("Select an Address", addresses)

            if selected_address:
                # Find details of the selected address
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

                        # Populate fields with address details
                        st.text_input("House Number", value=house_number)
                        st.text_input("Address Line 1", value=address_line_1)
                        st.text_input("Town", value=town)
                        st.text_input("County", value=county)
                        st.text_input("Postcode", value=postcode)
                        st.text_input("Last Sold Date", value=date)
                        st.text_input("Last Sold Price", value=f"£{price}")

                        # Fetch and display energy rating and valid until date
                        energy_rating, valid_until = fetch_energy_rating(postcode, house_number)
                        st.text_input("Energy Rating", value=energy_rating)
                        st.text_input("Valid Until Date", value=valid_until)
                        break

        else:
            st.info("No addresses found for the given postcode.")
    else:
        st.warning("Please enter a valid postcode.")
