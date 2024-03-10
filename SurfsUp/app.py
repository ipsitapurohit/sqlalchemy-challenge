
#################################################
# Database Setup
#################################################


# Import the dependencies.

from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import datetime as dt

# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

# create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session (link) from Python to the DB
session = Session(engine)

# Precipitation Analysis
# Find the most recent date in the dataset
most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
most_recent_date = dt.datetime.strptime(most_recent_date[0], '%Y-%m-%d')

# Calculate the date 1 year ago from the last data point in the database
one_year_ago = most_recent_date - dt.timedelta(days=365)

# Perform a query to retrieve the data and precipitation scores
precipitation_data = session.query(Measurement.date, Measurement.prcp).\
    filter(Measurement.date >= one_year_ago).all()

# Save the query results as a Pandas DataFrame and set the index to the date column
precipitation_df = pd.DataFrame(precipitation_data, columns=['Date', 'Precipitation'])
precipitation_df.set_index('Date', inplace=True)

# Sort the dataframe by date
precipitation_df = precipitation_df.sort_index()

# Plot the results
precipitation_df.plot(rot=45)
plt.xlabel("Date")
plt.ylabel("Inches")
plt.title("Precipitation Analysis")
plt.show()

# Use Pandas to print the summary statistics for the precipitation data
print(precipitation_df.describe())

# Station Analysis
# Design a query to calculate the total number of stations in the dataset
total_stations = session.query(Station.station).count()
print(f"Total number of stations: {total_stations}")

# Design a query to find the most active stations
most_active_stations = session.query(Measurement.station, func.count(Measurement.station)).\
    group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()

most_active_station = most_active_stations[0][0]
print(f"The most active station is {most_active_station} with {most_active_stations[0][1]} observations.")

# Design a query to calculate the lowest, highest, and average temperatures for the most active station
temperature_stats = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
    filter(Measurement.station == most_active_station).all()

print(f"Temperature Stats for Station {most_active_station}:")
print(f"Lowest Temperature: {temperature_stats[0][0]}")
print(f"Highest Temperature: {temperature_stats[0][1]}")
print(f"Average Temperature: {temperature_stats[0][2]}")

# Design a query to get the previous 12 months of temperature observation (TOBS) data for the most active station
tobs_data = session.query(Measurement.date, Measurement.tobs).\
    filter(Measurement.station == most_active_station).\
    filter(Measurement.date >= one_year_ago).all()

# Save the query results as a Pandas DataFrame
tobs_df = pd.DataFrame(tobs_data, columns=['Date', 'Temperature'])

# Plot the results as a histogram
tobs_df.plot.hist(bins=12, alpha=0.7)
plt.xlabel("Temperature")
plt.ylabel("Frequency")
plt.title("Temperature Observation Analysis")
plt.show()

# Close the session
session.close()

from flask import Flask, jsonify
import datetime as dt
from sqlalchemy import func

app = Flask(__name__)

# Define route to the homepage
@app.route("/")
def home():
    return (
        f"Welcome to Climate App!<br/><br/>"
        f"Available Routes:<br/>"
        f"<a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a><br/>"
        f"<a href='/api/v1.0/stations'>/api/v1.0/stations</a><br/>"
        f"<a href='/api/v1.0/tobs'>/api/v1.0/tobs</a><br/>"
        f"<a href='/api/v1.0/start_date'>/api/v1.0/start_date</a><br/>"
        f"<a href='/api/v1.0/start_date/end_date'>/api/v1.0/start_date/end_date</a>"
    )

# Define route to precipitation data
@app.route("/api/v1.0/precipitation")
def get_precipitation():
    # Calculate the date 1 year ago from the last data point in the database
    one_year_ago = dt.date.today() - dt.timedelta(days=365)
    # Query the last 12 months of precipitation data
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()
    # Convert the query results to a dictionary
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    return jsonify(precipitation_dict)

# Define route to list of stations
@app.route("/api/v1.0/stations")
def get_stations():
    # Query all stations
    stations = session.query(Station.station).all()
    # Convert the query results to a list
    station_list = [station[0] for station in stations]
    return jsonify(station_list)

# Define route to temperature observations for the most active station
@app.route("/api/v1.0/tobs")
def get_tobs():
    # Calculate the date 1 year ago from the last data point in the database
    one_year_ago = dt.date.today() - dt.timedelta(days=365)
    # Query the dates and temperature observations of the most active station for the previous year of data
    tobs_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= one_year_ago).all()
    return jsonify(tobs_data)

# Define route to temperature statistics for specified start or start-end range
@app.route("/api/v1.0/<start_date>")
@app.route("/api/v1.0/<start_date>/<end_date>")
def get_temp_stats(start_date, end_date=None):
    # Define function to calculate temperature statistics
    def calc_temps(start, end):
        if not end:
            return session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                filter(Measurement.date >= start).all()
        else:
            return session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                filter(Measurement.date >= start).filter(Measurement.date <= end).all()

    # Call calc_temps function
    temperature_stats = calc_temps(start_date, end_date)
    # Convert the query results to a dictionary
    temp_stats_dict = {'TMIN': temperature_stats[0][0], 'TAVG': temperature_stats[0][1], 'TMAX': temperature_stats[0][2]}
    return jsonify(temp_stats_dict)

if __name__ == '__main__':
    app.run(debug=True)
