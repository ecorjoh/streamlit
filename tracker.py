import streamlit as st
import pandas as pd
import pdb
from pyxlsb import open_workbook
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

df = pd.DataFrame()   
# df = pd.read_csv(r'C:\Users\ecorjoh\OneDrive - Ericsson\Projects\Smart CD\data\smartCD_verizon-2024-08-16.csv')
# with open_workbook(r'C:\Users\ecorjoh\OneDrive - Ericsson\Projects\Anupama_Chandra\Closeout Tracker Copy.xlsb') as wb:
with open_workbook('Closeout Tracker Copy.xlsb') as wb:
  with wb.get_sheet('Main Data') as sheet:
    data = [[cell.v for cell in row] for row in sheet.rows()]
    df = pd.DataFrame(data[4:], columns=data[0])
# df = pd.read_excel('Closeout Tracker Copy.xlsx', sheet_name="Main Data", skiprows=[1,2,3])

df = df.dropna(axis=1,how='all') 
df = df.head(1000)       
# Define column groups
default_groups = [
   "IWM_JOB_NUMBER","PACE","Site Name","Site ID","SiteTracker Project","FA Location Code","Project Type","Bucket List"
]

result = [item for item in list(df.columns) if item not in default_groups]
grouped_list = [result[i:i + 10] for i in range(0, len(result), 10)]
column_groups = {f"Grp {idx}": group for idx, group in enumerate(grouped_list)}

# Streamlit layout
st.set_page_config(page_title="My Streamlit App", layout="wide")

st.title("Tracker")

# Expandable sidebar
with st.sidebar:
    st.header("Settings")
    
    with st.expander("Search"):
        selected_column = st.selectbox("Select Column to search:", list(default_groups))
        search_term = st.text_input(f"Enter search term (applies to '{selected_column}')", value="")
        
    # Use an expander for column group selection
    with st.expander("Group Selection"):
        selected_group = st.multiselect("Select Group of Columns", list(column_groups.keys()), default=list(column_groups.keys()))
        
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
gb.configure_pagination(paginationAutoPageSize=True)  # Enable pagination
gb.configure_columns(default_groups, pinned="left")
gb.configure_side_bar()
gb.configure_grid_options(suppressMovableColumns=True)
# gb.configure_grid_options(enable_pivot=True)  # Enable pivoting

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

# gb.configure_grid_options(headerStyle={"backgroundColor": "#FFA726", "color": "white", "fontWeight": "bold"})
    
# Configure grid options for return and update modes
grid_options = gb.build()

st.markdown("""
    <style>
    .custom-header {
        background-color: #4CAF50 !important;  /* Change the header background color */
        color: black !important;               /* Change the header text color */
        font-size: 16px !important;            /* Increase font size */
        text-align: center !important;         /* Center the header text */
        font-weight: bold !important;          /* Make the header text bold */
    }
    </style>
""", unsafe_allow_html=True)

# Display DataGrid
st.subheader("Data Grid:")
grid_response = AgGrid(
    filtered_df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    enable_enterprise_modules=True,
    height=500,
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
  