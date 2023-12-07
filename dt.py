import streamlit as st
from streamlit_chat import message
import os
from openai import OpenAI
from pathlib import Path
from io import StringIO
import imageio.v2 as iio
from streamlit_extras.app_logo import add_logo
from datetime import date
import pandas as pd


client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv('OPENAI_API_KEY')
)

st.set_page_config(page_title="B2b Sales Copilot", page_icon=":robot:",layout="wide")

img_business = iio.imread("./assets/dt.png")
st.image(image=img_business, width=500)

st.markdown("## B2B Sales Copilot")

img = iio.imread("./assets/dt.png")
st.sidebar.image(image=img, width=200)

st.sidebar.markdown("### Client Information")
profiles = pd.read_csv("./assets/b2b_profiles.csv")
profiles["combined"] = profiles[profiles.columns[0:2]].apply(
    lambda x: " ".join(x.astype(str)), axis=1
)

combined_name_list = profiles.loc[:, ["combined"]].values.flatten().tolist()

profile_selection = st.sidebar.selectbox("Select Account", combined_name_list)

# print(profile_selection)

row_idx = profiles.index[profiles["combined"] == profile_selection]
row = profiles.iloc[row_idx]
# print(row.iloc[0])

sales_person = "William Müller"

operator = "Deutsche Telekom"

industry_list = [
    "Retail",
    "Software",
    "Professional services",
    "Transportation",
    "Healthcare",
    "Education",
    "Financial services",
    "Manufacturing",
    "Government",
    "Telecommunications",
    "Media & Entertainment",
    "Energy & Utilities",
    "Hospitality",
    "Agriculture",
]

product_list = [
    "None",
    "1Gbps Ethernet",
    "10Gbps Ethernet",
    "SD-WAN",
    "SD-WAN and Managed Wi-Fi",
]

sales_play_list = [
    "Acquire new customer", 
    "Upsell",
]

sales_play_list_description = [
    "The goal of the email is to acquire a new customer. The recipient is currently with a competing service provider. The email should not imply that there is any existing relationship with the recipient. It can be assumed that the customer has heard of {operator}.",
    "The goal of the email is to upsell any existing customer to the identified product. The email should provide a short articulation of the benefits of the upgrade in a way that is relevant to the customer's indsutry. The email should be written with the udnerstanding that the recipient is an existing customer of {operator}.",
]

langauge_list = ["English", "German"]

previous_relationship_list = [
                "None",
                "Mutual friend",
                "Previous customer",
]


with st.sidebar.expander("Account Information", expanded=False):
    first_name = st.text_input("Profile First name", row.iloc[0]["First Name"])
    last_name = st.text_input("Profile Last name", row.iloc[0]["Last Name"])
    position = st.text_input("Profile position", row.iloc[0]["Position"])
    address = st.text_input("Address", row.iloc[0]["Address"])
    city = st.text_input("City", row.iloc[0]["City"])
    State = st.text_input("State", row.iloc[0]["State"])
    zipcode = st.text_input("Zipcode", row.iloc[0]["Zipcode"])

with st.sidebar.expander("Business Information"):
    company = st.text_input("Company", row.iloc[0]["Company"])
    company_size = st.text_input("Company Size", row.iloc[0]["Company size"])
    
    industry = st.selectbox(
        "Industry", industry_list, industry_list.index(row.iloc[0]["Industry"])
    )

    current_monthly_spend = st.text_input(
        "Current monthly spend", row.iloc[0]["Current monthly spend"]
    )

additional_comments = st.sidebar.text_input("Additional Comments ")

col1, col2 = st.columns(2)


with col1:
    st.markdown("### Sales Information")

    sales_play = st.selectbox(
        "Sales play",
        options=sales_play_list,
        index=0,
    )

    current_product = st.selectbox(
        "Current products",
        options=product_list,
        index=0,
    )

    language = st.selectbox(
        "Language",
        options=langauge_list,
        index=0,
    )

    previous_relationship = st.selectbox(
        "Previous Relationship",
        options=previous_relationship_list,
        index=0,
    )

    likely_product_needs = st.multiselect(
        "Likely Product Needs", 
        product_list, 
        product_list[2]
    )

with col2:
    st.markdown("### Model Parameter")
    email_length = st.slider(
        label="Maximum Email Length", min_value=128, max_value=1024, step=1, value=512
    )
    temperature = st.slider(
        label="Model temperature", min_value=0.0, max_value=1.0, step=0.01, value=0.5
    )
    tone = st.multiselect(
        "Tone",
        ["Professional", "Engaging", "Persuasive", "Inspirational", "Informal"],
        ["Professional", "Engaging"],
    )
    n = st.number_input(label="Number of candidate emails to generate", min_value=1)

# convert lists to string for prompting
product_need_str = ", ".join(likely_product_needs)
tone_str = ", ".join(tone)

openAI_prompt = f"""    
    Write an email from {sales_person} working for {operator} for the purpose of {sales_play} with the following information:
    Recipient name: {first_name} {last_name}
    Recipient company: {company}
    Likely product needs: {product_need_str}
    Previous relationship with the client: {previous_relationship}. 
    The tone of the email should be {tone_str}.
    Do not mention Sales play in the email.     
    THe email should be written in {language}.
    {sales_play_list_description[sales_play_list.index(sales_play)]}.
    """

if st.button("Generate content"):

    responses = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=openAI_prompt,
        temperature=temperature,
        max_tokens=email_length,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["Q:"],
        n=n,
        timeout=20,
    )

    num_lis = list(range(1, n + 1))
    str_lis = list(map(str, num_lis))
    str_lis = [f"Candidate Email {num}" for num in str_lis]
    tabs = st.tabs(str_lis)
    # print(tabs)
    for i in range(0, n):
        response_text = responses.choices[i - 1].text
        response_text = response_text.replace("$", "\$")
        tabs[i - 1].write(response_text)

    st.session_state.current_response = response_text


comments = st.text_input("Comments", help="i.e. make it longer")
st.session_state.comments = comments

# if response_text: # create iterative button after content is generated
if st.button("Iterate Content"):
    st.session_state.iter_prompt = f'Rewrite the email with these adjustments: {st.session_state.comments}:\nEmail: """{st.session_state.current_response}"""'
    print(f"session state {st.session_state.current_response}")
    # iter_prompt = f'Rewrite the email with these additional comments {iter_comments}: {response_text}'
    # print(iter_prompt)
    iter_responses = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=st.session_state.iter_prompt,
        temperature=temperature,
        max_tokens=email_length,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        n=n,
        timeout=20,
    )

    num_lis = list(range(1, n + 1))
    str_lis = list(map(str, num_lis))
    str_lis = [f"Candidate Email {num}" for num in str_lis]
    tabs = st.tabs(str_lis)
    # print(tabs)

    iter_response_text = iter_responses.choices[0].text
    with st.expander("Original Content"):
        st.write(st.session_state.current_response)
    st.markdown("### Edited Content")
    st.write(iter_response_text)