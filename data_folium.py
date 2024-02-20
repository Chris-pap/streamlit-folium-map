import pandas as pd
import numpy as np
import streamlit as st
import folium
import openpyxl
from folium.plugins import MarkerCluster, Fullscreen
from streamlit_folium import st_folium




# load and clean data
@st.cache_data
def load_data():

    # load data to df
    df = pd.read_csv(
        filepath_or_buffer='./data.csv',
        delimiter=';',
        dtype={'VAT': str},
        dayfirst=True,
        parse_dates=['DATE_STARTED', 'DATE_CLOSED']
    )

    # rename columns
    df.columns = [
        'NAME', 'LEGAL TYPE', 'VAT', 'KAD', 'MARKET', 'ADDRESS',
        'DATE_STARTED', 'DATE_CLOSED', 'STATUS','CAPITAL', 'LAT_LON', 'LINKS'
    ]

    # remove start and trail spaces from str columns
    str_columns =[
        'NAME', 'LEGAL TYPE', 'VAT', 'KAD', 'MARKET', 
        'ADDRESS', 'STATUS', 'LAT_LON', 'LINKS'
    ]
    for column in df[str_columns]:
        df[column] = df[column].str.strip()

    # create two new columns with the lat & long values
    df = df.assign(
        LATITUDE =
        [i.split(',')[0] for i in df['LAT_LON']],
        LONGITUDE =
        [i.split(',')[1] for i in df['LAT_LON']]
    )

    # return the pandas dataframe
    return df


# function to create the tooltip
@st.cache_data
def create_tooltip(name: str) -> str:
    """Creates the tooltip for folium markers"""

    return f"""<span style="font-size:14px;"><b>{name}</b></span>"""


# function to create the popup
@st.cache_data
def create_popup(
    name: str,
    entity: str,
    vat: str,
    kad: str,
    status: str,
    date_start: str,
    date_close: str,
    capital: float,
    market: str,
    address: str
) -> str:

    """Creates the popup for folium markers"""


    # create the HTML code for every popup value
    html_style = """
    <head>
        <style>
            .container{display:flex; width:100%; padding: 0; margin:0;}
            .half{width:100%; padding: 0; margin:0;}
        </style>
    </head>
    """
    html_name = f"""
    <span style="font-size:20px;color:#148CDA;"><b>{name}</b></span>
    <hr style="border:1px solid grey;">
    """
    html_entity = f"""
    <div class="container">
    <div class="half">
        <span style="font-size:14px;color:#148CDA;"><b>Εταιρικός Τύπος:</b></span>
        <span style="font-size:14px"><b>{entity}</b></span>
    </div>
    """
    html_vat = f"""
    <div class="half">
        <span style="font-size:14px;color:#148CDA;"><b>Α.Φ.Μ.:</b></span>
        <span style="font-size:14px;"><b>{vat}</b></span><br><br>
    </div>
    </div>
    """
    html_kad = f"""
    <div class="container">
    <div class="half">
        <span style="font-size:14px;color:#148CDA;"><b>ΚΑΔ:</b></span>
        <span style="font-size:14px;"><b>{kad}</b></span>
    </div>
    """
    html_status = f"""
    <div class="half">
        <span style="font-size:14px;color:#148CDA;"><b>Κατάσταση:</b></span>
        <span style="font-size:14px;"><b>{status}</b></span><br><br>
    </div></div>
    """
    html_date_start = f"""
    <div class="container">
    <div class="half">
        <span style="font-size:14px;color:#148CDA;"><b>Ημ/νία Ίδρυσης:</b>
        </span>
        <span style="font-size:14px;"><b>{date_start.strftime('%d/%m/%Y')}</b>
        </span>
    </div>
    """

    # if date_close is NOT NAN we add it to the popup
    if not pd.isna(date_close):
        html_date_close = f"""
        <div class="half">
            <span style="font-size:14px;color:#148CDA;"><b>Ημ/νία Κλεισίματος:</b></span>
            <span style="font-size:14px;"><b>{date_close.strftime('%d/%m/%Y')}
            </b></span><br><br>
        </div>
        </div>
        """
    else:
        html_date_close = '<br><br></div>'

    # if capital is NOT NAN we round it and add it to the popup
    if not pd.isna(capital):
        capital = f'{round(capital):,}'.replace(',','.') + '€'
        html_capital = f"""
        <div class="container">
        <div class="half">
            <span style="font-size:14px;color:#148CDA;"><b>Μετοχικό Κεφάλαιο:</b></span>
            <span style="font-size:14px;"><b>{capital}</b></span><br><br>
        </div>
        </div>
        """
    else:
        html_capital = ''

    html_market = f"""
    <div class="container">
    <div class="half">
        <span style="font-size:14px;color:#148CDA;"><b>Δραστηριότητα:</b></span>
        <span style="font-size:14px;"><b>{market}</b></span><br><br>
    </div></div>
    """
    html_address = f"""
    <div class="container">
    <div class="half">
        <span style="font-size:14px;color:#148CDA;"><b>Διεύθυνση:</b></span>
        <span style="font-size:14px;"><b>{address}</b></span><br><br>
    </div></div>
    """

    return html_style+html_name+html_entity+html_vat+html_kad+html_status+html_date_start+html_date_close+html_capital+html_market+html_address


# icons based on the KAD number an the status of the company
@st.cache_data
def icon_params(kad: str, status: str) -> list[str,str]:
    """
    Takes as an import a KAD number and the status of the company
    and exports the color and the icon for the folium markers
    """
    _kad = [41,86,85,56]
    _status = ['Ενεργή', 'Κλειστή']

    n = float(kad.split('.')[0])
    s = status

    conditions = [(n,s)==(i,j) for i in _kad for j in _status] 
    choices = [
        ('green','building'),
        ('gray','building'),
        ('red','ambulance'),
        ('gray','ambulance'),
        ('blue', 'book'),
        ('gray', 'book'),
        ('orange','coffee'),
        ('gray','coffee')
    ]
    return [str(param) for param in np.select(conditions, choices)]


# Filters
# market - kad
def kad_filter(df: pd.DataFrame, kad2: str) -> pd.DataFrame:
    """It accepts the first 2 numbers
    of a KAD number as a string, or the name of the market
    eg 'ΚΑΤΑΣΚΕΥΕΣ' and returns the
    appropriate dataframe with only those KADs
    df.KAD[0].split('.')[0]"""
    cond = ['ΚΑΤΑΣΚΕΥΕΣ', 'ΥΓΕΙΑ', 'ΕΚΠΑΙΔΕΥΣΗ', 'ΕΣΤΙΑΣΗ']
    conditions = [kad2==i for i in cond]
    choices = ['41', '86', '85', '56']
    _kad = np.select(conditions, choices, kad2).item()

    return df[df.KAD.str.startswith(_kad)]

# legal entity
def type_filter(df: pd.DataFrame, _type: str) -> pd.DataFrame:
    """It accepts the legal type of the company
    and returns the dataframe with only those types"""
    return df[df['LEGAL TYPE'] == _type]

# status
def status_filter(df: pd.DataFrame, status: str) -> pd.DataFrame:
    """It accepts the status of the company (Open or Close)
    and returns the dataframe with only the selected status"""
    if status == 'ΕΝΕΡΓΗ':
        status = 'Ενεργή'
    else:
        status = 'Κλειστή'
    return df[df['STATUS'] == status]

# date started
def date_filter(df: pd.DataFrame, dates: tuple[int,int]) -> pd.DataFrame:
    """It accepts the starting and the ending year of the
    company creation and returns the companies within those years
    in a dataframe"""
    start_year = dates[0]
    end_year = dates[1]
    return df[df['DATE_STARTED'].dt.year.between(start_year, end_year)]

# capital
def capital_filter(
    df: pd.DataFrame,
    capital_limits: tuple[float,float]
    ) -> pd.DataFrame:
    """It accepts the lower and upper limit of company capital and
    returns the companies inside that limit"""
    low_capital = capital_limits[0]
    up_capital = capital_limits[1]
    # if the low capital is 0 we want to keep the companies with no capital
    if low_capital == 0:
        nan_values = df[df['CAPITAL'].isna()]
        return pd.concat([
            nan_values,
            df[df['CAPITAL'].between(low_capital, up_capital)]
        ])
    else:
        return df[df['CAPITAL'].between(low_capital, up_capital)]


# create the map
def create_map():
    """Creates the base map and adds a fullscreen button"""
    # create the base map
    m = folium.Map(
        location=[39.558, 21.765],
        zoom_start=12,
        min_zoom=8,
        zoom_control=False)

    # add fullscreen btn
    fscreen = Fullscreen(
        position='topleft',
        force_separate_button=True).add_to(m)

    return m


# create the markers
def create_markers(df, _m):
    """Create the markers and add them to the map"""

    # add the layer for the markers
    fg = folium.FeatureGroup(name='Markers')

    # create a cluster for markers
    marker_cluster = MarkerCluster(
        spiderfyOnMaxZoom=False,
        disable_clustering_at_zoom=15
        ).add_to(fg)

    # add the markers
    for i in range(len(df)):

        # export the values for every marker
        name = df['NAME'].iloc[i]
        entity = df['LEGAL TYPE'].iloc[i]
        vat = df['VAT'].iloc[i]
        address = df['ADDRESS'].iloc[i]
        kad = df['KAD'].iloc[i]
        status = df['STATUS'].iloc[i]
        market = df['MARKET'].iloc[i]
        date_start = df['DATE_STARTED'].iloc[i]
        date_close = df['DATE_CLOSED'].iloc[i]
        capital = df['CAPITAL'].iloc[i]

        coordinates = df['LATITUDE'].iloc[i], df['LONGITUDE'].iloc[i]

        # create the tooltip and the popup for the marker
        tooltipt = create_tooltip(name)
        popupt = create_popup(name,entity,vat,kad,status,date_start,date_close,capital,market,address)

        # create the icon
        icon_p = icon_params(kad=kad, status=status)
        icon_color = icon_p[0]
        icon_shape = icon_p[1]
        icon = folium.Icon(prefix='fa', color=icon_color, icon=icon_shape)

        # create the marker
        marker = folium.Marker(
            location=coordinates,
            tooltip=folium.Tooltip(text=tooltipt),
            popup=folium.Popup(popupt, max_width=550, min_width=450),
            icon=icon
            ).add_to(marker_cluster)

    # add all the markers to the map
    map_data = st_folium(
        fig=_m,
        width=1200,
        use_container_width=True,
        feature_group_to_add=fg,
        center=[39.558, 21.765],
        zoom=12,
        key='map_data'
        )

    return map_data
