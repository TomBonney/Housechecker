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


def display_crime_image(postcode):
    base_url = f"https://www.crime-statistics.co.uk/postcode/{postcode.replace(' ', '')}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        image_div = soup.find('div', class_='ttm_single_image-wrapper text-sm-center pb-25')
        if image_div:
            image_element = image_div.find('img')
            if image_element:
                image_url = image_element['src']
                full_image_url = urljoin(base_url, image_url)

                image_response = requests.get(full_image_url)
                image_response.raise_for_status()

                image_data = io.BytesIO(image_response.content)
                img = Image.open(image_data)
                st.image(img, caption='Crime Statistics Map')
            else:
                st.info("No map image found.")
        else:
            st.info("No div found with the specified class.")
    except Exception as e:
        st.error(f"Failed to load crime image: {e}")


# Streamlit User Interface
st.title("Address Finder")

postcode = st.text_input("Enter Postcode:", "")

if st.button("Find Address"):
    if postcode:
        formatted_postcode = format_postcode(postcode)
        addresses_data = scrape_addresses(formatted_postcode)

        if addresses_data:
            st.write("Addresses Found:")
            for address, date, price in addresses_data:
                st.write(f"{address} - Last Sold: {date} - Price: £{price}")

            # Display crime statistics image
            display_crime_image(formatted_postcode)
        else:
            st.info("No addresses found for the given postcode.")
    else:
        st.warning("Please enter a valid postcode.")
