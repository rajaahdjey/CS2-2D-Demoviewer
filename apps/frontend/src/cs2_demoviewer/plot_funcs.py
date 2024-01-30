import pandas as pd
import numpy as np
import imageio.v3 as imageio
import pandas as pd


map_wise_params = {
    'de_mirage' : {
		"x": -3230,
		"y": 1713,
        "scale": 5
	}
}

def plot_transform(map_name,position):
    start_x = map_wise_params[map_name]["x"]
    start_y = map_wise_params[map_name]["y"]
    scale = map_wise_params[map_name]["scale"]
    x = position[0] - start_x
    x /= scale
    y = start_y - position[1]
    y /= scale
    #for now not worrying about z
    # z = position[2]
    # if "z_cutoff" in current_map_data and z < current_map_data["z_cutoff"]:
    #     y += 1024
    return (x, y)




