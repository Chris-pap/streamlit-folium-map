import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster, Fullscreen
from streamlit_folium import st_folium
from io import BytesIO
import data_folium



# set the layout to wide
st.set_page_config(
    page_title='Map of Companies',
    layout='wide',
    page_icon='📌',
    initial_sidebar_state='expanded'
)

# we load the data to a session
# and we create a copy so we could filter this and also keep the whole df 
if 'load_df' not in st.session_state:
    st.session_state['load_df'] = data_folium.load_data()
    st.session_state['df'] = st.session_state['load_df']

# create the function to apply the filters value to the dataframe
def apply_filter(activity_selectbox, entity_selectbox, status_selectbox, date_slider, capital_slider):
    """Takes a copy from the original dataframe 
    and then apply the filters to it"""

    filtered_df = st.session_state['load_df'].copy()

    if activity_selectbox != 'ΟΛΕΣ':
        filtered_df = data_folium.kad_filter(filtered_df, activity_selectbox)

    if entity_selectbox != 'ΟΛΕΣ':
        filtered_df = data_folium.type_filter(filtered_df, entity_selectbox)

    if status_selectbox != 'ΟΛΕΣ':
        filtered_df = data_folium.status_filter(filtered_df, status_selectbox)

    if date_slider != (1982, 2024):
        filtered_df = data_folium.date_filter(filtered_df, date_slider)

    if capital_slider != (0, 500000):
        filtered_df = data_folium.capital_filter(filtered_df, capital_slider)

    return filtered_df


def main():
    """The main function of the app"""
    
    # delete the top padding
    st.markdown(
        """<style>
        .block-container {padding: 0}
        </style>""",
        unsafe_allow_html=True
    )

    # create the sidebar
    with st.sidebar:

        # header of title
        header_sidebar = st.header('Επιλογή φίλτρων')

        # filters
        activity_selectbox = st.selectbox(
            label='Δραστηριότητα:',
            options=[
                'ΟΛΕΣ', 'ΚΑΤΑΣΚΕΥΕΣ', 'ΥΓΕΙΑ', 'ΕΚΠΑΙΔΕΥΣΗ', 'ΕΣΤΙΑΣΗ'
            ],
            index=0
        )

        entity_selectbox = st.selectbox(
            label='Νομική Μορφή:',
            options=[
                'ΟΛΕΣ', 'ΑΤΟΜΙΚΗ', 'ΟΕ', 'ΙΚΕ', 'ΑΕ', 'ΕΕ', 'ΕΠΕ'
            ],
            index=0
        )

        status_selectbox = st.selectbox(
            label='Κατάσταση:',
            options=[
                'ΟΛΕΣ', 'ΕΝΕΡΓΗ', 'ΚΛΕΙΣΤΗ'
            ],
            index=0
        )

        subheader_sidebar = st.subheader('Περισσότερα Φίλτρα')

        date_slider = st.slider(
            label='Έτος Ίδρυσης:',
            min_value=1982,
            max_value=2024,
            value=(1982,2024)
        )

        capital_slider = st.slider(
            label='Μετοχικό Κεφάλαιο:',
            value=(0, 500000), # write it as the max
            step=1000
        )

        # create 3 columns so we can center the button
        _, sidecol, _ = st.columns([1,3,1])
        with sidecol:
            # the button to apply the filter to the df
            if st.button(label='Εφαρμογή Φίλτρων', type='primary'):
                # Retrieve filter values from input widgets
                st.session_state['activity_selectbox'] = activity_selectbox
                st.session_state['entity_selectbox'] = entity_selectbox
                st.session_state['status_selectbox'] = status_selectbox
                st.session_state['date_slider'] = date_slider
                st.session_state['capital_slider'] = capital_slider
                # Apply filters to the session dataframe
                st.session_state['df'] = apply_filter(
                        st.session_state['activity_selectbox'],
                        st.session_state['entity_selectbox'],
                        st.session_state['status_selectbox'],
                        st.session_state['date_slider'],
                        st.session_state['capital_slider']
                )


    # create 3 columns to center the widgets
    _, col2, _ = st.columns([1,20,1])
    with col2:

        # Create the title
        st.title('🏢 Εταιρείες των Τρικάλων', anchor=False)

        # create another 3 columns to add the metric and the download btn
        met1, met2, _, met3 = st.columns([1,1,4,1])
        # Metrics
        with met1:
            # Number of the Companies
            st.metric('Αριθμός Εταιρειών', len(st.session_state['df']))
        with met2:
            # The average Capital per Company
            try:
                mean_capital = f"{'{:,}'.format(round(st.session_state['df'].CAPITAL.mean())).replace(',','.')}€"
                # if we only have NaN values we capture the Error
            except ValueError:
                mean_capital = '-'
            st.metric('Μέσο Μετοχικό Κεφάλαιο', mean_capital)
        with met3:
            #edit the csv columns before download
            download_df = st.session_state['df'][['NAME', 'LEGAL TYPE', 'VAT', 'KAD', 'MARKET', 'ADDRESS', 'DATE_STARTED', 'DATE_CLOSED', 'STATUS', 'CAPITAL']]
            # convert timestamp column to date
            download_df['DATE_STARTED'] = pd.to_datetime(download_df['DATE_STARTED']).dt.date
            download_df['DATE_CLOSED'] = pd.to_datetime(download_df['DATE_CLOSED']).dt.date
            # convert pandas dataframe to Bytes for download
            output_data = BytesIO()
            download_df.to_excel(output_data, index=False)
            output_data.seek(0)
            # create the download button
            st.download_button(
                'Λήψη Λίστας',
                data=output_data,
                file_name='data_download.xlsx',
                mime="application/vnd.ms-excel"
            )

        # load and create the map
        map = data_folium.create_map()
        # load and add the markers
        data_folium.create_markers(st.session_state['df'], map)


if __name__ == '__main__':
    main()
