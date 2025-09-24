import streamlit as st
import fastf1 as ff1
import pandas as pd
import plotly.express as px
import datetime


ff1.Cache.enable_cache(r'/home/siddhantp/Desktop/F1_Project/F1_Cache')


st.set_page_config(
    page_title="F1 Performance Dashboard",
    page_icon="🏎️",
    layout="wide"
)


@st.cache_data(ttl="1h") 
def get_race_schedule(year):
    """Gets the F1 race schedule for a given year and returns a list of past race names."""
    try:
        schedule = ff1.get_event_schedule(year, include_testing=False)
        past_races = schedule[schedule['EventDate'] < pd.to_datetime('today')]
        return past_races['EventName'].tolist()
    except Exception as e:
        st.error(f"Could not load race schedule for {year}: {e}")
        return []

@st.cache_data(ttl="1h") 
def load_session_data(year, race_name):
    """Loads the session data for a specific race."""
    try:
        session = ff1.get_session(year, race_name, 'R')
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        return session
    except Exception as e:
        st.error(f"Error loading data for {year} {race_name}: {e}")
        return None


st.title("F1 Performance Dashboard")

st.sidebar.header("Dashboard Filters")

current_year = datetime.datetime.now().year
year_list = list(range(current_year, 2017, -1))
selected_year = st.sidebar.selectbox("Select Season", year_list)


race_list = get_race_schedule(selected_year)
if race_list:
    selected_race = st.sidebar.selectbox("Select Grand Prix", race_list)
else:
    st.sidebar.warning(f"No completed races found for {selected_year}.")
    selected_race = None


if selected_race:
    session = load_session_data(selected_year, selected_race)
    
    if session:
        laps = session.laps
        
        laps['LapNumber'] = laps['LapNumber'].astype(int)

        driver_list = sorted(laps['Driver'].unique())
        
        st.sidebar.header("Driver Analysis")
        selected_drivers = st.sidebar.multiselect(
            "Select Drivers for Lap Time Analysis", 
            driver_list, 
            default=driver_list[:3]
        )
        
        st.sidebar.header("Head-to-Head Comparison")
        driver1 = st.sidebar.selectbox("Select Driver 1", driver_list, index=0)
        driver2 = st.sidebar.selectbox("Select Driver 2", driver_list, index=1)

        tab_results, tab_overview, tab_strategy, tab_h2h = st.tabs([
            " Race Results", 
            " Race Overview", 
            " Strategy Deep Dive", 
            "Head-to-Head"
        ])

        with tab_results:
            st.subheader("Race Classification")

            results = session.results.copy() # Use .copy() to avoid warnings

            # This comment is important, since I needed to redefine the time formatting for a better understanding of the timings of the viewer
            def format_time_or_status(row):
                # For drivers who are lapped or did not finish, their 'Time' is blank (NaT).
                # In this case, This will return their official 'Status'.
                if pd.isna(row['Time']):
                    return row['Status']
                # For finishers, this will format their total race time into H:MM:SS.ms
                else:
                    total_seconds = row['Time'].total_seconds()
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    return f"{int(hours)}:{int(minutes):02d}:{seconds:06.3f}"

            results['Time/Gap'] = results.apply(format_time_or_status, axis=1)

            results_display = results[[
                'Position', 'FullName', 'TeamName', 'Time/Gap', 'Points'
            ]].rename(columns={
                'FullName': 'Driver',
                'TeamName': 'Team'
            })
            
            st.dataframe(results_display, hide_index=True, use_container_width=True)

            st.subheader("Fastest Lap")
            fastest_lap = laps.pick_fastest()            
            lap_time = fastest_lap['LapTime']
            minutes, seconds = divmod(lap_time.total_seconds(), 60)
            lap_time_str = f"{int(minutes):02d}:{seconds:06.3f}"
            
            driver_name = fastest_lap['Driver']
            st.metric(
                label=f"Driver: {driver_name}",
                value=lap_time_str
            )
            st.markdown(f"Set on Lap **{fastest_lap['LapNumber']}**")


            
        with tab_overview:
            st.header("Race Story: Position Changes")
            pos_data = laps[['Driver', 'LapNumber', 'Position']]
            fig_pos = px.line(pos_data, x='LapNumber', y='Position', color='Driver', title="Race Position Changes Lap by Lap")
            fig_pos.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_pos, use_container_width=True)

            st.header("Lap Time Analysis")
            if selected_drivers:
                driver_laps = laps[laps['Driver'].isin(selected_drivers)].copy()
                driver_laps['LapTimeSeconds'] = driver_laps['LapTime'].dt.total_seconds()
                fig_lap_times = px.line(driver_laps, x="LapNumber", y="LapTimeSeconds", color="Driver", hover_name="Compound", title=f"Lap Times for Selected Drivers")
                st.plotly_chart(fig_lap_times, use_container_width=True)
            else:
                st.warning("Please select at least one driver for lap time analysis.")




        with tab_strategy:
            st.header("Strategy Deep Dive: Tyre Stints")

            # --- Data Calculation (No Changes Here) ---
            laps['Stint'] = laps['PitOutTime'].notna().groupby(laps['Driver']).cumsum() + 1
            stints = laps.groupby(['Driver', 'Stint'])[['Compound', 'LapNumber']].agg(
                StintStart=('LapNumber', 'min'),
                StintEnd=('LapNumber', 'max'),
                Compound=('Compound', 'first')
            ).reset_index()

            if not stints.empty:
                stints['StintDuration'] = stints['StintEnd'] - stints['StintStart']

                fig_stints = px.bar(
                    stints,
                    x="StintDuration",
                    y="Driver",
                    base="StintStart",  # This is the key argument
                    color="Compound",
                    orientation='h',  # Horizontal bars
                    title="Tyre Strategy and Stint Length",
                    color_discrete_map={"SOFT": "red", "MEDIUM": "yellow", "HARD": "grey", "INTERMEDIATE": "green", "WET": "blue"}
                )
                fig_stints.update_yaxes(categoryorder='total ascending')
                fig_stints.update_layout(xaxis_title="Lap Number")
                st.plotly_chart(fig_stints, use_container_width=True)
            else:
                st.info("No valid stint data could be calculated to generate the strategy chart for this race.")

            st.header("Pit Stop Analysis")
            pit_stops = laps.loc[laps['PitOutTime'].notna()].copy()
            if not pit_stops.empty:
                st.subheader("Raw Pit Stop Data Inspection")
                st.warning("This table shows the raw calculated data before filtering for valid times.")

                pit_stops_display = pit_stops[['Driver', 'Team', 'LapNumber', 'PitInTime', 'PitOutTime']].copy()
                st.info("This raw data from fastf1 library is kind of weird, in some cases it is Nan, then in almost all cases, the In The Pit time is higher than the Out of the pit time. It just doesn't make sense, hence viewer descretion is advised")

                def format_timedelta_hms(td):
                    if pd.isna(td):
                        return "N/A"
                    total_seconds = td.total_seconds()
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    return f"{int(hours)}:{int(minutes):02d}:{seconds:06.3f}"
                
                pit_stops_display['PitInTime'] = pit_stops_display['PitInTime'].apply(format_timedelta_hms)
                pit_stops_display['PitOutTime'] = pit_stops_display['PitOutTime'].apply(format_timedelta_hms)
                
                st.dataframe(pit_stops_display, hide_index=True, use_container_width=True)
                pit_stops['PitDuration'] = (pit_stops['PitOutTime'] - pit_stops['PitInTime']).dt.total_seconds()
                fig_pit = px.box(pit_stops, x='Team', y='PitDuration', color='Team', title="Pit Stop Duration by Team")
                fig_pit.update_layout(yaxis_title="Pit Duration (seconds)")
                st.plotly_chart(fig_pit, use_container_width=True)

            else:
                st.info("No pit stop data available for this session.")



                
                
        with tab_h2h:
            st.header(f"Head-to-Head: {driver1} vs. {driver2}")
            if driver1 == driver2:
                st.warning("Please select two different drivers for the Head-to-Head comparison.")
            else:

                d1_laps = laps.pick_drivers([driver1]).copy()
                d2_laps = laps.pick_drivers([driver2]).copy()
                d1_laps['LapTimeSeconds'] = d1_laps['LapTime'].dt.total_seconds()
                d2_laps['LapTimeSeconds'] = d2_laps['LapTime'].dt.total_seconds()
                
                merged_laps = pd.merge(d1_laps[['LapNumber', 'LapTimeSeconds']], d2_laps[['LapNumber', 'LapTimeSeconds']], on='LapNumber', suffixes=(f'_{driver1}', f'_{driver2}'))
                merged_laps['Delta'] = merged_laps[f'LapTimeSeconds_{driver1}'] - merged_laps[f'LapTimeSeconds_{driver2}']
                
                fig_delta = px.line(merged_laps, x='LapNumber', y='Delta', title=f"Lap Time Delta ({driver1} vs. {driver2})")
                fig_delta.add_hline(y=0, line_dash="dash", line_color="white")
                fig_delta.update_layout(yaxis_title=f"Time Delta (s) | Negative = {driver1} is faster")
                st.plotly_chart(fig_delta, use_container_width=True)
else:
    st.info("Select a season and a Grand Prix to load the dashboard.")




