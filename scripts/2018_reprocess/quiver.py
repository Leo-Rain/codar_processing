import xarray as xr
import numpy.ma as ma
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from codar_processing.common import create_dir
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from oceans import uv2spdir, spdir2uv

file = '/Users/mikesmith/Documents/2018_codar_reprocess/nc/RU_MARA_2017_03_aggregated.nc'
save_dir = '/Users/mikesmith/Documents/2018_codar_reprocess/images/'
regions = dict(OuterBanks=[-76.5, -73, 34, 37], Massachusetts=[-70.5, -68, 40, 43], Rhode_Island=[-72, -70, 39, 41.5],
              New_Jersey=[-75, -72, 39, 41], EasternShores=[-76, -72, 37, 39])
velocity_min = 0
velocity_max = 60

LAND = cfeature.NaturalEarthFeature(
    'physical', 'land', '10m',
    edgecolor='face',
    facecolor='tan'
)

state_lines = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_1_states_provinces_lines',
    scale='50m',
    facecolor='none')

fig = plt.figure()

ds = xr.open_dataset(file)

for t in ds.time.data:
    temp = ds.sel(time=t, z=0)
    timestamp = pd.Timestamp(t).strftime('%Y%m%dT%H%M%SZ')

    for key, values in regions.items():
        extent = values
        tds = temp.sel(
            lon=(temp.lon > extent[0]) & (temp.lon < extent[1]),
            lat=(temp.lat < extent[3]) & (temp.lat > extent[2]),
        )

        u = tds['u'].data
        v = tds['v'].data

        lon = tds.coords['lon'].data
        lat = tds.coords['lat'].data
        time = tds.coords['time'].data

        u = ma.masked_invalid(u)
        v = ma.masked_invalid(v)

        angle, speed = uv2spdir(u, v)
        us, vs = spdir2uv(np.ones_like(speed), angle, deg=True)

        lons, lats = np.meshgrid(lon, lat)

        speed_clipped = np.clip(speed, velocity_min, velocity_max)

        fig, (ax) = plt.subplots(figsize=(11, 8),
                                 subplot_kw=dict(projection=ccrs.PlateCarree()))

        # plot pcolor on map
        h = ax.imshow(speed_clipped,
                      vmin=velocity_min,
                      vmax=velocity_max,
                      cmap='jet',
                      interpolation='bilinear',
                      extent=extent,
                      origin='lower')

        # plot arrows over pcolor
        ax.quiver(lons, lats,
                   us, vs,
                   cmap='jet',
                   scale=55)

        # generate colorbar
        plt.colorbar(h)

        # Plot title
        plt.title('{}\n{} - {}'.format(tds.title, ' '.join(key.split('_')), timestamp))

        # Gridlines and grid labels
        gl = ax.gridlines(draw_labels=True,
                           linewidth=1,
                           color='black',
                           alpha=0.5, linestyle='--')
        gl.xlabels_top = gl.ylabels_right = False
        gl.xlabel_style = {'size': 15, 'color': 'gray'}
        gl.ylabel_style = {'size': 15, 'color': 'gray'}
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER

        # Axes properties and features
        ax.set_extent(extent)
        ax.add_feature(LAND, zorder=0, edgecolor='black')
        ax.add_feature(cfeature.LAKES)
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(state_lines, edgecolor='black')

        create_dir(save_dir)

        fig_name = '{}/MARACOOS_{}_{}_totals.png'.format(save_dir, key, timestamp)
        plt.savefig(fig_name)
        plt.close('all')
        # plt.show()