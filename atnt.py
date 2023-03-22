import streamlit as st
from streamlit_chat import message
import os
import openai
from pathlib import Path
from io import StringIO
import imageio as iio
from streamlit_extras.app_logo import add_logo
from datetime import date
import pandas as pd

openai.api_key = os.getenv('OPENAI_API_KEY')


st.set_page_config(
    page_title="AT&T sales lead script generator",
    page_icon=":robot:"
)

st.markdown("# AT&T Sales Lead Script Generator")


img = iio.imread('./assets/AT&T_logo_2016.svg.png')
st.sidebar.image(image=img, width=200)
st.sidebar.markdown("### Client Information")
profiles = pd.read_csv('./assets/b2b_profiles.csv')
profiles['combined'] = profiles[profiles.columns[0:2]].apply(
    lambda x: ' '.join(x.astype(str)),
    axis=1)

combined_name_list = profiles.loc[:, ['combined']].values.flatten().tolist()

profile_selection = st.sidebar.selectbox('Select Account', combined_name_list)

#print(profile_selection)

row_idx = profiles.index[profiles['combined'] == profile_selection]
row = profiles.iloc[row_idx]
#print(row.iloc[0])

industry_list = ['Retail','Software','Professional services', 'Transportation','Healthcare','Education','Financial services', 'Manufacturing','Government','Telecommunications',
'Media & Entertainment', 'Energy & Utilities', 'Hospitality','Agriculture']
product_list = ['Unlimited Starter','Unlimited Performance','Unlimited Elite','Wireless Data 50 GB/month','Wireless Data 100 GB/month','Broadband Core','Broadband Pro','Broadband Ultra','Fiber 300 Mbps','Fiber 500 Mbps','Fiber 1 Gbps','Fiber 2 Gbps','Fiber 5 Gbps','Phone','None']
promotion_list = ['25% wireless discount','$250 wireline reward','$750 wireline reward','Phone bundle','$50 reward card','Retention promotion']


with st.sidebar.expander("Account Information",expanded=False):
    first_name = st.text_input('Profile First name', row.iloc[0]['First Name'])
    last_name = st.text_input('Profile Last name', row.iloc[0]['Last Name'])
    position = st.text_input('Profile position', row.iloc[0]['Position'])
    address = st.text_input('Address', row.iloc[0]['Address'])
    city = st.text_input('City', row.iloc[0]['City'])
    State = st.text_input('State', row.iloc[0]['State'])
    zipcode = st.text_input('Zipcode', row.iloc[0]['Zipcode'])

with st.sidebar.expander("Business Information"):
    company = st.text_input('Company' , row.iloc[0]['Company'])
    company_size = st.text_input('Company Size', row.iloc[0]['Company size'])
#spend = st.sidebar.text_input('Spend Last Month', row.iloc[0]['Spend last month'])
    industry = st.selectbox('Industry', industry_list, industry_list.index(row.iloc[0]['Industry']))
    current_monthly_spend = st.text_input('Current monthly spend', row.iloc[0]['Current monthly spend'])
additional_comments = st.sidebar.text_input('Additional Comments ')
# add_logo("./assets/AT&T_logo_2016.svg.png")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Sales Information")
    current_product = st.multiselect('Current products', product_list, row.iloc[0]['Current products'])
    sales_play = st.selectbox('Sales Play', (['Account Acquisition','Upsell', 'Cross-sell', 'Retain']))
    likely_product_needs = st.multiselect(
    'Likely Product Needs',
    product_list, row.iloc[0]['Product needs'])
    promotions = st.multiselect("Applicable Promotions",promotion_list)
    
with col2:
    st.markdown("### Model Parameter")
    email_length = st.slider(label='Email Length',min_value=128, max_value=1024, step=1, value=256)
    temperature = st.slider(label='Model temperature',min_value=0.0, max_value=1.0, step=0.01, value=0.5)
    tone = st.multiselect('Tone',['Professional','Engaging','Humours','Persuasive','Inspirational','Informal'], ['Professional','Engaging'])
    n = st.number_input(label='Number of candidate emails to generate',min_value=1)

# convert lists to string for prompting
product_need_str = ", ".join(likely_product_needs)
promotions_str = ", ".join(promotions)
tone_str = ", ".join(tone)


openAI_prompt = f'Write a AT&T sales lead email with the following information: Salesperson name: Maria Hernandez Client name: {first_name} {last_name}, Client Company: {company}, Sales play: {sales_play}, Likely product needs: {product_need_str}, Applicable promotion: {promotions_str}. The tone of the email should be {tone_str}'

# print(openAI_prompt)

# container = st.container()

if st.button('Generate content'):
    responses = openai.Completion.create(
        model="text-davinci-003",
        prompt=openAI_prompt,
        temperature=temperature,
        max_tokens=email_length,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["Q:"],
        n=n,
        timeout=20)
    #print((list(range(0,1)))
    num_lis = list(range(1,n+1))
    str_lis = list(map(str, num_lis))
    str_lis = [ f'Candidate Email {num}' for num in str_lis]
    tabs = st.tabs(str_lis)
    #print(tabs)
    for i in range(0,n):
        response_text = responses["choices"][i-1]["text"]
        response_text = response_text.replace('$', '\$')
        tabs[i-1].write(response_text)
        
        

        
    st.session_state.current_response = response_text
    #if 'iter_comments' not in st.session_state: # store variable in session state so that it persists
    
    #print(f'comments: {st.session_state.iter_comments}')

comments = st.text_input('Comments','Add a joke',help='i.e. make it longer')
st.session_state.comments = comments
        #if response_text: # create iterative button after content is generated       
if st.button('Iterate Content'):
    st.session_state.iter_prompt = f'Rewrite the email with these adjustments: {st.session_state.comments}: Email: """{st.session_state.current_response}"""'
    print(f'session state {st.session_state}')
    #iter_prompt = f'Rewrite the email with these additional comments {iter_comments}: {response_text}'
    #print(iter_prompt)
    iter_responses = openai.Completion.create(
        model="text-davinci-003",
        prompt= st.session_state.iter_prompt,
        temperature=temperature,
        max_tokens=email_length,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        n=n,
        timeout=20)
    
    num_lis = list(range(1,n+1))
    str_lis = list(map(str, num_lis))
    str_lis = [ f'Candidate Email {num}' for num in str_lis]
    tabs = st.tabs(str_lis)
    #print(tabs)

    
    iter_response_text = iter_responses["choices"][0]["text"]
    with st.expander("Original Content"):
        st.write(st.session_state.current_response)
    st.markdown("### Edited Content")
    st.write(iter_response_text)