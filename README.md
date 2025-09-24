# 🏎️ F1 Race Strategy & Performance Analytics Dashboard

An interactive web application built with Streamlit to analyze and visualize Formula 1 race data. This dashboard provides a comprehensive overview of race results, driver performance, and team strategies for any Grand Prix from recent seasons.

🚀 Live Demo[
Access the Dashboard Here!](https://f1-performance-analytics.streamlit.app/)

📸 Screenshots
(Add screenshots of dashboard's different tabs here)

## ✨ Features

🏆 Race Results: View the final race classification, points distribution for each driver, and the fastest lap of the race with the driver's name and time.

### 📊 Race Overview:

Position Changes: A dynamic "worm chart" tracking the lap-by-lap position changes for every driver.

Lap Time Analysis: Compare lap times for a custom selection of drivers on an interactive line chart.

### ⚙️ Strategy Deep Dive:

Tyre Strategy: A Gantt chart visualizing the tyre compound and stint length for every driver.

Pit Stop Analysis: A box plot comparing the distribution of pit stop durations for all teams.

### ⚔️ Head-to-Head:

Directly compare the race pace of any two drivers.

View a lap-by-lap time delta chart to see who was faster at different stages of the race.

📅 Dynamic Filters: Use the sidebar to select any season and any completed race from the past several years.

## 🛠️ Tech Stack
Language: Python

Framework: Streamlit

Libraries:

fastf1 for F1 data access

pandas for data manipulation

plotly for interactive visualizations

