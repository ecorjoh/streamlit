import streamlit as st
import pandas as pd
import pdb
from pyxlsb import open_workbook
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

df = pd.DataFrame()
filters_dict = {}
# Streamlit layout
st.set_page_config(page_title="My Streamlit App", layout="wide")

@st.cache_data
def load_data():
    filtered_groups = {
        "All": ["Grp 0","Grp 1","Grp 2","Grp 3","Grp 4","Grp 5","Grp 6","Grp 7","Grp 8","Grp 9","Grp 10","Grp 11","Grp 12","Grp 13","Grp 14","Grp 15"],
        "DropDown": ["Grp 0","Grp 1","Grp 2","Grp 3"],
        "Filter 1": ["Grp 4","Grp 5","Grp 6"],
        "Filter 2": ["Grp 7","Grp 8","Grp 9"],
        "Filter 3": ["Grp 10","Grp 11","Grp 12"],
        "Filter 4": ["Grp 13","Grp 14","Grp 15"]
    }
    
    df = pd.DataFrame()   
    # with open_workbook(r'C:\Users\ecorjoh\OneDrive - Ericsson\Projects\Anupama_Chandra\Closeout Tracker Copy.xlsb') as wb:
    with open_workbook('Closeout Tracker Copy.xlsb') as wb:
        with wb.get_sheet('Main Data') as sheet:
            data = [[cell.v for cell in row] for row in sheet.rows()]
            df = pd.DataFrame(data[4:], columns=data[0])
    # df = pd.read_excel('Closeout Tracker Copy.xlsx', sheet_name="Main Data", skiprows=[1,2,3])

    df = df.dropna(axis=1,how='all') 
    # df = df.head(1000)
    
    return df, filtered_groups
    
# Load Data
df, filters_dict = load_data() 
      
# Define column groups
default_groups = [
   "IWM_JOB_NUMBER","PACE","Site Name","Site ID","SiteTracker Project","FA Location Code","Project Type","Bucket List"
]

result = [item for item in list(df.columns) if item not in default_groups]
grouped_list = [result[i:i + 10] for i in range(0, len(result), 10)]
column_groups = {f"Grp {idx}": group for idx, group in enumerate(grouped_list)}

if "all_data" not in st.session_state:
    st.session_state['all_data'] = filters_dict
if "filtered_groups" not in st.session_state:
    st.session_state['filtered_groups'] = list(filters_dict.keys())
if "text_input" not in st.session_state:
    st.session_state['text_input'] = ''
if "selected_group" not in st.session_state:
    st.session_state['selected_group'] = list(filters_dict['All'])
if "selected_filter" not in st.session_state:
    st.session_state['selected_filter'] = 'All'

def update_filters():
    new_filter_name = st.session_state['text_input']
    new_filter_group = st.session_state['selected_group']
    if new_filter_name and new_filter_group:
        filters_dict[new_filter_name] = new_filter_group
    
    # print(filters_dict)
    st.session_state['all_data'] = filters_dict
    st.session_state['selected_filter'] = new_filter_name
    st.session_state['selected_group'] = new_filter_group
    st.session_state['text_input'] = ''    
    st.session_state['filtered_groups'] = list(filters_dict.keys())

def update_selected_group():
    new_grp = st.session_state['filtered_groups']
    new_filter = st.session_state['selected_filter']
    all_data = st.session_state['all_data']
    st.session_state['selected_group'] =  all_data[new_filter]
        
st.title("Southern California Market")

# Expandable sidebar
with st.sidebar:  
    st.header("Settings")
    
    with st.expander("Load Market Data"):
        mkt_selected = st.selectbox("Select Market", ["SoCal"])
        if st.button("Load"):
            pass
    with st.expander("Search"):
        selected_column = st.selectbox("Select Column to search:", default_groups)
        search_term = st.text_input(f"Enter search term (applies to '{selected_column}')", value="")
    
    with st.expander("Saved Filters"):
        selected_filter = st.selectbox("Select Filter:", st.session_state['filtered_groups'], key='selected_filter', on_change=update_selected_group)
        # filter_grp = filters_dict[selected_filter]
             
    # Use an expander for column group selection
    with st.expander("Filter Selection"):
        # selected_group = st.multiselect("Select Group of Columns", list(filters['All']), default=filters[selected_filter])
        selected_group = st.multiselect("Select Group of Columns", list(filters_dict['All']), key='selected_group')
        st.markdown("--------")
        filter_name = st.text_input('Filter Name', key="text_input")
        save_btn = st.button("Save Filter", disabled=(not filter_name), on_click=update_filters)
        if save_btn:
            st.success(f"Filter {filter_name} saved successfully!")
            
print(f"Session State: {st.session_state}")     
                  
# Dropdown for selecting column groups
common_group = default_groups.copy()

if len(selected_group) > 0:
    for grp in selected_group:
        common_group.extend(column_groups[grp])
  
filtered_df = df[common_group]
filtered_df.fillna("N/A", inplace=True)
if search_term:
    filtered_df = filtered_df[
        filtered_df[selected_column].str.contains(search_term, case=False)
    ]
 
# Set up AgGrid options (with filtering, pivoting, and editing enabled)
gb = GridOptionsBuilder.from_dataframe(filtered_df)
gb.configure_default_column(editable=True, filter=True, resizable=True, sortable=True, groupable=True)
gb.configure_selection(selection_mode="multiple", use_checkbox=True)
gb.configure_pagination(paginationAutoPageSize=True, paginationPageSize=30)
gb.configure_columns(default_groups, pinned="left")
gb.configure_side_bar()
gb.configure_grid_options(suppressMovableColumns=True, enable_pivot=True)
gb.configure_column(
    'Priority',
    header_name='Priority',
    cellStyle={"backgroundColor": "#c2574f", "color": "white"},
    editable=True,
    cellEditor='agSelectCellEditor',
    cellEditorParams={'values': ['','0. CI020 ACT; Need CI050', '2. CI050 ACT; Pending CI032 / FTU Review', '3. CL001 ACT', 
                                 '3. Interim Solution, Pending CI050', '4. Hold/Cancelled', '5. Not E//', 'N/A']},
    suppressKeyboardEvent=True
)

# Initialize session state to keep track of whether columns are hidden or not
if "collapse_state" not in st.session_state:
    st.session_state.collapse_state = False  # Start with columns visible

# Create a button to toggle column visibility (collapse/expand)
if st.button("Collapse/Expand Common Columns"):
    st.session_state.collapse_state = not st.session_state.collapse_state
    
# Conditionally hide columns based on collapse state
if st.session_state.collapse_state:
    gb.configure_columns(default_groups[1:], hide=True)
else:
     gb.configure_columns(default_groups[1:], hide=False)
     
for col in common_group[:8]:
    gb.configure_column(col, cellStyle={"backgroundColor": "#7a7fa1", "color": "white"})
    
# Configure grid options for return and update modes
grid_options = gb.build()

# Display DataGrid
st.subheader("Data Grid:")
grid_response = AgGrid(
    filtered_df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    enable_enterprise_modules=True,
    height=800,
    fit_columns_on_grid_load=False
)

# Capture edited data
updated_data = pd.DataFrame(grid_response['data'])

filtered_df.reset_index(drop=True, inplace=True)
updated_data.reset_index(drop=True, inplace=True)
mask = (filtered_df != updated_data)
updated_rows = updated_data[mask.any(axis=1)].reset_index(drop=True)
            
# st.subheader(f"Rows to update: {len(updated_rows)}")

# Save button
if len(updated_rows) > 0:
  btn = st.button("Save Changes", disabled=False)
else:
  btn = st.button("Save Changes", disabled=True)
  
if btn:
  st.subheader("Updated Rows:")
  st.dataframe(updated_rows)
  # updated_data.to_excel(r'C:\Users\ecorjoh\OneDrive - Ericsson\Projects\Anupama_Chandra\Closeout Tracker Copy.xlsb', index=False)
  st.success("Data saved successfully!")
  