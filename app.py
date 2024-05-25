import pandas as pd
import json
import urllib
import sys

import ipyleaflet as ipyl
import ipywidgets as widgets

from shiny import *
from shinywidgets import *
from datetime import datetime


def getMBTA(route):

    # MBTA JSON file
    # https://shinylive.io/py/examples/#fetch-data-from-a-web-api
    url = "https://mbta-flask-513a6449725e.herokuapp.com/proxy"
    if "pyodide" in sys.modules:
        import pyodide.http
        with pyodide.http.open_url(url) as f:
            jdat = json.loads(f.getvalue())
    else:
        response = urllib.request.urlopen(url)
        jdat = json.loads(response.read().decode("utf-8"))

    jdat_header = jdat["header"]
    jdat_entity = jdat["entity"]

    # MBTA DataFrame
    jdf = pd.DataFrame({})
    for i in range(len(jdat_entity)):
        # Vehicle
        car = jdat_entity[i]
        # DataFrame
        cdf = pd.DataFrame(
            {
                "ID": [car.get("id")],
                "Lat": [car.get("vehicle").get("position").get("latitude")],
                "Lon": [car.get("vehicle").get("position").get("longitude")],
                "Route": [car.get("vehicle").get("trip").get("route_id")],
                "Direction": [car.get("vehicle").get("trip").get("direction_id")],
                "Carriage": [
                    (
                        len(car.get("vehicle").get("multi_carriage_details"))
                        if car.get("vehicle").get("multi_carriage_details") != None
                        else "-"
                    )
                ],
                "Trip": [car.get("vehicle").get("trip").get("trip_id")],
                "Stop": [car.get("vehicle").get("stop_id")],
                "Status": [car.get("vehicle").get("current_status")],
            }
        )
        # Combine
        jdf = pd.concat([jdf, cdf], ignore_index=True)

    # Route
    rdf = jdf[jdf["Route"] == route]

    return rdf, jdat_header, jdat_entity

# ------------------- #

# Define UI
app_ui = ui.page_fluid(
    ui.panel_title("MBTA Real-Time"),
    ui.tags.h5("By Jianzhao Bi"),
    ui.input_select(id="route", label=None, choices=[
        'Green-B', 'Green-C', 'Green-D', 'Green-E', 'Red', 'Orange', 'Blue',
        '1', '57', '60', '64', '66', '88', '90'
    ], selected='Green-B'),
    ui.output_text("nowtime"),
    output_widget("routemap"),
)

def server(input, output, session):

    # Register data and map
    mbta_lst = reactive.value()
    route_map = ipyl.Map(
                basemap=ipyl.TileLayer(url='https://tile.thunderforest.com/transport/{z}/{x}/{y}.png?apikey=74002972fcb44035b775167d6c01a6f0'),
                center=(42.3601, -71.0889),  # (lat, lon)
                zoom=12,
                close_popup_on_click=False,
                scroll_wheel_zoom=True,
                touch_zoom=True,
                zoom_snap=0.5, # Forces the map’s zoom level to always be a multiple of this.
                zoom_delta=0.5, # Controls how much the map’s zoom level will change after pressing + or - on the keyboard, or using the zoom controls.
                box_zoom=False, # Whether the map can be zoomed to a rectangular area specified by dragging the mouse while pressing the shift key
            )
    route_map.layout.height = '600px'
    register_widget("routemap", route_map)

    # Update automatically
    @reactive.Effect
    def _():
        mbta_lst.set(getMBTA(input.route()))
        mbta_df, mbta_h, mbta_e = mbta_lst.get()
        route_map.layers = [layer for layer in route_map.layers if isinstance(layer, ipyl.TileLayer)]  # clear layers
        for i in range(len(mbta_df)):
            marker = ipyl.CircleMarker(
                location=(mbta_df["Lat"].iloc[i], mbta_df["Lon"].iloc[i]),
                radius=10,
                color="blue" if mbta_df["Direction"].iloc[i] == 1 else "green",
                opacity=0.5,
                draggable=False,
            )
            # marker.popup = ipyl.Popup(
            #     location=(mbta_df["Lat"].iloc[i], mbta_df["Lon"].iloc[i]),
            #     child=widgets.HTML(f"ID: {mbta_df['ID'].iloc[i]}<br/>Cars: {mbta_df['Carriage'].iloc[i]}<br/>"),
            #     close_button=False
            # )
            route_map.add(marker)
        reactive.invalidate_later(5)

    @reactive.Effect
    @reactive.event(input.route)
    def _():
        mbta_lst.set(getMBTA(input.route()))
        mbta_df, mbta_h, mbta_e = mbta_lst.get()
        latmean = mbta_df["Lat"].mean()
        lonmean = mbta_df["Lon"].mean()
        route_map.center = (latmean, lonmean)
        route_map.zoom = 12

    @output
    @render.text
    def nowtime():
        mbta_df, mbta_h, mbta_e = mbta_lst.get()
        return str(input.route()) + ": " + str(datetime.fromtimestamp(mbta_h["timestamp"]))

app = App(app_ui, server)

# run_app(app)