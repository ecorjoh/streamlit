import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import textwrap


COLUMNS = ["Opportunity Name", "Size* ($M)", "OPEX", "Expected Close Date", "Current Win Probability (%)", "Percent Used"]
def wrap_text(text, width=15):
    return "<br>".join(textwrap.wrap(str(text), width=width))
  
def main():
    st.set_page_config(layout="wide")
    st.title("Opportunity Win Probability by Quarter (Scatter + Table)")

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file, skiprows=3, engine='openpyxl')
        
        # 1) Clean / transform the data
        df["Expected Close Date"] = pd.to_datetime(df["Expected Close Date"])
        df["Opportunity Name Wrapped"] = df["Opportunity Name"].apply(lambda x: wrap_text(x, width=15))

        # Convert Size column from strings (with commas) to integers
        df["Size* ($M)"] = (
            df["Size* ($M)"]
            .astype(str)
            .str.replace(",", "")
            .astype(float)
            .astype(int)
        )

        # Extract quarter (1–4) and year
        df["Quarter"] = df["Expected Close Date"].dt.quarter
        df["Year"] = df["Expected Close Date"].dt.year
        df["QuarterStr"] = df.apply(lambda x: f"Q{x['Quarter']} {x['Year']}", axis=1)

        # Numeric x-axis for chronological order
        df["quarter_index"] = (df["Year"] - 2020)*4 + df["Quarter"]

        # Jitter so overlapping points shift horizontally
        df["group_order"] = df.groupby("quarter_index").cumcount()
        offset_step = 0.5
        df["quarter_index_jitter"] = df["quarter_index"] + df["group_order"] * offset_step

        # Build a lookup for quarter labels
        quarter_map_df = (
            df[["quarter_index", "QuarterStr"]]
            .drop_duplicates()
            .sort_values("quarter_index")
        )
        quarter_map = dict(zip(quarter_map_df["quarter_index"], quarter_map_df["QuarterStr"]))

        df["Percent Used"] = round((df["OPEX"] / df["Size* ($M)"]) * 100, 2).astype(float)
        # 2) Create the scatter plot with Plotly Express
        scatter_fig = px.scatter(
            df,
            x="quarter_index_jitter",
            y="Current Win Probability (%)",
            text="Opportunity Name Wrapped",
            size="Size* ($M)",
            size_max=50,
            range_y=[0, 100],
            hover_data={
                "quarter_index_jitter": False,
                "QuarterStr": False,
                "Opportunity Name": False,
                "Opportunity Name Wrapped": False,
                "Size* ($M)": True,
                "OPEX": True,
                "Percent Used": True,
                # "Expected Close Date"
            },
            color="Percent Used",
            # color_continuous_scale=px.colors.sequential.Magma,
            # range_color=[0, 100],
            template=None,
            title="Opportunity Win Probability by Expected Close Quarter"
        )

        # 3) Make subplots with 1 row and 2 columns
        #    - col 1: scatter (xy)
        #    - col 2: table   (domain)
        fig = make_subplots(
            rows=1, cols=2,
            specs=[
                [{"type": "xy"}, {"type": "domain"}]
            ],
            horizontal_spacing=0.08,  # space between the two columns
            column_widths=[0.6, 0.4], # adjust widths: 60% for scatter, 40% for table
            subplot_titles=("Opportunity Scatter", "Data Table")
        )

        # Add scatter traces from scatter_fig to (row=1, col=1)
        for trace in scatter_fig.data:
            fig.add_trace(trace, row=1, col=1)

        # 4) Create a Table trace
        table_trace = go.Table(
            header=dict(
                values=list(df[COLUMNS]),
                fill_color="blue",
                align="left"
            ),
            cells=dict(
                values=[df[col].tolist() for col in df[COLUMNS]],
                align="left"
            )
        )
        # Add the table trace to (row=1, col=2)
        fig.add_trace(table_trace, row=1, col=2)
        fig.update_traces(
            textfont_size=14,
            selector=(dict(type="scatter"))
        )
        # 5) Customize the scatter axis in (row=1, col=1)
        fig.update_xaxes(
            tickmode="array",
            tickvals=list(quarter_map.keys()),
            ticktext=list(quarter_map.values()),
            title_text="Expected Close Quarter",
            row=1, col=1
        )
        fig.update_yaxes(
            title_text="Win Probability (%)",
            row=1, col=1
        )

        # 6) Final layout
        fig.update_layout(
            width=1500,
            height=800,
            coloraxis_colorscale=px.colors.sequential.Reds,
            coloraxis_colorbar=dict(
                title="OPEX as % of Size",
                x=0.56,
                y=0.5,
                len=1,
                thickness=15,
            ),
            title="Opportunity Win Probability (Scatter + Table)",
            showlegend=False
        )

        # Position text labels above scatter markers
        fig.update_traces(textposition="top center", row=1, col=1)

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.write("Please upload an Excel file to visualize the data.")

if __name__ == "__main__":
    main()
