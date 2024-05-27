import pandas as pd
import geopandas as gpd
import pickle
import gzip

# Route GeoJSON files
bus_route = gpd.read_file("data/inputs/Bus_Routes.geojson")
transit_route = gpd.read_file("data/inputs/Transit_Routes.geojson")
route_shp = pd.concat([bus_route, transit_route])
# route_shp = route_shp[["OBJECTID", "route_id", "geometry"]]
route_shp_sim = route_shp.copy()
route_shp_sim['geometry'] = route_shp.simplify(0.0001)

route_shp_sim.to_file("data/outputs/routes.geojson", driver="GeoJSON")

# route_shp.to_pickle("data/outputs/routes.pkl")

# with open("data/outputs/routes.pkl", "wb") as f:
#     pickle.dump(route_shp, f)



